"""Known Hytera telemetry: little-endian IEEE754 float32, separate from alarms.

MIB fields and LibreNMS's Hytera voltage/temperature adapters document this
representation. Unknown types/units are not guessed. See HYTERA_ETHERNET.md.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

DATA_BASE = "1.3.6.1.4.1.40297.1.2.1.2."
METRICS = {
    1: "Besleme gerilimi",
    2: "Güç katı sıcaklığı",
    4: "VSWR / anten",
    9: "Slot 1 RSSI (MIB)",
    10: "Slot 2 RSSI (MIB)",
    11: "Besleme türü",
    12: "Batarya bağlantısı",
    13: "Batarya gerilimi",
}
METRIC_OIDS = {f"{DATA_BASE}{n}.0": n for n in METRICS}
# Alarm row -> independent measurement object. Fan and RF power units are unverified.
ALARM_METRICS = {1: 1, 2: 2, 6: 4, 9: 13}


@dataclass(frozen=True)
class Measurement:
    value: float | int | None
    unit: str
    text: str


def decode_measurement(number: int, tag: int, raw: int | str | None) -> Measurement:
    missing = Measurement(None, "", "— / ölçüm yok")
    if number not in METRICS or raw is None:
        return missing
    if number in (11, 12):
        options = {0: "DC", 1: "Batarya"} if number == 11 else {0: "Bağlı değil", 1: "Bağlı"}
        if tag == 2 and isinstance(raw, int) and raw in options:
            return Measurement(raw, "", options[raw])
        return missing
    if number in (9, 10):
        # The MIB says dB, not dBm. -200 is its no-reading default.
        if tag == 2 and isinstance(raw, int) and -200 < raw <= 0:
            return Measurement(raw, "dB", f"{raw} dB")
        return missing
    if tag != 4 or not isinstance(raw, str) or not raw.startswith("hex:") or len(raw) != 12:
        return Measurement(None, "", "— / biçim desteklenmiyor")
    try:
        value = struct.unpack("<f", bytes.fromhex(raw[4:]))[0]
    except (ValueError, struct.error):
        return Measurement(None, "", "— / geçersiz veri")
    # Reject NaN, infinity and subnormal garbage; never switch byte order by plausibility.
    if not math.isfinite(value) or (value != 0 and abs(value) < 1e-6):
        return Measurement(None, "", "— / geçersiz veri")
    if number in (1, 13):
        if not 0 < value <= 100:
            return missing
        return Measurement(value, "V", f"{value:.2f} V")
    if number == 2:
        if not -100 <= value <= 250:
            return missing
        return Measurement(value, "°C", f"{value:.1f} °C")
    if number == 4 and 1 <= value <= 100:
        return Measurement(value, ":1", f"{value:.2f}:1")
    return missing


def measurement_cell(record: dict | None, now: float, running: bool) -> tuple[str, str]:
    if record is None:
        return "— / henüz gelmedi", "—"
    age = max(0, now - record["at"])
    freshness = f"{age:.0f} sn önce"
    if age > 35 or not running:
        freshness += " • eski veri"
    return record["text"], freshness
