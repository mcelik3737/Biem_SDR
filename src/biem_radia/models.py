from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

SAMPLE_RATE = 960_000
AUDIO_RATE = 16_000


@dataclass(frozen=True)
class Channel:
    name: str
    frequency_hz: int
    spacing_hz: int = 12_500
    bandwidth_hz: int = 12_500
    squelch_db: float = -45.0

    def __post_init__(self):
        if not self.name.strip() or len(self.name) > 100:
            raise ValueError("Kanal adı 1–100 karakter olmalı.")
        if not 24_000_000 <= self.frequency_hz <= 1_766_000_000:
            raise ValueError(
                "Frekans 24–1766 MHz aralığında olmalı; gerçek aralık tunere bağlıdır."
            )
        if self.spacing_hz not in (6250, 12500, 25000):
            raise ValueError("Kanal aralığı 6250, 12500 veya 25000 Hz olmalı.")
        if not 4000 <= self.bandwidth_hz <= 25000:
            raise ValueError("FM filtre genişliği 4000–25000 Hz olmalı.")
        if not isfinite(self.squelch_db) or not -100 <= self.squelch_db <= 0:
            raise ValueError("Squelch −100 ile 0 dBFS arasında olmalı.")


def center_for(channels: list[Channel]) -> int:
    if not channels or len(channels) > 8:
        raise ValueError("1–8 kanal seçilmeli.")
    if len({c.name.casefold() for c in channels}) != len(channels):
        raise ValueError("Kanal adları benzersiz olmalı.")
    # Move the tuner DC spike away from a single channel.
    center = (
        min(c.frequency_hz for c in channels) + max(c.frequency_hz for c in channels)
    ) // 2 + 100_000
    if any(
        abs(c.frequency_hz - center) + c.bandwidth_hz / 2 > SAMPLE_RATE * 0.40 for c in channels
    ):
        raise ValueError(
            "Kanallar tek alıcının kullanılabilir bandına sığmıyor. Ayrı alıcı gerekir."
        )
    return center
