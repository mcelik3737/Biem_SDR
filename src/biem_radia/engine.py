from __future__ import annotations

import logging
import math
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .dmr import DmrBackend, DmrDiscriminator
from .dsp import FMDemodulator
from .models import SAMPLE_RATE, Channel, center_for
from .recorder import CallRecorder
from .scanner import ScanGate
from .sources import TCPSource, USBSource
from .storage import Archive


class Receiver:
    def __init__(self, archive: Archive):
        self.archive = archive
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.messages: queue.Queue[dict] = queue.Queue(maxsize=200)

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def publish(self, kind: str, **fields):
        message = {"kind": kind, **fields}
        try:
            self.messages.put_nowait(message)
        except queue.Full:
            # UI telemetry is expendable; sample data is never silently discarded.
            self.messages.get_nowait()
            self.messages.put_nowait(message)

    def start(
        self,
        channels: list[Channel],
        dll: Path,
        source_kind: str = "USB",
        host: str = "127.0.0.1",
        port: int = 1234,
        ppm: int = 0,
        usb_gain: float = 19,
        scan: bool = False,
        scan_dwell: float = 1.0,
        scan_release: float = 1.0,
    ):
        if self.running:
            raise ValueError("Alım zaten çalışıyor.")
        if not all(math.isfinite(v) and 0.3 <= v <= 10 for v in (scan_dwell, scan_release)):
            raise ValueError("Tarama beklemeleri 0,3–10 saniye olmalı.")
        if scan:
            if not 1 <= len(channels) <= 8 or len({c.name.casefold() for c in channels}) != len(
                channels
            ):
                raise ValueError("Tarama için 1–8 farklı adlı etkin kanal gerekli.")
            center = center_for([channels[0]])
        else:
            center = center_for(channels)
        if source_kind not in ("USB", "rtl_tcp"):
            raise ValueError("Geçersiz kaynak.")
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._scan if scan else self._run,
            args=(channels, dll, source_kind, host, port, ppm, scan_dwell, usb_gain, scan_release)
            if scan
            else (channels, dll, source_kind, host, port, ppm, center, usb_gain),
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def _scan(self, channels, dll, source_kind, host, port, ppm, dwell, usb_gain, release):
        index = 0
        reason = "stopped"
        while not self.stop_event.is_set():
            channel = channels[index]
            reason = self._run(
                [channel],
                dll,
                source_kind,
                host,
                port,
                ppm,
                center_for([channel]),
                usb_gain,
                ScanGate(channel.squelch_db, dwell, release),
            )
            if reason == "error":
                break
            index = (index + 1) % len(channels)
        self.publish("stopped", reason="error" if reason == "error" else "stopped")

    def _run(self, channels, dll, source_kind, host, port, ppm, center, usb_gain, gate=None):
        source = None
        recorders: list[CallRecorder] = []
        digital: dict[str, tuple[DmrDiscriminator, DmrBackend]] = {}
        reason = "stopped"
        try:
            self.publish("status", text="Alıcı açılıyor…")
            for channel in channels:
                if channel.mode == "DMR":
                    digital[channel.name] = (
                        DmrDiscriminator(channel, center),
                        DmrBackend(self.archive, channel, self.archive.root.parent),
                    )
            source = (
                USBSource(dll, center, ppm=ppm, gain_db=usb_gain)
                if source_kind == "USB"
                else TCPSource(host, port, center, ppm)
            )
            # Discard tuner startup transients before starting any recording.
            discarded = 0
            while discarded < SAMPLE_RATE // 4 and not self.stop_event.is_set():
                discarded += len(source.read())
            epoch = datetime.now(timezone.utc)
            analog = [c for c in channels if c.mode == "NFM"]
            recorders = [CallRecorder(self.archive, c, source_kind, epoch) for c in analog]
            demodulators = [FMDemodulator(c, center) for c in analog]
            self.archive.event(
                "INFO",
                f"Alım başladı: {source_kind}, merkez {center}, kanallar {[c.name for c in channels]}",
            )
            self.publish(
                "status",
                text=f"TARAMA • {channels[0].name} • {channels[0].frequency_hz / 1e6:.5f} MHz"
                if gate is not None
                else "ALIM HAZIR • DMR senkronu bekleniyor"
                if digital
                else "ALIM HAZIR • Analog FM",
            )
            last_update = 0.0
            while not self.stop_event.is_set():
                iq = source.read()
                states = []
                for name, (discriminator, backend) in digital.items():
                    pcm, level = discriminator.process(iq)
                    backend.feed(pcm)
                    states.append(
                        {
                            "name": name,
                            "level": round(level, 1),
                            "active": False,
                            "completed": backend.completed,
                            "mode": "DMR",
                            "offset_hz": round(discriminator.offset_hz),
                        }
                    )
                for demod, recorder in zip(demodulators, recorders, strict=True):
                    audio, level = demod.process(iq)
                    recorder.feed(audio, level)
                    states.append(
                        {
                            "name": recorder.channel.name,
                            "level": round(level, 1),
                            "active": recorder.active,
                            "completed": recorder.completed,
                        }
                    )
                if time.monotonic() - last_update >= 0.2:
                    self.publish("levels", channels=states)
                    last_update = time.monotonic()
                if gate is not None:
                    was_held = gate.held
                    move_on = gate.advance(states[0]["level"], len(iq) / SAMPLE_RATE)
                    if gate.held and not was_held:
                        self.publish(
                            "status",
                            text=f"KANALDA BEKLİYOR • {channels[0].name} • Eşik {gate.threshold:g} dBFS",
                        )
                    if move_on:
                        reason = "scan"
                        break
        except Exception as exc:
            reason = "error"
            logging.exception("Receiver failed")
            self.publish("error", text=str(exc))
            try:
                self.archive.event("ERROR", str(exc))
            except Exception:
                logging.exception("Cannot write event log")
        finally:
            for _, backend in digital.values():
                try:
                    backend.close()
                except Exception as exc:
                    reason = "error"
                    logging.exception("DMR finalization failed")
                    self.publish("error", text=f"DMR kapanış hatası: {exc}")
            for recorder in recorders:
                try:
                    recorder.finish(reason)
                except Exception as exc:
                    logging.exception("Cannot finalize recording")
                    reason = "error"
                    self.publish("error", text=f"Kayıt tamamlanamadı: {exc}")
            if source is not None:
                try:
                    source.close()
                except Exception as exc:
                    logging.exception("Cannot close receiver")
                    reason = "error"
                    self.publish("error", text=str(exc))
            try:
                self.archive.event("INFO", f"Alım sonlandı: {reason}")
            except Exception:
                logging.exception("Cannot write final event")
            self.publish("archive_changed")
            if gate is None:
                self.publish("stopped", reason=reason)
        return reason
