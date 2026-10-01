"""Validated admin settings, compatible with the existing desktop JSON files."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from ..models import Channel
from .auth import AuthError


class SettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ChannelSettings(SettingsModel):
    name: str = Field(min_length=1, max_length=100)
    frequency_hz: int = Field(ge=24_000_000, le=1_766_000_000)
    spacing_hz: Literal[6250, 12500, 25000] = 12500
    bandwidth_hz: int = Field(default=12500, ge=4000, le=25000)
    squelch_db: float = Field(default=-45, ge=-100, le=0)
    mode: Literal["NFM", "DMR", "TETRA", "APCO25", "NXDN", "AUTO"] = "NFM"
    system: str = Field(default="Default", min_length=1, max_length=100)
    color_code: int | None = Field(default=None, ge=0, le=4095)
    enabled: bool = True
    tone_mode: Literal["CSQ", "CTCSS", "DCS", "DCS-I"] = "CSQ"
    tone_value: str = Field(default="67.0", max_length=20)
    follow_signal: bool = True

    def channel(self) -> Channel:
        values = self.model_dump()
        values["name"] = self.name.strip()
        if self.mode in ("NFM", "AUTO"):
            values["color_code"] = None
        if self.mode != "NFM":
            values["tone_mode"] = "CSQ"
        if values["name"].casefold().startswith("hytera • slot"):
            raise ValueError("Bu ad Ethernet röle kanalları için ayrılmıştır.")
        return Channel(**values)


class Revision(SettingsModel):
    revision: str = Field(pattern=r"^[0-9a-f]{64}$")


class ChannelsUpdate(Revision):
    channels: list[ChannelSettings] = Field(max_length=8)


class ReceiverSettings(SettingsModel):
    source: Literal["USB", "rtl_tcp"] = "USB"
    host: str = Field(default="127.0.0.1", min_length=1, max_length=253, pattern=r"^[\w.:-]+$")
    port: int = Field(default=1234, ge=1, le=65535)
    ppm: int = Field(default=0, ge=-200, le=200)
    usb_gain: float = Field(default=19, ge=-10, le=50)
    usb_agc: Literal["Manuel", "Tuner AGC"] = "Manuel"
    receive_mode: Literal["Sabit", "Tarama"] = "Sabit"
    scan_dwell: float = Field(default=1, ge=0.3, le=10)
    scan_release: float = Field(default=1, ge=0.3, le=10)


class ReceiverUpdate(Revision):
    receiver: ReceiverSettings


class DeviceSettings(SettingsModel):
    index: int = Field(default=0, ge=0, le=255)
    serial: str = Field(default="", max_length=256)


class DeviceUpdate(Revision):
    device: DeviceSettings


def snapshot(root: Path, name: str, default):
    path = root / (name + ".json")
    raw = path.read_bytes() if path.exists() else b""
    return (json.loads(raw) if raw else default), hashlib.sha256(raw).hexdigest()


def channel_list(value) -> list[Channel]:
    if not isinstance(value, list) or len(value) > 8:
        raise ValueError("Kanal ayarları 0–8 kanal içermeli.")
    channels = [ChannelSettings.model_validate(item).channel() for item in value]
    if len({c.name.casefold() for c in channels}) != len(channels):
        raise ValueError("Kanal adları benzersiz olmalı.")
    return channels


def editable(root: Path, name: str) -> dict:
    """Invalid local JSON stays on disk until an explicit, revision-checked repair."""
    path = root / (name + ".json")
    raw = path.read_bytes() if path.exists() else None
    schema = ReceiverSettings if name == "receiver" else DeviceSettings
    default = [] if name == "channels" else schema().model_dump()
    result = {"value": default, "revision": hashlib.sha256(raw or b"").hexdigest()}
    try:
        value = json.loads(raw) if raw is not None else default
        if name == "channels":
            result["value"] = [asdict(channel) for channel in channel_list(value)]
        else:
            if not isinstance(value, dict):
                raise ValueError("Ayar dosyası nesne olmalı.")
            result["value"] = schema.model_validate(
                {key: v for key, v in value.items() if key in schema.model_fields}
            ).model_dump()
    except (ValueError, TypeError):
        result["error"] = (
            f"{name}.json okunamadı veya geçersiz değer içeriyor. "
            "Düzenleme için başlangıç değerleri gösteriliyor. "
            "Kontrol edip Kaydet'e basın; eski dosya yedeklenecek."
        )
    return result


def save(root: Path, name: str, revision: str, value):
    """Caller holds the runtime lock. Never overwrite a stale browser's config."""
    path = root / (name + ".json")
    previous = path.read_bytes() if path.exists() else b""
    if hashlib.sha256(previous).hexdigest() != revision:
        raise AuthError("Ayar başka bir yerde değişti. Sayfayı yenileyip tekrar deneyin.", 409)
    if previous:
        backup = root / "server/config-backups"
        backup.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        (backup / f"{name}-{stamp}-{uuid4().hex[:8]}.json").write_bytes(previous)
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=root, prefix=name + "-", suffix=".part", delete=False
        ) as output:
            temporary = Path(output.name)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return hashlib.sha256(payload).hexdigest()
