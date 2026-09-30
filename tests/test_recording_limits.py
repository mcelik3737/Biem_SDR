import base64
import json
from datetime import datetime, timezone

import numpy as np

from biem_radia.models import AUDIO_RATE, Channel
from biem_radia.recorder import CallRecorder
from biem_radia.scanner import TetraScanGate
from biem_radia.storage import Archive
from biem_radia.tetra import TetraBackend


def test_analog_exact_limit_and_pause_inside_large_block(tmp_path):
    archive = Archive(tmp_path)
    epoch = datetime(2026, 9, 12, tzinfo=timezone.utc)
    recorder = CallRecorder(archive, Channel("A", 446006250), "USB", epoch)
    recorder.feed(np.full(AUDIO_RATE * 185, 0.1), -30)
    recorder.finish("stopped")
    rows = sorted(archive.search(), key=lambda r: r["started_utc"])
    assert [r["duration"] for r in rows] == [90, 90, 1]
    assert [(datetime.fromisoformat(r["started_utc"]) - epoch).total_seconds() for r in rows] == [
        0,
        92,
        184,
    ]


def test_tetra_scan_timeout_control_and_voice():
    gate = TetraScanGate(-48)
    for _ in range(19):
        assert not gate.advance_tetra(-20, 1, False, False)
    assert gate.advance_tetra(-20, 1, False, False)
    gate = TetraScanGate(-48)
    for _ in range(240):
        assert not gate.advance_tetra(-20, 1, True, True)
    assert not gate.advance_tetra(-20, 1, False, True)
    assert gate.advance_tetra(-20, 1, False, True)
    assert TetraScanGate(-48).advance_tetra(-90, 1, False, False)


def test_tetra_limit_pause_and_control_evidence(tmp_path, monkeypatch):
    backend = TetraBackend.__new__(TetraBackend)
    backend.archive = Archive(tmp_path)
    backend.channel = Channel("T", 427500000, 25000, 25000, mode="TETRA")
    backend.directory = tmp_path / "session"
    backend.directory.mkdir()
    backend.calls, backend.clear, backend.cooldowns = {}, {}, {}
    backend.cc = backend.control_signature = None
    backend.control_confirmations = backend.completed = 0
    backend.last_voice = float("-inf")
    clock = [1.0]
    monkeypatch.setattr("biem_radia.tetra.time.monotonic", lambda: clock[0])
    pcm = base64.b64encode(b"\x01\x00" * 480).decode()
    event = {
        "slot": 1,
        "pcm": pcm,
        "errors": False,
        "sync": {"ColorCode": 11},
        "data": [{"CurrTimeSlot": 1, "Encryption_mode": 0}],
    }
    for _ in range(1500):
        backend._event(event)
        clock[0] += 0.06
    assert not backend.calls and backend.archive.search()[0]["duration"] == 90
    backend._event(event)
    assert not backend.calls
    clock[0] += 2
    backend._event(event)
    assert backend.calls
    backend._finish(1)
    control = {
        "slot": 0,
        "errors": False,
        "sync": {"ColorCode": 11},
        "data": [
            {
                "MAC_PDU_Type": 2,
                "MAC_Broadcast_Type": 0,
                "Main_Carrier": 1100,
                "Frequency_Band": 4,
                "Offset": 0,
            }
        ],
    }
    backend._event({"slot": 0, "sync": {"ColorCode": 11}})
    assert backend.control_confirmations == 0
    for _ in range(3):
        backend._event(control)
    assert backend.control_confirmations == 3
    control["errors"] = True
    backend._event(control)
    assert backend.control_confirmations == 3
    assert json.loads((backend.directory / "events.jsonl").read_text().splitlines()[-1])["errors"]
