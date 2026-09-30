from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .tones import CTCSS, DCS

SAMPLE_RATE = 960_000
AUDIO_RATE = 16_000


@dataclass(frozen=True)
class Channel:
    name: str
    frequency_hz: int
    spacing_hz: int = 12_500
    bandwidth_hz: int = 12_500
    squelch_db: float = -45.0
    mode: str = "NFM"
    system: str = "Default"
    color_code: int | None = None
    enabled: bool = True
    tone_mode: str = "CSQ"
    tone_value: str = "67.0"
    follow_signal: bool = True

    def __post_init__(self):
        if not isinstance(self.follow_signal, bool):
            raise ValueError("Yakın sinyal kilidi açık/kapalı olmalı.")
        if self.mode not in ("NFM", "DMR", "TETRA", "APCO25", "NXDN", "AUTO"):
            raise ValueError("Geçersiz kanal modu.")
        if self.mode == "AUTO" and self.color_code is not None:
            raise ValueError("Otomatik modda CC boş olmalı; alınan protokolden bulunur.")
        if self.tone_mode not in ("CSQ", "CTCSS", "DCS", "DCS-I"):
            raise ValueError("Geçersiz analog ton modu.")
        if self.tone_mode == "CTCSS" and float(self.tone_value) not in CTCSS:
            raise ValueError("Standart CTCSS tonu seçin.")
        if self.tone_mode in ("DCS", "DCS-I") and self.tone_value not in DCS:
            raise ValueError("Standart DCS kodu seçin.")
        if not self.system.strip() or len(self.system) > 100:
            raise ValueError("Sistem adı 1–100 karakter olmalı.")
        maximum = {"TETRA": 63, "APCO25": 4095, "NXDN": 63}.get(self.mode, 15)
        if self.color_code is not None and not 0 <= self.color_code <= maximum:
            raise ValueError(f"CC / NAC / RAN 0–{maximum} olmalı veya boş bırakılmalı.")
        if self.mode == "DMR" and self.spacing_hz != 12500:
            raise ValueError("DMR taşıyıcısı 12500 Hz kanal aralığı kullanır; slot bundan ayrıdır.")
        if self.mode == "TETRA" and (self.spacing_hz != 25000 or self.bandwidth_hz < 20000):
            raise ValueError("TETRA için 25000 Hz kanal aralığı ve en az 20000 Hz filtre seçin.")
        if self.mode == "APCO25" and self.spacing_hz != 12500:
            raise ValueError("APCO25 Phase 1 için 12500 Hz kanal aralığı seçin.")
        if self.mode == "NXDN" and self.spacing_hz not in (6250, 12500):
            raise ValueError("NXDN için 6250 veya 12500 Hz kanal aralığı seçin.")
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
        abs(c.frequency_hz - center)
        + (25000 if c.mode == "AUTO" else c.bandwidth_hz) / 2
        + (6500 if c.follow_signal else 0)
        > SAMPLE_RATE * 0.40
        for c in channels
    ):
        raise ValueError(
            "Kanallar tek alıcının kullanılabilir bandına sığmıyor. Ayrı alıcı gerekir."
        )
    return center
