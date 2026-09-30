"""Hardware-free protocol, archive and receive-only transport checks."""

import struct
import time
import wave

import numpy as np
import pytest

from biem_radia.hytera_protocol import (
    CallStatus,
    VoicePacket,
    call_status,
    pcmu_decode,
    transport,
    voice_packet,
)
from biem_radia.hytera_receiver import HyteraReceiver, SlotRecorder
from biem_radia.live_audio import LiveAudio
from biem_radia.storage import Archive


def status_bytes(slot=1, source=1234, target=5678, state=0, service=1, sequence=1):
    payload = struct.pack("<HHHHII", 0, state, service, 1, target, source)
    body = b"\x45\xb8\x10\x00" + payload
    hdap = b"\x02" + body + bytes([(0x32 - sum(body)) & 255, 3])
    return (
        b"2B\x00\x20"
        + sequence.to_bytes(2, "big")
        + bytes([0x84, 1, slot, 3, 4, 0, 0, 0, 9])
        + hdap
    )


def test_transport_tlv_checksum_and_ack():
    packet = transport(status_bytes(slot=2, sequence=99))
    assert packet.slot == 2 and packet.sequence == 99
    assert packet.acknowledgement == b"2B\x00\x01\x00\x63"
    call = call_status(packet.payload)
    assert call == CallStatus(0, 1, "group", 5678, 1234)
    assert call.voice
    assert transport(bytes.fromhex("324200020000")).acknowledgement is None
    assert transport(bytes.fromhex("324200010002")).acknowledgement is None
    assert transport(bytes.fromhex("324200040002")).acknowledgement == bytes.fromhex("324200050002")
    broken = bytearray(packet.payload)
    broken[-3] ^= 1
    with pytest.raises(ValueError, match="sağlama"):
        call_status(bytes(broken))
    for length in range(len(status_bytes())):
        data = status_bytes()[:length]
        with pytest.raises(ValueError):
            parsed = transport(data)
            call_status(parsed.payload)


def test_rtp_extensions_padding_codec_and_mulaw():
    header = struct.pack("!BBHII", 0x91, 0, 65535, 123456, 42)
    data = header + b"CSRC" + b"\x00\x15\x00\x03" + b"\x00" * 12 + bytes([255, 127, 0, 128])
    packet = voice_packet(data)
    assert packet.sequence == 65535 and packet.ssrc == 42
    np.testing.assert_array_equal(pcmu_decode(packet.audio), [0, 0, -32124, 32124])
    padded = bytes([data[0] | 32]) + data[1:] + b"\x00\x02"
    assert voice_packet(padded) == packet
    with pytest.raises(ValueError):
        voice_packet(data[:18])
    with pytest.raises(ValueError, match="PCMU"):
        voice_packet(data[:1] + b"\x08" + data[2:])
    with pytest.raises(ValueError):
        voice_packet(bytes([data[0] | 32]) + data[1:] + b"\x00")


def test_two_slot_archive_reordering_loss_and_unknown_rf(tmp_path):
    archive = Archive(tmp_path)
    events = []
    monitor = LiveAudio()
    a, b = [SlotRecorder(archive, n, monitor, events.append) for n in (1, 2)]
    now = 1700000000.0
    a.control(CallStatus(0, 1, "group", 88, 101), now)
    b.control(CallStatus(0, 1, "private", 90, 202), now)

    def packet(seq, stamp, ssrc=7):
        return VoicePacket(seq, stamp, ssrc, b"\x80" * 480)

    a.accept(packet(65534, 0), now)
    a.accept(packet(0, 960), now + 0.12)
    a.accept(packet(65535, 480), now + 0.13)  # reordered, no loss
    a.accept(packet(0, 960), now + 0.14)  # duplicate
    a.accept(packet(2, 1920), now + 0.24)  # sequence 1 missing
    a.tick(now + 0.45)
    b.accept(packet(5, 0, 10), now + 0.1)
    a.finish("test")
    b.finish("test")
    rows = {r["slot"]: r for r in archive.search()}
    assert len(rows) == 2
    assert rows[1]["radio_id"] == "101" and rows[1]["group_id"] == "88"
    assert rows[2]["radio_id"] == "202" and rows[2]["group_id"] is None
    assert rows[2]["destination_id"] == "90"
    assert rows[1]["duration"] == 0.3 and a.lost == 1 and a.discarded == 1
    for row in rows.values():
        assert row["frequency_hz"] == 0
        assert row["color_code"] is row["rf_peak_dbm"] is row["rf_peak_dbfs"] is None
        assert row["source"] == "DMR/Hytera-IP"
    with wave.open(str(archive.audio_path(rows[1]["id"]))) as wav:
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), "<i2")
    assert np.all(pcm[1440:1920] == 0)


