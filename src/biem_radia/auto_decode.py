"""Parallel decoder probes for a fixed channel; no AFC or trunk following."""

import json
import time
from dataclasses import replace
from datetime import datetime, timezone

from .detection import AnalogEvidence, ProtocolEvidence
from .dmr import DmrBackend, DmrDiscriminator
from .dsp import FMDemodulator
from .recorder import CallRecorder
from .tetra import TetraBackend


class AutoChannel:
    def __init__(self, archive, channel, center, source_kind, epoch, project=None):
        self.channel, self.archive = channel, archive
        self.evidence = ProtocolEvidence()
        self.analog_evidence = AnalogEvidence()
        self.mode = None
        self.monitor = None
        self.last_label = None
        self.dmr = None
        self.tetra = None
        self.recorder = None
        self.log = None
        analog = replace(channel, mode="NFM", color_code=None)
        dmr = replace(channel, mode="DMR", spacing_hz=12500, bandwidth_hz=12500, color_code=None)
        tetra = replace(
            channel, mode="TETRA", spacing_hz=25000, bandwidth_hz=25000, color_code=None
        )
        self.discriminator = DmrDiscriminator(dmr, center)
        self.fm = FMDemodulator(analog, center)
        try:
            # Fail explicitly if either dependency is missing; silently using
            # analog fallback when a digital probe cannot run is unsafe.
            self.dmr = DmrBackend(archive, dmr, project or archive.root.parent)
            self.tetra = TetraBackend(archive, tetra, center, project=project)
            self.dmr.journal.observer = self.evidence.observe_dmr
            self.dmr.importer.recording_check = lambda: (
                "DMR" in self.evidence.confirmed and self.evidence.digital_mode() != "CONFLICT"
            )
            self.tetra.observer = self.evidence.observe_tetra
            self.tetra.recording_check = lambda: self.evidence.digital_mode() == "TETRA"
            self.recorder = CallRecorder(
                archive, analog, source_kind + "/AUTO-NFM", epoch, pre_seconds=2.5
            )
            directory = self.dmr.directory
            self.log = (directory / "auto-detection.jsonl").open("a", encoding="utf-8")
        except Exception:
            self.close("error")
            raise

    def feed(self, iq):
        assert self.dmr is not None and self.tetra is not None and self.recorder is not None
        pcm, level = self.discriminator.process(iq)
        self.dmr.feed(pcm)
        tetra_state = self.tetra.feed(iq)
        audio, analog_level = self.fm.process(iq)
        digital = self.evidence.digital_mode()
        above = max(level, tetra_state["level"]) >= self.channel.squelch_db
        analog_ok = self.analog_evidence.feed(
            self.discriminator.last_hz,
            analog_level >= self.channel.squelch_db
            and digital is None
            and time.monotonic() - self.evidence.last_digital > 3,
        )
        selected = digital if above else None
        if selected is None and analog_ok:
            selected = "NFM"
        # Never append digital discriminator noise to an existing analog call.
        if digital is not None:
            self.recorder.finish("digital_detected")
            self.recorder.pre.clear()
            self.recorder.pre_count = 0
        allowed_analog = selected == "NFM"
        # Keep only positive analog candidate samples for the acquisition pre-roll.
        candidate = self.analog_evidence.qualified_seconds > 0
        self.recorder.feed(
            audio if candidate else audio * 0,
            analog_level if allowed_analog else -120,
        )
        self.mode = selected
        if self.monitor is not None:
            if selected == "DMR":
                for stream, samples, rate in getattr(self.dmr, "audio_packets", []):
                    self.monitor.feed(
                        self.channel.name,
                        stream,
                        samples,
                        rate,
                        "DMR ses akışı · slot doğrulanmadı",
                    )
            elif selected == "NFM" and above:
                self.monitor.feed(self.channel.name, "analog", audio, 16000, "Analog ses")
        label = self.evidence.label(selected)
        if label != self.last_label:
            event = {
                "observed_utc": datetime.now(timezone.utc).isoformat(),
                "channel": self.channel.name,
                "frequency_hz": self.channel.frequency_hz,
                "mode": selected,
                "label": label,
                "tuning_changed": False,
            }
            assert self.log is not None
            self.log.write(json.dumps(event, ensure_ascii=False) + "\n")
            self.log.flush()
            self.archive.event("INFO", f"AUTO • {self.channel.name} • {label}")
            self.last_label = label
        details = (
            self.dmr.importer.last_metadata
            if selected == "DMR"
            else tetra_state["data"]
            if selected == "TETRA"
            else "FM ses ölçütleri sağlandı; tür olası"
            if selected == "NFM"
            else "Tür doğrulanmadı; analog kayıt açılmadı"
        )
        return {
            "name": self.channel.name,
            "level": round(max(level, tetra_state["level"]), 1),
            "active": self.recorder.active or tetra_state["active"],
            "completed": self.recorder.completed + self.dmr.completed + self.tetra.completed,
            "mode": "AUTO",
            "detected_mode": selected,
            "data": f"OTOMATİK • {label} • {details}",
            "voice": tetra_state["voice"] if selected == "TETRA" else self.recorder.active,
            "control_channel": selected == "TETRA" and tetra_state["control_channel"],
        }

    def close(self, reason="stopped"):
        errors = []
        for backend in (self.dmr, self.tetra):
            if backend is not None:
                try:
                    backend.close()
                except Exception as exc:
                    errors.append(exc)
        if self.recorder is not None:
            try:
                self.recorder.finish(reason)
            except Exception as exc:
                errors.append(exc)
        if self.log is not None:
            self.log.close()
        if errors:
            raise RuntimeError(f"Otomatik çözücü kapanış hatası: {errors[0]}")
