"""Channel-filter RMS power. dBm requires an external antenna-port reference.

This is RF power, never decoded audio volume or an FFT-bin peak. Calibration is
valid only for the same receiver, frequency, mode, filter, PPM and manual gain.
"""

from __future__ import annotations

import json
import math
import time
import uuid
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from .models import SAMPLE_RATE, Channel


def device_identity(source, index: int) -> str | None:
    """Do not bind absolute calibration to a USB enumeration index."""
    try:
        devices = source.library.inventory()
        device = devices[index]
        serial = device.get("serial")
        if not serial or sum(d.get("serial") == serial for d in devices) != 1:
            return None
        return json.dumps(
            [device.get("manufacturer"), device.get("product"), serial], ensure_ascii=False
        )
    except (AttributeError, IndexError, OSError, RuntimeError):
        return None


@dataclass
class PowerContext:
    device: str | None = None
    gain_db: float | None = None
    ppm: int = 0
    clipped: bool = False
    settling: bool = False


def calibration_key(settings: dict) -> str:
    fields = ("device", "gain_db", "ppm", "frequency_hz", "bandwidth_hz", "mode", "sample_rate")
    key = {field: settings[field] for field in fields}
    if key["gain_db"] is not None:
        key["gain_db"] = float(key["gain_db"])
    return json.dumps(key, sort_keys=True)


class PowerCalibrations:
    def __init__(self, root: Path):
        self.path = root / "rf-power-calibration.json"
        self.entries = {}
        self.error = ""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text("utf-8"))
                for entry in data["profiles"]:
                    offset = float(entry["offset_db"])
                    if not math.isfinite(offset) or abs(offset) > 200 or not entry["id"]:
                        raise ValueError("Geçersiz güç kalibrasyonu")
                    entry["offset_db"] = offset
                    self.entries[calibration_key(entry["settings"])] = entry
            except (OSError, ValueError, TypeError, KeyError):
                self.entries.clear()
                self.error = "Güç kalibrasyonu okunamadı; dBm devre dışı."

    def save_reference(self, reading: dict, reference_dbm: float):
        settings = reading.get("rf_context", {})
        value = reading.get("rf_dbfs")
        if (
            not settings.get("device")
            or settings.get("gain_db") is None
            or reading.get("rf_status") in ("clipped", "settling", "invalid")
            or value is None
            or not math.isfinite(value)
            or not -110 < value < -3
            or time.time() - reading.get("rf_observed", 0) > 2
        ):
            raise ValueError(
                "Güncel, kararlı USB ölçümü, benzersiz seri ve manuel kazanç gerekli; doygun veya çok zayıf sinyalle kalibre etmeyin."
            )
        if not math.isfinite(reference_dbm) or not -160 <= reference_dbm <= 10:
            raise ValueError("Referans seviyesi −160 ile +10 dBm arasında olmalı.")
        entry = dict(
            id=uuid.uuid4().hex,
            settings=settings,
            offset_db=reference_dbm - value,
            reference_dbm=reference_dbm,
            measured_dbfs=value,
            at_utc=time.time(),
        )
        self.entries[calibration_key(settings)] = entry
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"profiles": list(self.entries.values())}, ensure_ascii=False, indent=2),
            "utf-8",
        )
        temporary.replace(self.path)
        return entry


class RFPowerMeter:
    def __init__(self, channel: Channel, context: PowerContext, calibrations: PowerCalibrations):
        self.channel, self.context, self.calibrations = channel, context, calibrations
        # Bounded history; old/imported calls without complete measurements stay uncalibrated.
        self.history: deque[tuple[float, float, dict]] = deque(maxlen=24_000)
        self.latest: dict = {}

    def observe(self, level: float, seconds: float, *, end: float | None = None) -> dict:
        end = time.time() if end is None else end
        context, channel = self.context, self.channel
        settings = dict(
            device=context.device,
            gain_db=context.gain_db,
            ppm=context.ppm,
            frequency_hz=channel.frequency_hz,
            bandwidth_hz=25000 if channel.mode == "TETRA" else channel.bandwidth_hz,
            mode=channel.mode,
            sample_rate=SAMPLE_RATE,
        )
        valid = math.isfinite(level) and seconds > 0
        status = (
            "invalid"
            if not valid
            else "clipped"
            if context.clipped
            else "settling"
            if context.settling
            else "uncalibrated"
        )
        entry = self.calibrations.entries.get(calibration_key(settings))
        dbm = None
        calibration_id = None
        if status == "uncalibrated" and context.device and context.gain_db is not None and entry:
            dbm = level + entry["offset_db"]
            calibration_id = entry["id"]
            status = "calibrated"
        reading = dict(
            rf_dbfs=level if valid else None,
            rf_dbm=dbm,
            rf_status=status,
            rf_context=settings,
            rf_calibration_id=calibration_id,
            rf_observed=end,
        )
        self.latest = reading
        self.history.append((end - seconds, end, reading))
        return reading

    def summary(self, start: float, end: float, *, timing="sample_clock") -> dict:
        records = [(a, b, reading) for a, b, reading in self.history if b > start and a < end]
        valid = [reading for _, _, reading in records if reading["rf_dbfs"] is not None]
        if not valid:
            return {}
        peak = max(valid, key=lambda reading: reading["rf_dbfs"])
        complete = records[0][0] <= start + 0.05 and records[-1][1] >= end - 0.05
        complete = complete and all(
            b[0] - a[1] <= 0.05 for a, b in zip(records, records[1:], strict=False)
        )
        calibrated = complete and all(r["rf_dbm"] is not None for _, _, r in records)
        dbm_peak = max(valid, key=lambda reading: reading["rf_dbm"]) if calibrated else None
        status = (
            "calibrated"
            if calibrated
            else "partial_window"
            if not complete
            else "/".join(sorted({r["rf_status"] for _, _, r in records}))
        )
        info = dict(
            method="channel_filter_block_rms",
            timing=timing,
            channel_shared_rf=True,
            samples=len(records),
            status=status,
            peak_dbfs_context=peak["rf_context"],
            peak_dbm_context=dbm_peak["rf_context"] if dbm_peak else None,
            calibration_id=dbm_peak["rf_calibration_id"] if dbm_peak else None,
        )
        return dict(
            rf_peak_dbfs=peak["rf_dbfs"],
            rf_peak_dbm=dbm_peak["rf_dbm"] if dbm_peak else None,
            rf_power_info=json.dumps(info, ensure_ascii=False),
        )


def peak_text(values) -> str:
    dbm, dbfs = values["rf_peak_dbm"], values["rf_peak_dbfs"]
    if dbm is not None:
        return f"{dbm:.1f} dBm"
    if dbfs is not None:
        return f"{dbfs:.1f} dBFS"
    return "—"


def power_suffix(values: dict | None) -> str:
    if not values:
        return ""
    text = peak_text(values)
    return "" if text == "—" else "_max" + text.replace(" ", "")


def live_power_text(reading: dict | None) -> str:
    if not reading or reading.get("rf_dbfs") is None:
        return "Anten: — dBm\nRF: — dBFS"
    dbfs = reading["rf_dbfs"]
    if reading.get("rf_dbm") is not None:
        return f"Anten ≈ {reading['rf_dbm']:.1f} dBm\nRF: {dbfs:.1f} dBFS · kalibre"
    status = {"clipped": "doygun", "settling": "kazanç değişiyor"}.get(
        reading.get("rf_status", ""), "kalibrasyon gerekli"
    )
    return f"Anten: — dBm\n{dbfs:.1f} dBFS · {status}"
