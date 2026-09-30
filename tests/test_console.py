import struct
import wave
from types import SimpleNamespace

import numpy as np

from biem_radia.console_theme import channel_status, grid_shape
from biem_radia.inbox import InboxStore
from biem_radia.live_audio import LiveAudio, WavTap


def test_monitor_separates_streams_and_drops_stale_audio(monkeypatch):
    now = [10.0]
    monkeypatch.setattr("biem_radia.live_audio.time.monotonic", lambda: now[0])
    monitor = LiveAudio()
    monitor.selected = "A"
    samples = np.full(160, 0.25, dtype=np.float32)
    monitor.feed("A", "s1", samples, 8000, "slot 1")
    monitor.feed("A", "s2", samples * -1, 8000, "slot 2")
    monitor.feed("B", "s1", samples * -1, 8000, "other")
    assert monitor.pending.qsize() == 1
    assert monitor.state("A")["audio_stream_count"] == 2
    out = np.zeros((400, 1), dtype=np.float32)
    monitor._callback(out, 400, None, None)
    assert out[:320].mean() > 0 and not out[320:].any()
    now[0] = 11.0
    assert not monitor.state("A")["audio_present"]
    monitor.pending.put((9.0, monitor.generation, samples))
    monitor._callback(out, 400, None, None)
    assert not out.any()
    assert np.all(samples == 0.25)


def test_monitor_failure_and_mute_do_not_break_receiver(monkeypatch):
    monitor = LiveAudio()
    monitor.selected = "A"
    monkeypatch.setattr(
        "biem_radia.live_audio.resample_poly",
        lambda *a: (_ for _ in ()).throw(ValueError("test DSP failure")),
    )
    monitor.feed("A", "1", np.ones(160), 8000, "test")
    assert "test DSP failure" in monitor.error
    closed = []
    monitor.output = SimpleNamespace(
        stop=lambda: (_ for _ in ()).throw(OSError("lost output")),
        close=lambda: closed.append(True),
    )
    monitor.stop()
    assert closed and monitor.output is None and monitor.selected is None


def test_wav_tap_growing_header_two_streams_and_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr("biem_radia.live_audio.time.monotonic", lambda: 100.0)
    for name, value in [("TEMP_1", 1000), ("TEMP_2", -1000)]:
        with wave.open(str(tmp_path / name), "wb") as wav:
            wav.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
            wav.writeframes(np.full(160, value, dtype="<i2").tobytes())
        raw = bytearray((tmp_path / name).read_bytes())
        struct.pack_into("<I", raw, 40, 0)  # the live backend hasn't updated data length yet
        (tmp_path / name).write_bytes(raw)
    tap = WavTap(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = tap.poll()
    assert len(result) == 2 and {r[0] for r in result} == set(before)
    assert all(len(r[1]) == 160 and r[2] == 8000 for r in result)
    tap.last_poll = 0
    assert tap.poll() == []
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with (tmp_path / "TEMP_1").open("ab") as out:
        out.write(np.full(80, 500, dtype="<i2").tobytes())
    tap.last_poll = 0
    assert len(tap.poll()[0][1]) == 80


def test_channel_states_and_adaptive_grid():
    args = dict(connected=True, running=True, enabled=True, threshold=-45)
    assert channel_status(**args, state={"level": -80})[2] == "green"
    assert channel_status(**args, state={"level": -20})[2] == "red"
    assert channel_status(**args, state={"level": -20, "audio_present": True})[2] == "green"
    args["connected"] = False
    assert channel_status(**args, state={"level": -20, "audio_present": True})[0] == "disconnected"
    assert grid_shape(1, 680) == (1, 1)
    assert grid_shape(4, 680) == (2, 2)
    assert grid_shape(6, 680) == (3, 2)


def test_unread_persists_and_raw_does_not_count(tmp_path):
    store = InboxStore(tmp_path)
    store.add({"channel": "A", "text": "Hello", "source_id": 3737}, "test", "a")
    store.add({"channel": "A", "text": "Raw", "kind": "Ham veri / DMR"}, "test", "b")
    assert store.unread_counts() == {"A": 1}
    row = next(row for row in store.search() if row["text"] == "Hello")
    store.mark_read(row["id"])
    assert InboxStore(tmp_path).unread_counts() == {}
