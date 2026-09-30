from dataclasses import asdict
from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import signal

from biem_radia.auto_decode import AutoChannel
from biem_radia.detection import AnalogEvidence, ProtocolEvidence, fm_voice_candidate
from biem_radia.models import SAMPLE_RATE, Channel, center_for
from biem_radia.scanner import AutoScanGate
from biem_radia.storage import Archive


def test_repeated_protocol_evidence_errors_expiry_and_xpt():
    now = [10.0]
    detector = ProtocolEvidence(lambda: now[0])
    sync = "12:00:00 Sync: +DMR [slot1] slot2 | Color Code=11 | CSBK"
    detector.observe_dmr(sync)
    assert detector.digital_mode() is None
    detector.observe_dmr(sync)
    detector.observe_dmr(sync.replace("11", "12"))
    assert detector.digital_mode() is None  # different CC is a new candidate
    for _ in range(3):
        detector.observe_dmr(sync)
        detector.observe_dmr(" AMBE F861D43FA47280 err = [0] [0]")
    assert detector.digital_mode() == "DMR"
    detector.observe_dmr("XPT supported; Hytera radio")
    assert detector.label("DMR") == "DMR"
    for _ in range(2):
        detector.observe_dmr(" Hytera XPT Site Status - Free LCN: 3 SN: 0")
    assert detector.label("DMR") == "DMR / Hytera XPT"
    for _ in range(3):
        detector.observe_dmr(sync.replace("11", "12"))
    assert detector.label("DMR") == "DMR"
    detector.observe_dmr(sync + " | CACH/Burst FEC ERR")
    assert detector.digital_mode() is None
    for _ in range(3):
        detector.observe_dmr(sync)
    assert detector.label("DMR") == "DMR"
    now[0] += 2
    assert detector.digital_mode() is None
    assert "DMR" in detector.confirmed  # committed WAV may arrive after carrier ends


def test_tetra_requires_valid_data_and_does_not_guess_when_probes_conflict():
    detector = ProtocolEvidence()
    event = {"errors": False, "sync": {"ColorCode": 18}, "data": [{"Main_Carrier": 1094}]}
    for _ in range(5):
        detector.observe_tetra({**event, "errors": True})
        detector.observe_tetra({**event, "data": []})
    assert detector.digital_mode() is None
    for _ in range(3):
        detector.observe_tetra(event)
    assert detector.digital_mode() == "TETRA"
    for _ in range(3):
        detector.observe_dmr("Sync: +DMR | Color Code=01 | IDLE")
    assert detector.digital_mode() == "CONFLICT"


def test_fm_positive_evidence_rejects_noise_carrier_and_four_level_fsk():
    t = np.arange(24000) / 48000
    voice = 1100 * np.sin(2 * np.pi * 700 * t) + 400 * np.sin(2 * np.pi * 1900 * t)
    assert fm_voice_candidate(voice)
    rng = np.random.default_rng(47)
    for bad in (
        np.zeros(24000),
        rng.normal(0, 1800, 24000),
        np.repeat(rng.choice([-1944, -648, 648, 1944], 2400), 10),
        np.full(24000, np.nan),
    ):
        assert not fm_voice_candidate(bad)
    fsk = np.repeat(rng.choice([-1944, -648, 648, 1944], 4800), 10)
    shaped = signal.sosfilt(signal.butter(4, 2400, fs=48000, output="sos"), fsk)
    assert not fm_voice_candidate(shaped[-24000:])
    evidence = AnalogEvidence()
    assert not evidence.feed(voice[:9600], True)
    for _ in range(12):
        accepted = evidence.feed(voice[:9600], True)
    assert accepted
    assert not evidence.feed(voice, False)


def test_auto_configuration_and_scan_never_hold_on_unknown_carrier():
    channel = Channel("Auto", 427500000, mode="AUTO")
    assert Channel(**asdict(channel)) == channel
    assert center_for([channel]) == 427600000
    with pytest.raises(ValueError, match="CC"):
        Channel("Auto", 427500000, mode="AUTO", color_code=11)
    gate = AutoScanGate(-45, dwell=1)
    unknown = {"level": -20, "detected_mode": None}
    assert not gate.advance_auto(unknown, 2.5)
    assert gate.advance_auto(unknown, 0.5)
    gate = AutoScanGate(-45)
    assert not gate.advance_auto({"level": -20, "detected_mode": "DMR"}, 1)
    assert gate.held
    assert gate.advance_auto(unknown, 1)
    tetra = {"level": -20, "detected_mode": "TETRA", "voice": False, "control_channel": False}
    gate = AutoScanGate(-45)
    assert not gate.advance_auto(tetra, 19)
    assert gate.advance_auto(tetra, 1)


