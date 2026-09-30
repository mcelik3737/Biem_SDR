from datetime import datetime, timezone

import numpy as np
import pytest

from biem_radia.dmr import parse_event
from biem_radia.filenames import available_path, recording_name
from biem_radia.fmradio import WFM
from biem_radia.tones import ToneGate


def test_filenames_include_real_duration_and_do_not_overwrite(tmp_path):
    started = datetime(2026, 9, 12, 12, 35, 6, tzinfo=timezone.utc)
    stamp = started.astimezone().strftime("%Y-%m-%d_%H_%M_%S")
    assert recording_name("NFM", started, 3.24) == f"analog_{stamp}_3.24sn.wav"
    assert recording_name("DMR", started, 3.24, 3737, 3411) == f"3737_3411_{stamp}_3.24sn.wav"
    name = recording_name("DMR", started, 3.24, None, None)
    assert "bilinmiyor_bilinmiyor" in name
    first = available_path(tmp_path, name)
    first.write_bytes(b"keep")
    second = available_path(tmp_path, name)
    assert second != first and first.read_bytes() == b"keep"


@pytest.mark.parametrize("tone,expected", [(88.5, True), (91.5, False), (1000, False)])
def test_ctcss_rejects_other_tones_and_voice(tone, expected):
    gate = ToneGate("CTCSS", "88.5")
    t = np.arange(48000) / 48000
    audio = 300 * np.sin(2 * np.pi * tone * t) + 500 * np.sin(2 * np.pi * 1100 * t)
    for chunk in np.array_split(audio, 31):
        gate.feed(chunk)
    assert bool(gate.open) == expected


@pytest.mark.parametrize("invert", [False, True])
def test_dcs_polarity_is_not_guessed(invert):
    # D023, code LSB + fixed signature + Golay parity.
    bits = np.array([int(b) for b in "11001000000111000110111"])
    t = np.arange(48000) / 48000
    hz = (bits[(t * 134.4).astype(int) % 23] * 2 - 1) * 300
    if invert:
        hz = -hz
    normal = ToneGate("DCS", "023")
    inverse = ToneGate("DCS-I", "023")
    for chunk in np.array_split(hz, 31):
        normal.feed(chunk)
        inverse.feed(chunk)
    assert bool(normal.open) == (not invert)
    assert bool(inverse.open) == invert


def test_wfm_outputs_48k_and_demodulates_voice_without_hardware():
    rate = 960000
    t = np.arange(rate // 5) / rate
    iq = np.exp(-1j * 30 * np.cos(2 * np.pi * 1000 * t))
    demod = WFM()
    out = np.concatenate([demod.process(chunk) for chunk in np.array_split(iq, 37)])
    assert len(out) == 9600 and np.max(abs(out)) <= 1
    spectrum = abs(np.fft.rfft(out[2400:]))
    peak = np.argmax(spectrum) * 48000 / len(out[2400:])
    assert abs(peak - 1000) < 10


def test_digital_protocol_access_codes_are_distinct():
    p25 = parse_event("2026-09-12 12:00:10 P25p1 TGT: 201; SRC: 101; NAC: 293; Group;")
    nxdn = parse_event("2026-09-12 12:00:10 NXDN TGT: 201; SRC: 101; RAN: 12; Group;")
    assert p25 is not None and p25.protocol == "P25" and p25.color_code == 0x293
    assert nxdn is not None and nxdn.protocol == "NXDN" and nxdn.color_code == 12
    assert parse_event("2026-09-12 12:00:10 DMR TGT: 201; SRC: 101; NAC: 293; Group;") is None


def test_recording_rename_preserves_audio_and_archive_and_is_repeatable(tmp_path):
    import wave

    from biem_radia.rename_recordings import migrate
    from biem_radia.storage import Archive

    archive = Archive(tmp_path)
    directory = tmp_path / "recordings"
    directory.mkdir()
    old = directory / "old.wav"
    with wave.open(str(old), "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        wav.writeframes(b"\x01\x00" * 16000)
    original = old.read_bytes()
    with archive.connect() as db:
        db.execute(
            "INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason) VALUES('x','A',446006250,'2026-09-12T12:00:00+00:00',1,'recordings/old.wav','USB','squelch')"
        )
    plan = migrate(archive)
    assert len(plan) == 1 and old.exists()
    migrate(archive, True)
    assert not old.exists() and archive.audio_path("x").read_bytes() == original
    assert not migrate(archive, True)
    assert list((tmp_path / "backups").glob("*/rename-manifest.json"))


def test_tetra_audio_requires_matching_clear_slot_and_keeps_unknown_ids(tmp_path):
    import base64

    from biem_radia.models import Channel
    from biem_radia.storage import Archive
    from biem_radia.tetra import TetraBackend

    backend = TetraBackend.__new__(TetraBackend)
    backend.archive = Archive(tmp_path)
    backend.channel = Channel("T", 440000000, 25000, 25000, mode="TETRA")
    backend.directory = tmp_path / "session"
    backend.directory.mkdir()
    backend.calls = {}
    backend.clear = {}
    backend.cc = None
    backend.cooldowns = {}
    backend.last_voice = float("-inf")
    backend.control_signature = None
    backend.control_confirmations = 0
    backend.completed = 0
    pcm = base64.b64encode((np.sin(np.arange(480)) * 10000).astype("<i2").tobytes()).decode()
    backend._event({"slot": 2, "pcm": pcm, "data": [], "errors": False})
    assert not backend.calls
    backend._event(
        {
            "slot": 4,
            "pcm": pcm,
            "data": [{"CurrTimeSlot": 4, "Encryption_mode": 1}],
            "errors": False,
        }
    )
    assert not backend.calls
    backend._event(
        {
            "slot": 3,
            "pcm": pcm,
            "sync": {"ColorCode": 11},
            "data": [{"CurrTimeSlot": 3, "Encryption_mode": 0}],
            "errors": False,
        }
    )
    backend._finish(3)
    row = backend.archive.search(slot=3)[0]
    assert row["protocol_slot"] == 3 and row["radio_id"] is None and row["group_id"] is None
    assert row["color_code"] == 11 and row["duration"] == 0.06