def test_no_control_no_audio_stale_identity_and_encrypted_service(tmp_path):
    archive = Archive(tmp_path)
    recorder = SlotRecorder(archive, 1, LiveAudio(), lambda _: None)
    now = 1700000000.0
    packet = VoicePacket(1, 0, 9, b"\x80" * 480)
    recorder.accept(packet, now)
    assert not archive.search() and recorder.writer is None
    recorder.control(CallStatus(0, 7, "group", 20, 10), now)  # E2E service is not voice
    recorder.accept(packet, now + 0.1)
    assert recorder.writer is None
    recorder.control(CallStatus(0, 1, "group", 20, 10), now)
    recorder.accept(packet, now + 0.1)
    recorder.tick(now + 2)
    recorder.accept(VoicePacket(2, 480, 9, b"\x80" * 480), now + 2.1)
    assert recorder.call is None and len(archive.search()) == 1
    recorder.control(CallStatus(0, 1, "group", 30, 11), now + 3)
    recorder.accept(packet, now + 3.1)
    recorder.finish("test")
    assert {r["radio_id"] for r in archive.search()} == {"10", "11"}


def test_maximum_90_seconds_two_second_gap(tmp_path):
    archive = Archive(tmp_path)
    recorder = SlotRecorder(archive, 2, LiveAudio(), lambda _: None)
    now = 1700000000.0
    recorder.control(CallStatus(0, 1, "group", 20, 10), now)
    for i in range(1600):
        recorder.accept(VoicePacket(i, i * 480, 3, b"\x80" * 480), now + i * 0.06)
    recorder.finish("test")
    rows = sorted(archive.search(), key=lambda r: r["started_utc"])
    assert len(rows) == 2 and rows[0]["duration"] == 90
    assert 3.9 <= rows[1]["duration"] <= 4.02
    assert all(r["duration"] <= 90 for r in rows)


def test_transport_only_sends_handshake_heartbeat_ack_and_releases_ports(tmp_path, monkeypatch):
    archive = Archive(tmp_path)
    receiver = HyteraReceiver(archive)
    created = []

    class FakeSocket:
        def __init__(self, *args):
            self.sent = []
            self.closed = False
            self.incoming = [bytes.fromhex("324200020000"), status_bytes()]
            created.append(self)

        def setsockopt(self, *args):
            pass

        def bind(self, address):
            self.port = address[1]

        def sendto(self, data, address):
            self.sent.append(data)

        def recvfrom(self, size):
            return self.incoming.pop(0), ("127.0.0.2", self.port)

        def close(self):
            self.closed = True

    iterations = 0

    def ready(sockets, *args):
        nonlocal iterations
        iterations += 1
        if iterations > 3:
            receiver.cancel.set()
        return [s for s in sockets if s.incoming], [], []

    monkeypatch.setattr("biem_radia.hytera_receiver.socket.socket", FakeSocket)
    monkeypatch.setattr("biem_radia.hytera_receiver.select.select", ready)
    receiver.start(
        {
            "local_ip": "127.0.0.1",
            "repeater_ip": "127.0.0.2",
            "rcp_ts1": 30009,
            "rcp_ts2": 30010,
            "rtp_ts1": 30012,
            "rtp_ts2": 30014,
        }
    )
    deadline = time.monotonic() + 3
    while receiver.running and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not receiver.running and len(created) == 4 and all(s.closed for s in created)
    assert not archive.search()
    assert all(
        len(packet) == 6 and packet[:4] in (b"2B\x00\x05", b"2B\x00\x02", b"2B\x00\x01")
        for sock in created
        for packet in sock.sent
    )
