import json
import tkinter as tk
import wave

import pytest

from biem_radia.app import RadiaApp
from biem_radia.digital_log import DigitalJournal, Tail
from biem_radia.models import Channel
from biem_radia.protection import MAGIC, read_audio
from biem_radia.storage import Archive


def test_protected_archive_roundtrip_and_tamper(tmp_path):
    archive = Archive(tmp_path, protected=True)
    path = tmp_path / "call.wav"
    with wave.open(str(path), "wb") as writer:
        writer.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        writer.writeframes(b"\x01\x00" * 8000)
    original = path.read_bytes()
    with archive.connect() as db:
        db.execute(
            "INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason) VALUES('one','test',427500000,'2026-09-12',1,'call.wav','TEST','stop')"
        )
    encrypted = archive.protect_file(path)
    assert not path.exists()
    assert encrypted.read_bytes().startswith(MAGIC)
    assert archive.audio_path("one") == encrypted
    assert read_audio(encrypted) == original
    damaged = bytearray(encrypted.read_bytes())
    damaged[-10] ^= 1
    encrypted.write_bytes(damaged)
    with pytest.raises(OSError):
        read_audio(encrypted)


def test_failed_encryption_preserves_original(tmp_path, monkeypatch):
    archive = Archive(tmp_path, protected=True)
    path = tmp_path / "call.wav"
    path.write_bytes(b"evidence")

    def fail(*args, **kwargs):
        raise OSError("disk/key failure")

    monkeypatch.setattr("biem_radia.protection.transform", fail)
    with pytest.raises(OSError):
        archive.protect_file(path)
    assert path.read_bytes() == b"evidence"


def test_incremental_digital_metadata_and_gps_log(tmp_path):
    journal = DigitalJournal(tmp_path, Channel("GPS test", 427500000, mode="DMR"))
    path = tmp_path / "decoder.log"
    path.write_text(
        "12:34:56 Sync: DMR MS/DM MODE/MONO Color Code=11\nSLOT 1 TGT=8 SRC=3737\nLRRP Latitude: 41.0 Longitude: 29.0\npartial",
        "utf-8",
    )
    journal.poll()
    assert "ID 3737" in journal.latest and "CC 11" in journal.latest
    assert "Çözücü slotu 1" in journal.latest and "Grup" not in journal.latest
    lines = [
        json.loads(line) for line in (tmp_path / "digital.jsonl").read_text("utf-8").splitlines()
    ]
    assert len(lines) == 3
    assert lines[-1]["category"] == "konum/veri çıktısı"
    assert lines[-1]["frequency_hz"] == 427500000 and lines[-1]["observed_utc"]
    journal.poll()
    assert len((tmp_path / "digital.jsonl").read_text("utf-8").splitlines()) == 3
    with path.open("a", encoding="utf-8") as stream:
        stream.write(" line\n")
    assert journal.tail.read() == ["partial line"]
    journal.observe("12:34:57 Sync: invalid")
    journal.observe("SLOT 1 TGT=9 SRC=99")
    assert "3737" not in journal.latest and "99" not in journal.latest


def test_tail_truncation(tmp_path):
    path = tmp_path / "log"
    path.write_text("abcdef\n")
    tail = Tail(path)
    assert tail.read() == ["abcdef"]
    path.write_text("new\n")
    assert tail.read() == ["new"]


def test_admin_gate_and_mode_controls(tmp_path, monkeypatch):
    root = tk.Tk()
    root.withdraw()
    app = RadiaApp(root, tmp_path)
    errors = []
    monkeypatch.setattr("biem_radia.app.is_admin", lambda: False)
    monkeypatch.setattr(
        "biem_radia.app.messagebox.showerror", lambda title, text: errors.append(text)
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Unauthorized audio access")

    monkeypatch.setattr(app.archive, "audio_path", forbidden)
    try:
        app.play()
        assert errors and "yönetici" in errors[0]
        card = app.cards[0]
        card.mode.set("Analog")
        card.tone_mode.set("CTCSS")
        card.update_options()
        assert str(card.code_entry.cget("state")) == "disabled"
        assert str(card.value_box.cget("state")) == "readonly"
        card.mode.set("DMR")
        card.code.set("")
        card.update_options()
        assert str(card.code_entry.cget("state")) == "normal"
        assert str(card.tone_box.cget("state")) == "disabled"
        assert card.value().color_code is None
    finally:
        for token in root.tk.splitlist(root.tk.call("after", "info")):
            root.after_cancel(token)
        root.destroy()