class FakeDmr:
    closed = False

    def __init__(self, archive, channel, project):
        self.channel = channel
        self.directory = archive.root / "probe"
        self.directory.mkdir()
        self.importer = SimpleNamespace(recording_check=None, last_metadata="CC 11 • ID 3737")
        self.journal = SimpleNamespace(observer=None)
        self.completed = 0
        self.inject_sync = False

    def feed(self, pcm):
        if self.inject_sync:
            for _ in range(3):
                self.journal.observer("Sync: +DMR MS/DM MODE/MONO | Color Code=11 | VC1")

    def close(self):
        FakeDmr.closed = True


class FakeTetra:
    def __init__(self, archive, channel, center, project=None):
        self.channel = channel
        self.observer = None
        self.recording_check = None
        self.completed = 0

    def feed(self, iq):
        return {"level": -90, "active": False, "data": "", "voice": False, "control_channel": False}

    def close(self):
        pass


def synthetic_voice(block, seconds=0.1):
    t = (
        np.arange(round(SAMPLE_RATE * seconds)) + block * round(SAMPLE_RATE * seconds)
    ) / SAMPLE_RATE
    return 0.2 * np.exp(-2j * np.pi * 100000 * t - 1j * 2 * np.cos(2 * np.pi * 700 * t))


def test_auto_iq_to_analog_archive_then_digital_suppresses_analog(tmp_path, monkeypatch):
    monkeypatch.setattr("biem_radia.auto_decode.DmrBackend", FakeDmr)
    monkeypatch.setattr("biem_radia.auto_decode.TetraBackend", FakeTetra)
    archive = Archive(tmp_path / "archive")
    channel = Channel("Automatic", 427500000, mode="AUTO")
    receiver = AutoChannel(
        archive, channel, center_for([channel]), "USB", datetime.now(timezone.utc)
    )
    assert not receiver.dmr.importer.recording_check()
    for i in range(40):
        state = receiver.feed(synthetic_voice(i))
    assert state["detected_mode"] == "NFM" and state["active"]
    receiver.dmr.inject_sync = True
    state = receiver.feed(synthetic_voice(40))
    assert state["detected_mode"] == "DMR" and not receiver.recorder.active
    assert receiver.dmr.importer.recording_check()
    assert receiver.channel.frequency_hz == 427500000
    receiver.close()
    calls = archive.search()
    assert len(calls) == 1 and calls[0]["duration"] > 3
    assert calls[0]["radio_id"] is None and calls[0]["slot"] is None
    assert calls[0]["source"] == "USB/AUTO-NFM"
    assert calls[0]["end_reason"] == "digital_detected"


def test_missing_tetra_dependency_cleans_dmr_and_does_not_fall_back(tmp_path, monkeypatch):
    monkeypatch.setattr("biem_radia.auto_decode.DmrBackend", FakeDmr)

    def missing(*args, **kwargs):
        raise RuntimeError("TETRA missing")

    monkeypatch.setattr("biem_radia.auto_decode.TetraBackend", missing)
    FakeDmr.closed = False
    with pytest.raises(RuntimeError, match="TETRA missing"):
        AutoChannel(
            Archive(tmp_path),
            Channel("A", 427500000, mode="AUTO"),
            427600000,
            "USB",
            datetime.now(timezone.utc),
        )
    assert FakeDmr.closed


def test_auto_card_discovers_code_preserves_frequency_and_roundtrips():
    import tkinter as tk

    from biem_radia.cards import ChannelCard

    root = tk.Tk()
    root.withdraw()
    try:
        card = ChannelCard(root, 0)
        card.load(Channel("Test", 428500000, mode="DMR", color_code=11))
        card.mode.set("Otomatik")
        card.update_options()
        assert str(card.code_entry.cget("state")) == "disabled"
        assert str(card.tone_box.cget("state")) == "disabled"
        auto = card.value()
        assert auto.mode == "AUTO" and auto.color_code is None
        assert auto.frequency_hz == 428500000
        card.load(Channel(**asdict(auto)))
        assert card.mode.get() == "Otomatik" and card.freq.get() == "428.50000"
        card.telemetry({"level": -30, "active": False, "data": "OTOMATİK • DMR / Hytera XPT"})
        assert "XPT" in card.details.get()
    finally:
        root.destroy()


