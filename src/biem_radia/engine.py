from __future__ import annotations

import logging
import math
import queue
import threading
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .auto_decode import AutoChannel
from .dmr import DmrBackend, DmrDiscriminator
from .dsp import FMDemodulator
from .live_audio import LiveAudio
from .models import SAMPLE_RATE, Channel, center_for
from .recorder import CallRecorder
from .rf_power import PowerCalibrations, PowerContext, RFPowerMeter, device_identity
from .scanner import AutoScanGate, DmrScanGate, ScanGate, TetraScanGate
from .signal_follow import SignalFollower
from .signal_peak import PeakMonitor
from .sources import TCPSource, USBSource
from .storage import Archive
from .tetra import TetraBackend


class Receiver:
    def __init__(self, archive: Archive):
        self.archive = archive
        self.stop_event = threading.Event()
        self.usb_settings = (19.0, False)
        self.usb_index = 0
        self.thread: threading.Thread | None = None
        self.messages: queue.Queue[dict] = queue.Queue(maxsize=200)
        self.monitor = LiveAudio()

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
        usb_agc: bool = False,
        usb_index: int = 0,
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
        self.monitor.clear()
        self.usb_settings = (usb_gain, usb_agc)
        self.usb_index = usb_index
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
        self.monitor.stop()

    def _read_source(self, source):
        try:
            return source.read()
        except (OSError, RuntimeError):
            self.publish("connection", connected=False)
            raise

    def _scan(self, channels, dll, source_kind, host, port, ppm, dwell, usb_gain, release):
        index = 0
        reason = "stopped"
        while not self.stop_event.is_set():
            channel = channels[index]
            if channel.mode == "DMR":
                channel = replace(channel, color_code=None)
            reason = self._run(
                [channel],
                dll,
                source_kind,
                host,
                port,
                ppm,
                center_for([channel]),
                usb_gain,
                (
                    {"TETRA": TetraScanGate, "DMR": DmrScanGate, "AUTO": AutoScanGate}.get(
                        channel.mode, ScanGate
                    )
                )(channel.squelch_db, dwell, release),
            )
            if reason == "error":
                break
            index = (index + 1) % len(channels)
        self.publish("stopped", reason="error" if reason == "error" else "stopped")

    def _run(self, channels, dll, source_kind, host, port, ppm, center, usb_gain, gate=None):
        source = None
        recorders: list[CallRecorder] = []
        digital: dict[str, tuple[DmrDiscriminator, DmrBackend]] = {}
        tetra = []
        automatic = []
        reason = "stopped"
        try:
            self.publish("status", text="Alıcı açılıyor…")
            self.publish("tuning", names=[c.name for c in channels])
            for channel in channels:
                if channel.mode == "AUTO":
                    automatic.append(
                        AutoChannel(
                            self.archive, channel, center, source_kind, datetime.now(timezone.utc)
                        )
                    )
                if channel.mode == "TETRA":
                    tetra.append(TetraBackend(self.archive, channel, center))
                if channel.mode in ("DMR", "APCO25", "NXDN"):
                    digital[channel.name] = (
                        DmrDiscriminator(channel, center),
                        DmrBackend(self.archive, channel, self.archive.root.parent),
                    )
            applied_settings = self.usb_settings
            try:
                source = (
                    USBSource(
                        dll,
                        center,
                        index=self.usb_index,
                        ppm=ppm,
                        gain_db=applied_settings[0],
                        agc=applied_settings[1],
                    )
                    if source_kind == "USB"
                    else TCPSource(host, port, center, ppm)
                )
            except (OSError, RuntimeError):
                self.publish("connection", connected=False)
                raise
            self.publish("connection", connected=True)
            # Discard tuner startup transients before starting any recording.
            if isinstance(source, USBSource) and hasattr(source, "gain_db"):
                self.publish(
                    "gain",
                    text="Tuner AGC açık"
                    if applied_settings[1]
                    else f"Uygulanan USB kazancı: {source.gain_db:g} dB",
                )
            discarded = 0
            while discarded < SAMPLE_RATE // 4 and not self.stop_event.is_set():
                discarded += len(self._read_source(source))
            epoch = datetime.now(timezone.utc)
            for auto_channel in automatic:
                if auto_channel.recorder is not None:
                    auto_channel.recorder.epoch = epoch
            analog = [c for c in channels if c.mode == "NFM"]
            recorders = [CallRecorder(self.archive, c, source_kind, epoch) for c in analog]
            demodulators = [FMDemodulator(c, center) for c in analog]
            power_context = PowerContext(
                device=device_identity(source, self.usb_index),
                gain_db=getattr(source, "gain_db", None),
                ppm=ppm,
            )
            calibrations = PowerCalibrations(self.archive.root)
            if calibrations.error:
                self.archive.event("WARNING", calibrations.error)
            owners = [*recorders, *tetra, *(b.importer for _, b in digital.values())]
            for auto_channel in automatic:
                assert auto_channel.dmr is not None
                assert auto_channel.recorder is not None and auto_channel.tetra is not None
                owners.extend(
                    [auto_channel.recorder, auto_channel.dmr.importer, auto_channel.tetra]
                )
            for owner in owners:
                owner.rf_power = RFPowerMeter(owner.channel, power_context, calibrations)
            power_settles_at = 0.0
            self.archive.event(
                "INFO",
                f"Alım başladı: {source_kind}, merkez {center}, PPM {ppm:+d}, kanallar {[c.name for c in channels]}",
            )
            self.publish(
                "status",
                text=f"TARAMA • {channels[0].name} • {channels[0].frequency_hz / 1e6:.5f} MHz"
                if gate is not None
                else "ALIM HAZIR • " + ", ".join(dict.fromkeys(c.mode for c in channels)),
            )
            last_update = 0.0
            for backend_tetra in tetra:
                backend_tetra.audio_sink = lambda slot, audio, name=backend_tetra.channel.name: (
                    self.monitor.feed(name, f"tetra-{slot}", audio, 8000, f"TETRA slot {slot}")
                )
            for auto_channel in automatic:
                auto_channel.monitor = self.monitor
                auto_tetra = getattr(auto_channel, "tetra", None)
                if auto_tetra is not None:
                    auto_tetra.audio_sink = lambda slot, audio, name=auto_channel.channel.name: (
                        self.monitor.feed(name, f"tetra-{slot}", audio, 8000, f"TETRA slot {slot}")
                    )
            peaks = PeakMonitor(channels, center)
            followers = {c.name: SignalFollower(c, channels) for c in channels}
            while not self.stop_event.is_set():
                if isinstance(source, USBSource) and applied_settings != self.usb_settings:
                    applied_settings = self.usb_settings
                    self.publish("gain", text=source.set_gain(*applied_settings))
                    power_context.gain_db = getattr(source, "gain_db", None)
                    power_settles_at = time.monotonic() + 1.0
                iq = self._read_source(source)
                power_context.settling = time.monotonic() < power_settles_at
                power_context.clipped = bool(
                    np.any(np.abs(np.real(iq)) >= 127.5 / 128)
                    or np.any(np.abs(np.imag(iq)) >= 127.5 / 128)
                )
                peaks.feed(iq)
                update_due = time.monotonic() - last_update >= 0.2
                measurements = {}
                if update_due:
                    measurements = peaks.measure()
                    for name, follower in followers.items():
                        previous_offset = follower.offset
                        follower.observe(peaks.axis, peaks.power, time.monotonic())
                        if follower.offset != previous_offset:
                            self.archive.event(
                                "INFO",
                                f"RF takip • {name} • "
                                + (
                                    "kilit bırakıldı"
                                    if follower.offset is None
                                    else f"kilit {follower.channel.frequency_hz + follower.offset:.0f} Hz • fark {follower.offset:+.0f} Hz"
                                )
                                + " • kanal frekansı ve PPM sabit",
                            )
                channel_iq = {name: follower.process(iq) for name, follower in followers.items()}
                states: list[dict] = []
                for auto_channel in automatic:
                    states.append(auto_channel.feed(channel_iq[auto_channel.channel.name]))
                for backend_tetra in tetra:
                    states.append(backend_tetra.feed(channel_iq[backend_tetra.channel.name]))
                for name, (discriminator, backend) in digital.items():
                    pcm, level = discriminator.process(channel_iq[name])
                    assert backend.importer.rf_power is not None
                    backend.importer.rf_power.observe(level, len(iq) / SAMPLE_RATE)
                    backend.feed(pcm)
                    for stream, samples, rate in getattr(backend, "audio_packets", []):
                        self.monitor.feed(
                            name, stream, samples, rate, "Çözücü ses akışı · slot doğrulanmadı"
                        )
                    states.append(
                        {
                            **backend.importer.rf_power.latest,
                            "name": name,
                            "level": round(level, 1),
                            "active": False,
                            "completed": backend.completed,
                            "mode": backend.channel.mode,
                            "data": backend.importer.last_metadata,
                            "offset_hz": round(discriminator.offset_hz),
                        }
                    )
                for demod, recorder in zip(demodulators, recorders, strict=True):
                    audio, level = demod.process(channel_iq[recorder.channel.name])
                    recorder.feed(
                        audio if demod.tone.open else audio * 0,
                        level if demod.tone.open else -120,
                        rf_level=level,
                    )
                    if demod.tone.open and level >= recorder.channel.squelch_db:
                        self.monitor.feed(
                            recorder.channel.name, "analog", audio, 16000, "Analog ses"
                        )
                    states.append(
                        {
                            **(recorder.rf_power.latest if recorder.rf_power is not None else {}),
                            "name": recorder.channel.name,
                            "level": round(level, 1),
                            "active": recorder.active,
                            "completed": recorder.completed,
                            "data": demod.tone.label,
                            "mode": "NFM",
                        }
                    )
                if update_due:
                    for state in states:
                        state.update(self.monitor.state(state["name"]))
                        state.update(measurements[state["name"]])
                        state.update(followers[state["name"]].telemetry())
                    self.publish("levels", channels=states)
                    last_update = time.monotonic()
                if gate is not None:
                    was_held = gate.held
                    if isinstance(gate, AutoScanGate):
                        move_on = gate.advance_auto(states[0], len(iq) / SAMPLE_RATE)
                    elif isinstance(gate, TetraScanGate):
                        state = states[0]
                        move_on = gate.advance_tetra(
                            state["level"],
                            len(iq) / SAMPLE_RATE,
                            state.get("voice", False),
                            state.get("control_channel", False),
                        )
                        if move_on and gate.reason:
                            self.archive.event(
                                "INFO", f"{channels[0].name}: {gate.reason}; tarama devam ediyor"
                            )
                            self.publish(
                                "status", text=f"{channels[0].name} • {gate.reason} • Sonraki kanal"
                            )
                    elif isinstance(gate, DmrScanGate):
                        backend = digital[channels[0].name][1]
                        journal = backend.journal
                        cc = journal.cc if time.monotonic() - journal.sync_time < 0.8 else None
                        move_on = gate.advance_dmr(states[0]["level"], len(iq) / SAMPLE_RATE, cc)
                    else:
                        move_on = gate.advance(states[0]["level"], len(iq) / SAMPLE_RATE)
                    if gate.held and not was_held:
                        if isinstance(gate, DmrScanGate):
                            digital[channels[0].name][1].importer.channel = replace(
                                channels[0], color_code=gate.color_code
                            )
                        self.publish(
                            "status",
                            text=f"KANALDA BEKLİYOR • {channels[0].name} • Eşik {gate.threshold:g} dBFS"
                            + (
                                f" • DMR CC {gate.color_code} kilitlendi"
                                if isinstance(gate, DmrScanGate)
                                else ""
                            ),
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
            for auto_channel in automatic:
                try:
                    auto_channel.close(reason)
                except Exception as exc:
                    reason = "error"
                    self.publish("error", text=str(exc))
            for backend_tetra in tetra:
                try:
                    backend_tetra.close()
                except Exception as exc:
                    reason = "error"
                    self.publish("error", text=f"TETRA kapanış hatası: {exc}")
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
