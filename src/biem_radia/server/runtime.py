"""Headless adapter. Existing demodulators/recorders are deliberately unchanged."""

from __future__ import annotations

import base64
import io
import json
import logging
import math
import queue
import threading
import time
from collections import deque
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ..engine import Receiver
from ..hytera_receiver import HyteraReceiver
from ..hytera_snmp import SnmpMonitor
from ..inbox import InboxStore
from ..live_audio import LiveAudio
from ..locations import LocationReader
from ..models import Channel
from ..sources import RtlLibrary
from ..spectrum import SpectrumWorker
from ..storage import Archive
from ..vector_map import COS39, VectorMap, Viewport, find_package


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text("utf-8")) if path.exists() else {}
    if not isinstance(value, dict):
        raise ValueError(f"Geçersiz ayar dosyası: {path.name}")
    return value


class BrowserAudio(LiveAudio):
    """Bounded independent tap; never opens a sound device on the server."""

    def __init__(self):
        super().__init__()
        self.buffer_lock = threading.Lock()
        self.buffers: dict[tuple[str, str], deque] = {}
        self.sequence = 0

    def _feed(self, channel: str, stream: str, audio: np.ndarray, rate: int, label: str):
        stream = str(stream)
        super()._feed(channel, stream, audio, rate, label)
        if rate not in (8000, 16000) or not len(audio):
            return
        pcm = (np.clip(np.nan_to_num(audio), -1, 1) * 32767).astype("<i2")
        now = time.monotonic()
        with self.buffer_lock:
            self.buffers = {k: v for k, v in self.buffers.items() if v and now - v[-1][0] < 2}
            buffer = self.buffers.setdefault((channel, stream), deque(maxlen=64))
            for offset in range(0, min(len(pcm), rate * 2), rate // 4):
                self.sequence += 1
                buffer.append(
                    (now, self.sequence, rate, pcm[offset : offset + rate // 4].tobytes())
                )

    def packets(self, channel: str, stream: str, after: int) -> dict:
        now = time.monotonic()
        with self.buffer_lock:
            frames = [
                p
                for p in self.buffers.get((channel, stream), ())
                if p[1] > after and now - p[0] < 1.5
            ]
            return {
                "packets": [
                    {"sequence": seq, "rate": rate, "pcm": base64.b64encode(pcm).decode("ascii")}
                    for _, seq, rate, pcm in frames
                ]
            }

    def streams(self, channel: str) -> list[dict]:
        with self.lock:
            return [
                {"id": stream, "label": self.stream_labels.get((name, stream), stream)}
                for (name, stream), (at, _) in self.meters.items()
                if name == channel and time.monotonic() - at < 2
            ]

    def clear(self):
        super().clear()
        with self.buffer_lock:
            self.buffers.clear()


class RadioRuntime:
    def __init__(self, project: Path):
        self.project = project.resolve()
        self.archive = Archive(self.project / "data", protected=True)
        self.receiver = Receiver(self.archive)
        self.hytera = HyteraReceiver(self.archive)
        self.audio = BrowserAudio()
        self.receiver.monitor = self.audio
        self.hytera.monitor = self.audio
        self.snmp = SnmpMonitor(self.archive.root)
        self.spectrum = SpectrumWorker()
        self.inbox = InboxStore(self.archive.root)
        self.locations = LocationReader(self.archive.root)
        self.lock = threading.RLock()
        self.map_lock = threading.Lock()
        self.cancel = threading.Event()
        self.thread: threading.Thread | None = None
        self.levels: dict[str, dict] = {}
        self.connected = False
        self.status = "Alıcı beklemede"
        self.repeater: dict = {}
        self.repeater_status = "Röle alımı kapalı"
        self.sweep: dict = {}
        self.updated = 0.0
        self.vector: VectorMap | None = None
        self.channels: list[Channel] = []
        self.reload_channels()

    @property
    def dll(self) -> Path:
        return self.project / "vendor/rtl-sdr/package/x64/rtlsdr.dll"

    def reload_channels(self):
        path = self.archive.root / "channels.json"
        values = json.loads(path.read_text("utf-8")) if path.exists() else []
        if not isinstance(values, list) or len(values) > 8:
            raise ValueError("Kanal ayarları 0–8 kanal içermeli.")
        channels = [Channel(**item) for item in values]
        if len({c.name.casefold() for c in channels}) != len(channels):
            raise ValueError("Kanal adları benzersiz olmalı.")
        self.channels = channels

    def inventory(self) -> list[str]:
        with self.archive.connect() as db:
            archived = [r[0] for r in db.execute("SELECT DISTINCT channel FROM calls")]
        return sorted(
            set([c.name for c in self.channels] + archived + ["Hytera • Slot 1", "Hytera • Slot 2"])
        )

    def start(self):
        self.cancel.clear()
        self.thread = threading.Thread(target=self._poll, daemon=True, name="biem-server-state")
        self.thread.start()

    def _poll(self):
        while not self.cancel.wait(0.2):
            try:
                self.poll_once()
            except Exception:
                logging.exception("Server state update failed; receivers continue")
                with self.lock:
                    self.status = "Durum güncellenemedi; sunucu günlüğünü kontrol edin."

    def poll_once(self):
        with self.lock:
            for _ in range(200):
                try:
                    item = self.receiver.messages.get_nowait()
                except queue.Empty:
                    break
                if item["kind"] == "levels":
                    self.levels.update(
                        {v["name"]: {**v, "updated": time.time()} for v in item["channels"]}
                    )
                    self.updated = time.time()
                elif item["kind"] == "connection":
                    self.connected = item["connected"]
                    if not self.connected:
                        self.levels.clear()
                elif item["kind"] == "tuning":
                    # A scanned-out channel must not keep a green/audio state.
                    self.levels.clear()
                elif item["kind"] in ("error", "status"):
                    self.status = ("Hata: " if item["kind"] == "error" else "") + item["text"]
                elif item["kind"] == "stopped":
                    self.connected = False
                    self.levels.clear()
                    if not self.status.startswith("Hata:"):
                        self.status = "Alım durduruldu"
            for _ in range(256):
                try:
                    item = self.hytera.messages.get_nowait()
                except queue.Empty:
                    break
                if item["kind"] == "snapshot":
                    self.repeater = {**item, "updated": time.time()}
                elif item["kind"] in ("status", "error", "stopped"):
                    if item["kind"] != "stopped" or not self.repeater_status.startswith("Hata:"):
                        self.repeater_status = (
                            "Hata: " if item["kind"] == "error" else ""
                        ) + item.get("text", "")
                    if item["kind"] in ("error", "stopped"):
                        self.repeater = {}
            for message in self.spectrum.take_messages():
                values = message.get("values")
                if values is not None:
                    message = {**message, "values": np.nan_to_num(values, nan=-120).tolist()}
                self.sweep.update(message)
            self.inbox.poll()
            self.locations.poll()

    def snapshot(self) -> dict:
        with self.lock:
            channels = []
            for c in self.channels:
                state = self.levels.get(c.name, {})
                if time.time() - state.get("updated", 0) > 3:
                    state = {}
                channels.append(
                    {
                        **asdict(c),
                        **state,
                        **self.audio.state(c.name),
                        "streams": self.audio.streams(c.name),
                        "connected": self.connected and c.enabled,
                    }
                )
            for slot in (1, 2):
                name = f"Hytera • Slot {slot}"
                channels.append(
                    {
                        "name": name,
                        "mode": "DMR / Ethernet",
                        "enabled": True,
                        "frequency_hz": None,
                        "squelch_db": None,
                        "connected": self.hytera.running
                        and self.repeater.get("linked", 0) > 0
                        and time.time() - self.repeater.get("updated", 0) < 5,
                        **self.audio.state(name),
                        "streams": self.audio.streams(name),
                    }
                )
            return {
                "running": self.receiver.running,
                "hytera_running": self.hytera.running,
                "spectrum_running": self.spectrum.running,
                "channels": channels,
            }

    def _usb_index(self) -> int:
        saved = read_object(self.archive.root / "device.json")
        library = RtlLibrary(self.dll)
        try:
            items = list(library.inventory())
        finally:
            library.close()
        matches = [p for p in items if saved.get("serial") and p["serial"] == saved["serial"]]
        if len(matches) == 1:
            return int(matches[0]["index"])
        if saved.get("serial") and not matches:
            raise ValueError("Kaydedilmiş USB alıcı bağlı değil.")
        candidates = matches or items
        match = next((p for p in candidates if p["index"] == saved.get("index", 0)), None)
        if match is None:
            raise ValueError("USB alıcı bulunamadı; masaüstü cihaz ayarını kontrol edin.")
        return int(match["index"])

    def control(self, target: str, action: str, low: float = 420, high: float = 421):
        with self.lock:
            if action == "stop":
                worker = {
                    "receiver": self.receiver,
                    "hytera": self.hytera,
                    "spectrum": self.spectrum,
                }[target]
                worker.stop()
                return
            if target == "receiver":
                if self.spectrum.running:
                    raise ValueError("Önce spektrum ölçümünü durdurun.")
                self.reload_channels()
                cfg = read_object(self.archive.root / "receiver.json")
                source = cfg.get("source", "USB")
                self.receiver.start(
                    [c for c in self.channels if c.enabled],
                    self.dll,
                    source_kind=source,
                    host=cfg.get("host", "127.0.0.1"),
                    port=int(cfg.get("port", 1234)),
                    ppm=int(cfg.get("ppm", 0)),
                    usb_gain=float(cfg.get("usb_gain", 19)),
                    scan=cfg.get("receive_mode") == "Tarama",
                    scan_dwell=float(cfg.get("scan_dwell", 1)),
                    scan_release=float(cfg.get("scan_release", 1)),
                    usb_agc=cfg.get("usb_agc") == "Tuner AGC",
                    usb_index=self._usb_index() if source == "USB" else 0,
                )
            elif target == "hytera":
                profile = read_object(self.archive.root / "hytera.json")
                self.hytera.start(profile)
                if profile.get("snmp_enabled"):
                    self.snmp.start(profile["local_ip"], profile["repeater_ip"])
            elif target == "spectrum":
                if self.receiver.running:
                    raise ValueError(
                        "Spektrum için önce SDR alımını durdurun. Röle alımı devam edebilir."
                    )
                cfg = read_object(self.archive.root / "receiver.json")
                self.sweep.clear()
                self.spectrum.start(
                    self.dll,
                    low * 1e6,
                    high * 1e6,
                    "Hamming",
                    self._usb_index(),
                    int(cfg.get("ppm", 0)),
                    float(cfg.get("usb_gain", 19)),
                    cfg.get("usb_agc") == "Tuner AGC",
                )

    def close(self):
        self.cancel.set()
        for worker in (self.receiver, self.hytera, self.spectrum, self.snmp):
            worker.stop()
        if self.thread:
            self.thread.join()
        for worker in (self.receiver, self.hytera, self.spectrum, self.snmp):
            if worker.thread:
                while worker.thread.is_alive():
                    worker.thread.join(timeout=10)
                    if worker.thread.is_alive():
                        logging.warning(
                            "Waiting for recording finalization: %s", type(worker).__name__
                        )

    def map_image(self, lon: float, lat: float, zoom: int) -> bytes:
        with self.map_lock:
            if self.vector is None:
                path = find_package(self.archive.root)
                if path is None:
                    raise ValueError("Sunucuda çevrimdışı sokak haritası paketi bulunamadı.")
                self.vector = VectorMap(path)
            scale = 256 * 2**zoom / (360 * COS39)
            view = Viewport(1000, 600, (lon * COS39, -lat), scale)
            result = self.vector.render(view)
            if result is None:
                raise ValueError("Harita çizilemedi.")
            image, _ = result
            output = io.BytesIO()
            image.save(output, "PNG")
            return output.getvalue()


def finite_json(value):
    """Decoder telemetry may contain numpy scalars; never emit NaN in JSON."""
    if isinstance(value, dict):
        return {str(k): finite_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [finite_json(v) for v in value]
    if isinstance(value, np.generic):
        return finite_json(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