def test_probe_recording_gate_keeps_wav_pending_until_confirmed(tmp_path):
    from test_dmr import fixture_call

    from biem_radia.dmr import DmrImporter

    archive = Archive(tmp_path / "archive")
    directory = tmp_path / "session"
    fixture_call(directory)
    detector = ProtocolEvidence()
    importer = DmrImporter(archive, Channel("AUTO", 427500000, mode="DMR"), directory)
    importer.recording_check = lambda: "DMR" in detector.confirmed
    assert importer.scan() == 0 and not archive.search()
    assert len(list(directory.glob("*.wav"))) == 1
    for _ in range(3):
        detector.observe_dmr("Sync: +DMR | Color Code=11 | VLC")
    detector.observe_dmr("Sync: no sync")
    assert importer.scan() == 1  # end-of-call WAV still imports after sync ends
    row = archive.search()[0]
    assert row["radio_id"] == "101" and row["slot"] == 1


def test_engine_starts_auto_probes_before_usb_and_closes_on_error(tmp_path, monkeypatch):
    from pathlib import Path

    from biem_radia.engine import Receiver

    actions = []

    class AutoProbe:
        recorder = None

        def __init__(self, *args):
            actions.append("probe")
            self.channel = args[1]
            self.recorder = SimpleNamespace(channel=self.channel)
            self.dmr = SimpleNamespace(importer=SimpleNamespace(channel=self.channel))
            self.tetra = SimpleNamespace(channel=self.channel)

        def feed(self, iq):
            actions.append("feed")
            return {"name": "Auto", "level": -40, "active": False, "completed": 0, "data": "test"}

        def close(self, reason):
            actions.append("closed " + reason)

    class Source:
        def __init__(self, *args, **kwargs):
            actions.append("usb")
            self.reads = 0

        def read(self):
            self.reads += 1
            if self.reads > 7:
                raise RuntimeError("test unplugged")
            return np.zeros(48000, dtype=complex)

        def close(self):
            actions.append("usb closed")

    monkeypatch.setattr("biem_radia.engine.AutoChannel", AutoProbe)
    monkeypatch.setattr("biem_radia.engine.USBSource", Source)
    receiver = Receiver(Archive(tmp_path))
    receiver.start([Channel("Auto", 427500000, mode="AUTO")], Path("unused"))
    receiver.thread.join(10)
    assert not receiver.running
    assert actions[:2] == ["probe", "usb"]
    assert actions.count("feed") == 2
    assert actions[-2:] == ["closed error", "usb closed"]


def test_tetra_auto_confirmation_records_only_clear_slot(tmp_path):
    import base64

    from biem_radia.tetra import TetraBackend

    backend = TetraBackend.__new__(TetraBackend)
    backend.archive = Archive(tmp_path / "archive")
    backend.channel = Channel("AUTO TETRA", 427500000, 25000, 25000, mode="TETRA")
    backend.directory = tmp_path / "session"
    backend.directory.mkdir()
    backend.calls, backend.clear, backend.cooldowns = {}, {}, {}
    backend.cc = None
    backend.last_voice = float("-inf")
    backend.control_signature = None
    backend.control_confirmations = backend.completed = 0
    evidence = ProtocolEvidence()
    backend.observer = evidence.observe_tetra
    backend.recording_check = lambda: evidence.digital_mode() == "TETRA"
    pcm = base64.b64encode((np.sin(np.arange(480)) * 10000).astype("<i2").tobytes()).decode()
    event = {
        "slot": 2,
        "pcm": pcm,
        "errors": False,
        "sync": {"ColorCode": 18},
        "data": [{"CurrTimeSlot": 2, "Encryption_mode": 0}],
    }
    backend._event(event)
    backend._event(event)
    assert not backend.calls
    backend._event(event)
    assert 2 in backend.calls
    backend._event({**event, "slot": 3, "data": [{"CurrTimeSlot": 3, "Encryption_mode": 1}]})
    assert 3 not in backend.calls
    backend._finish(2)
    row = backend.archive.search()[0]
    assert row["protocol_slot"] == 2 and row["color_code"] == 18
    assert row["radio_id"] is None and row["group_id"] is None
