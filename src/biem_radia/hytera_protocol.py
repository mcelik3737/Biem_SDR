"""Receive-only IP Dispatch wire parsing; no radio control commands.

HSTRP/HDAP framing and RCP 0xB845 are described by the HytBridge and
OK-DMR protocol research (see docs/HYTERA_ETHERNET.md). RTP follows RFC 3550.
"""

import struct
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Transport:
    flags: int
    sequence: int
    slot: int | None
    payload: bytes

    @property
    def acknowledgement(self) -> bytes | None:
        if self.flags & (1 | 2 | 8 | 16):
            return None
        if self.payload or self.flags & 4:
            return (
                b"2B\x00" + bytes([5 if self.flags & 4 else 1]) + self.sequence.to_bytes(2, "big")
            )
        return None


def transport(data: bytes) -> Transport:
    if len(data) < 6 or data[:3] != b"2B\x00":
        raise ValueError("Geçersiz HSTRP başlığı")
    flags, sequence = data[3], int.from_bytes(data[4:6], "big")
    if flags & 0xC0:
        raise ValueError("Bilinmeyen HSTRP bayrağı")
    cursor, slot = 6, None
    if flags & 0x20:
        for _ in range(32):
            if cursor + 2 > len(data):
                raise ValueError("Eksik HSTRP seçenek başlığı")
            command, length = data[cursor : cursor + 2]
            cursor += 2
            if cursor + length > len(data):
                raise ValueError("Eksik HSTRP seçeneği")
            if command & 0x7F == 4:
                if length != 1 or data[cursor] not in (1, 2) or slot is not None:
                    raise ValueError("Geçersiz HSTRP slotu")
                slot = data[cursor]
            cursor += length
            if not command & 0x80:
                break
        else:
            raise ValueError("Fazla HSTRP seçeneği")
    return Transport(flags, sequence, slot, data[cursor:])


@dataclass(frozen=True)
class CallStatus:
    state: int
    service: int
    kind: str
    target: int | None
    radio: int | None

    @property
    def voice(self) -> bool:
        return self.service == 1 and self.state in (0, 2, 6)


def call_status(payload: bytes) -> CallStatus | None:
    if len(payload) < 7:
        raise ValueError("Eksik HDAP")
    length = int.from_bytes(payload[3:5], "little")
    if len(payload) != length + 7 or payload[-1] != 3:
        raise ValueError("HDAP uzunluğu/sonlandırıcısı hatalı")
    if payload[-2] != (0x32 - sum(payload[1:-2])) & 255:
        raise ValueError("HDAP sağlama toplamı hatalı")
    if payload[0] & 0x7F != 2 or payload[1:3] != b"\x45\xb8":
        return None
    if length != 16:
        raise ValueError("Röle durum paketi uzunluğu hatalı")
    _, state, service, kind, target, radio = struct.unpack("<HHHHII", payload[5:-2])
    return CallStatus(
        state,
        service,
        {0: "private", 1: "group", 2: "all"}.get(kind, "unknown"),
        target if 1 <= target <= 0xFFFFFF else None,
        radio if 1 <= radio <= 0xFFFFFF else None,
    )


@dataclass(frozen=True)
class VoicePacket:
    sequence: int
    timestamp: int
    ssrc: int
    audio: bytes


def voice_packet(data: bytes) -> VoicePacket:
    if len(data) < 12 or data[0] >> 6 != 2:
        raise ValueError("Geçersiz RTP")
    if data[1] & 0x7F != 0:
        raise ValueError("Desteklenmeyen ses biçimi; yalnız RTP PCMU / PT 0")
    cursor = 12 + 4 * (data[0] & 15)
    if cursor > len(data):
        raise ValueError("Eksik RTP CSRC")
    if data[0] & 16:
        if cursor + 4 > len(data):
            raise ValueError("Eksik RTP uzantısı")
        cursor += 4 + 4 * int.from_bytes(data[cursor + 2 : cursor + 4], "big")
    end = len(data)
    if data[0] & 32:
        padding = data[-1]
        if padding == 0 or padding > end - cursor:
            raise ValueError("Geçersiz RTP dolgu")
        end -= padding
    if not 0 < end - cursor <= 1600:
        raise ValueError("Eksik veya aşırı büyük PCMU yükü")
    seq, stamp, ssrc = struct.unpack("!HII", data[2:12])
    return VoicePacket(seq, stamp, ssrc, data[cursor:end])


def pcmu_decode(data: bytes) -> np.ndarray:
    """ITU G.711 mu-law to signed 16-bit PCM, without the removed audioop module."""
    codes = np.bitwise_xor(np.frombuffer(data, dtype=np.uint8), 255).astype(np.int32)
    magnitude = (((codes & 15) << 3) + 132) << ((codes >> 4) & 7)
    return (np.where(codes & 128, 132 - magnitude, magnitude - 132)).astype("<i2")
