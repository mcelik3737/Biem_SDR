from __future__ import annotations

import socket
import struct
import threading
import wave
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from biem_radia.dsp import FMDemodulator
from biem_radia.models import AUDIO_RATE, SAMPLE_RATE, Channel, center_for
from biem_radia.recorder import CallRecorder
from biem_radia.sources import TCPSource, decode_iq
from biem_radia.storage import Archive

EPOCH = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)


def modulated(length, offset, tone=1000, amplitude=0.15):
    t = np.arange(length) / SAMPLE_RATE
    return amplitude * np.exp(
        2j * np.pi * offset * t - 1j * 2500 / tone * np.cos(2 * np.pi * tone * t)
    )


def test_fm_recovers_tone_across_irregular_blocks():
    channel = Channel("PMR", 446006250)
    center = center_for([channel])
    iq = modulated(SAMPLE_RATE // 2, channel.frequency_hz - center)
    demod = FMDemodulator(channel, center)
    chunks = [demod.process(iq[i : i + 16381])[0] for i in range(0, len(iq), 16381)]
    audio = np.concatenate(chunks)
    assert len(audio) == AUDIO_RATE // 2
    samples = audio[1600:]
    frequencies = np.fft.rfftfreq(len(samples), 1 / AUDIO_RATE)
    peak = frequencies[np.argmax(abs(np.fft.rfft(samples)))]
    assert abs(peak - 1000) < 5
    assert np.sqrt(np.mean(samples**2)) > 0.2
    whole, _ = FMDemodulator(channel, center).process(iq)
    np.testing.assert_allclose(audio, whole, atol=1e-6)


def test_two_simultaneous_channels_are_demodulated_separately():
    channels = [Channel("A", 446006250), Channel("B", 446056250)]
    center = center_for(channels)
    iq = modulated(SAMPLE_RATE // 2, channels[0].frequency_hz - center, 700)
    iq += modulated(len(iq), channels[1].frequency_hz - center, 1600)
    for c, expected in zip(channels, [700, 1600], strict=True):
        audio, _ = FMDemodulator(c, center).process(iq)
        audio = audio[1600:]
        peak = np.fft.rfftfreq(len(audio), 1 / AUDIO_RATE)[np.argmax(abs(np.fft.rfft(audio)))]
        assert abs(peak - expected) < 5


def test_off_channel_carrier_does_not_open_squelch():
    c = Channel("A", 446006250)
    center = center_for([c])
    d = FMDemodulator(c, center)
    iq = modulated(SAMPLE_RATE // 3, c.frequency_hz - center + 100000)
    d.process(iq)
    _, level = d.process(iq)
    assert level < -65


def test_two_calls_are_searchable_and_playable_wavs(tmp_path):
    archive = Archive(tmp_path)
    recorder = CallRecorder(archive, Channel("Güvenlik PMR", 446006250), "USB", EPOCH)
    quiet = np.zeros(1600, dtype=np.float32)
    voice = (0.5 * np.sin(2 * np.pi * 700 * np.arange(1600) / AUDIO_RATE)).astype(np.float32)
    for _ in range(6):
        recorder.feed(quiet, -90)
    for _ in range(2):
        for _ in range(10):
            recorder.feed(voice, -30)
        for _ in range(10):
            recorder.feed(quiet, -90)
    recorder.finish("stopped")
    calls = archive.search("Güvenlik", EPOCH.astimezone().date().isoformat())
    assert len(calls) == 2
    assert len(archive.search("GÜVENLİK")) == 2
    assert len(archive.search("güvenlik")) == 2
    assert not archive.search("Yok")
    assert not archive.search(day=(EPOCH + timedelta(days=1)).date().isoformat())
    for call in calls:
        assert call["radio_id"] is None and call["slot"] is None
        assert call["duration"] == pytest.approx(1.9)
        with wave.open(str(archive.audio_path(call["id"])), "rb") as wav:
            assert wav.getframerate() == AUDIO_RATE
            assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
            data = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
            assert np.max(abs(data)) > 10000
    assert not list(tmp_path.rglob("*.part"))


def test_stop_finalizes_active_call_and_noise_only_does_not_record(tmp_path):
    archive = Archive(tmp_path)
    recorder = CallRecorder(archive, Channel("A", 446006250), "USB", EPOCH)
    for _ in range(5):
        recorder.feed(np.zeros(1600), -90)
    assert archive.search() == []
    recorder.feed(np.ones(1600) * 0.2, -30)
    recorder.finish("error")
    assert archive.search()[0]["end_reason"] == "error"
    assert archive.audio_path(archive.search()[0]["id"]).is_file()


def test_max_duration_splits_continuous_carrier(tmp_path):
    archive = Archive(tmp_path)
    recorder = CallRecorder(archive, Channel("A", 446006250), "USB", EPOCH, max_seconds=0.5)
    for _ in range(12):
        recorder.feed(np.ones(1600) * 0.1, -30)
    recorder.finish("stopped")
    calls = archive.search()
    assert len(calls) == 3
    assert sum(c["duration"] for c in calls) == pytest.approx(1.2)


def test_rtl_tcp_fragmented_header_commands_and_disconnect():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    commands = bytearray()
    errors = []

    def serve():
        try:
            client, _ = server.accept()
            with client:
                client.settimeout(3)
                header = b"RTL0" + struct.pack(">II", 1, 0)
                client.sendall(header[:2])
                client.sendall(header[2:])
                while len(commands) < 20:
                    part = client.recv(20 - len(commands))
                    if not part:
                        raise RuntimeError("Missing commands")
                    commands.extend(part)
                client.sendall(bytes([128, 255]) * 16384)
        except Exception as exc:
            errors.append(exc)
        finally:
            server.close()

    thread = threading.Thread(target=serve)
    thread.start()
    source = TCPSource("127.0.0.1", server.getsockname()[1], 446106250, ppm=-2)
    try:
        iq = source.read()
        assert len(iq) == 16384
        assert iq[0].imag == pytest.approx(127.5 / 128)
        with pytest.raises(RuntimeError, match="kesildi"):
            source.read()
    finally:
        source.close()
        thread.join(5)
    assert not thread.is_alive() and not errors
    assert struct.unpack(">BI", commands[:5]) == (2, SAMPLE_RATE)
    assert struct.unpack(">BI", commands[-5:]) == (5, 0xFFFFFFFE)


@pytest.mark.parametrize(
    "change",
    [
        {"name": ""},
        {"spacing_hz": 7000},
        {"squelch_db": float("nan")},
        {"frequency_hz": 2},
        {"bandwidth_hz": 50000},
    ],
)
def test_invalid_channel_settings_rejected(change):
    with pytest.raises(ValueError):
        Channel(**({"name": "A", "frequency_hz": 446006250} | change))


def test_impossible_single_tuner_range_rejected():
    with pytest.raises(ValueError, match="sığmıyor"):
        center_for([Channel("VHF", 150000000), Channel("UHF", 446000000)])
    with pytest.raises(ValueError, match="benzersiz"):
        center_for([Channel("A", 446000000), Channel("a", 446000000)])
    with pytest.raises(ValueError):
        decode_iq(b"\x00")


def test_archive_path_traversal_rejected(tmp_path):
    archive = Archive(tmp_path / "archive")
    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"do not read")
    with archive.connect() as db:
        db.execute(
            "INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason) VALUES('bad','A',446000000,?,1,'../outside.wav','USB','stopped')",
            (EPOCH.isoformat(),),
        )
    with pytest.raises(ValueError):
        archive.audio_path("bad")
