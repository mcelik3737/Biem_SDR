from __future__ import annotations

import tkinter as tk
from pathlib import Path

import numpy as np

from biem_radia.app import RadiaApp
from biem_radia.engine import Receiver
from biem_radia.models import SAMPLE_RATE, Channel
from biem_radia.sources import USBSource
from biem_radia.storage import Archive


def test_iq_to_archive_and_error_finalization(tmp_path, monkeypatch):
    class TestSource:
        closed = False

        def __init__(self, *args, **kwargs):
            self.index = 0

        def read(self):
            if self.index >= 25:
                raise RuntimeError("test disconnected")
            t = (np.arange(48000) + self.index * 48000) / SAMPLE_RATE
            self.index += 1
            return 0.2 * np.exp(-2j * np.pi * 100000 * t - 1j * 2.5 * np.cos(2 * np.pi * 1000 * t))

        def close(self):
            TestSource.closed = True

    monkeypatch.setattr("biem_radia.engine.USBSource", TestSource)
    archive = Archive(tmp_path)
    receiver = Receiver(archive)
    receiver.start([Channel("Live path", 446006250)], Path("unused"))
    assert receiver.thread is not None
    receiver.thread.join(10)
    assert not receiver.running and TestSource.closed
    calls = archive.search()
    assert len(calls) == 1 and calls[0]["end_reason"] == "error"
    assert calls[0]["duration"] > 0.8
    assert archive.audio_path(calls[0]["id"]).is_file()


def test_usb_queue_overflow_is_reported_instead_of_silent_loss():
    # Exercise the callback boundary without opening real hardware.
    import ctypes
    import queue

    source = USBSource.__new__(USBSource)
    source.queue = queue.Queue(maxsize=1)
    source.error = None
    raw = (ctypes.c_ubyte * 2)(128, 128)
    source._callback(raw, 2, None)
    source._callback(raw, 2, None)
    assert source.error is not None and "kuyruğu doldu" in source.error


def test_desktop_settings_search_and_playback_path(tmp_path, monkeypatch):
    import wave

    root = tk.Tk()
    root.withdraw()
    app = RadiaApp(root, tmp_path)
    played = []
    monkeypatch.setattr(
        "biem_radia.app.winsound.PlaySound", lambda path, flags: played.append(path)
    )
    try:
        app.name.set("Güvenlik")
        app.freq.set("446,01875")
        app.save_channel()
        assert len(app.channels) == 2
        assert app.config_path.is_file()
        sound_path = app.archive.root / "test.wav"
        with wave.open(str(sound_path), "wb") as wav:
            wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            wav.writeframes(b"\x00\x00" * 1600)
        with app.archive.connect() as db:
            db.execute(
                "INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason) VALUES('test','Güvenlik',446018750,'2026-09-12T10:00:00+00:00',0.1,'test.wav','TEST','stopped')"
            )
        app.search_text.set("Güvenlik")
        app.refresh_archive()
        assert app.calls.get_children() == ("test",)
        app.calls.selection_set("test")
        app.play()
        assert played == [str(sound_path)]
        app.search_text.set("olmayan kanal")
        app.refresh_archive()
        assert not app.calls.get_children()
    finally:
        for after_id in root.tk.splitlist(root.tk.call("after", "info")):
            root.after_cancel(after_id)
        root.destroy()
