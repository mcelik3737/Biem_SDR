from __future__ import annotations

import base64
import json
import queue
import subprocess
import threading
import time
import uuid
import wave
from collections.abc import Callable
from datetime import datetime, timezone

import numpy as np
from scipy import signal

from .filenames import available_path, recording_name
from .models import SAMPLE_RATE
from .rf_power import RFPowerMeter


class TetraBackend:
    """Local x86 TETRA decoder, isolated from the receiver and SDR# process."""

    def __init__(self, archive, channel, center, project=None):
        self.archive, self.channel = archive, channel
        self.position = 0
        self.offset = channel.frequency_hz - center
        self.sos = np.asarray(signal.butter(8, 12500, fs=SAMPLE_RATE, output="sos"))
        self.state = np.zeros((len(self.sos), 2), dtype=np.complex128)
        self.completed = 0
        self.rf_power: RFPowerMeter | None = None
        self.data = "TETRA • senkron bekleniyor • RF doğrulaması gerekli"
        self.events: queue.Queue = queue.Queue(maxsize=300)
        self.directory = archive.root / "tetra-sessions" / uuid.uuid4().hex
        self.directory.mkdir(parents=True)
        self.log = (self.directory / "bridge.log").open("wb")
        self.calls: dict = {}
        self.clear: dict = {}
        self.cc = None
        self.observer: Callable[[dict], None] | None = None
        self.recording_check: Callable[[], bool] | None = None
        self.cooldowns: dict[int, float] = {}
        self.last_voice = float("-inf")
        self.audio_sink = None
        self.control_signature = None
        self.control_confirmations = 0
        exe = (project or archive.root.parent) / "vendor/tetra/TetraBridge.exe"
        if not exe.exists():
            self.log.close()
            raise ValueError("TETRA için Setup-TETRA.ps1 çalıştırılmalı.")
        self.process = subprocess.Popen(
            [str(exe)],
            cwd=exe.parent,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.log,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()
        try:
            ready = self.events.get(timeout=10)
            if not ready.get("ready"):
                raise RuntimeError("TETRA yardımcı süreç hazır değil.")
        except Exception:
            self.close()
            raise

    def _read(self):
        assert self.process.stdout is not None
        try:
            for line in self.process.stdout:
                self.events.put(json.loads(line), timeout=1)
        except Exception as exc:
            try:
                self.events.put_nowait({"error": str(exc)})
            except queue.Full:
                pass

    def _event(self, e):
        if e.get("error"):
            raise RuntimeError(e["error"])
        observer = getattr(self, "observer", None)
        if observer is not None:
            observer(e)
        now = time.monotonic()
        sync = e.get("sync", {})
        if "ColorCode" in sync and not e.get("errors"):
            self.cc = sync["ColorCode"]
        fields = e.get("data", [])
        self.data = f"TETRA {e.get('mode', '')} • CC {self.cc if self.cc is not None else '—'} • BER {e.get('ber', 0):.1f}%"
        for item in fields:
            slot = item.get("CurrTimeSlot", item.get("TimeSlot"))
            if slot in (1, 2, 3, 4) and "Encryption_mode" in item and not e.get("errors"):
                self.clear[slot] = (item["Encryption_mode"] == 0, now)
            if item:
                self.data += " • " + ", ".join(f"{k}={v}" for k, v in list(item.items())[:5])
        # MAC broadcast system information, repeated and matching this carrier.
        # Color code alone says nothing about whether this is a control carrier.
        if not e.get("errors"):
            for item in fields:
                if (
                    item.get("MAC_PDU_Type") == 2
                    and item.get("MAC_Broadcast_Type") == 0
                    and all(k in item for k in ("Main_Carrier", "Frequency_Band", "Offset"))
                ):
                    band, carrier, offset = (
                        item["Frequency_Band"],
                        item["Main_Carrier"],
                        item["Offset"],
                    )
                    if 0 <= band <= 15 and 0 <= carrier <= 4095 and offset in range(4):
                        frequency = (
                            band * 100000000 + carrier * 25000 + (0, 6250, -6250, 12500)[offset]
                        )
                        signature = (frequency, self.cc)
                        if frequency == self.channel.frequency_hz and self.cc is not None:
                            self.control_confirmations = (
                                self.control_confirmations + 1
                                if signature == self.control_signature
                                else 1
                            )
                            self.control_signature = signature
        slot = e.get("slot", 0)
        permitted, last = self.clear.get(slot, (False, 0))
        cc_ok = self.channel.color_code is None or self.channel.color_code == self.cc
        recording_check = getattr(self, "recording_check", None)
        # Never identify a voice burst using a previous unassociated SSI/GSSI.
        if (
            slot in (1, 2, 3, 4)
            and e.get("pcm")
            and permitted
            and now - last < 2
            and cc_ok
            and not e.get("errors")
            and (recording_check is None or recording_check())
        ):
            pcm = base64.b64decode(e["pcm"], validate=True)
            if len(pcm) != 960:
                raise ValueError("TETRA PCM frame size changed.")
            self.last_voice = now
            sink = getattr(self, "audio_sink", None)
            if sink is not None:
                sink(slot, np.frombuffer(pcm, "<i2") / 32768.0)
            if now >= self.cooldowns.get(slot, 0):
                call = self.calls.setdefault(
                    slot, {"started": datetime.now(timezone.utc), "chunks": [], "last": now}
                )
                call["chunks"].append(pcm)
                call["last"] = now
                call["last_utc"] = time.time()
                if len(call["chunks"]) >= 1500:  # 1500 * 60 ms = exactly 90 seconds.
                    self._finish(slot, "max_duration")
                    self.cooldowns[slot] = now + 2
        elif slot:
            self.data += " • Ses: açık çağrı bilgisi bekleniyor"
        with (self.directory / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "observed_utc": datetime.now(timezone.utc).isoformat(),
                        "channel": self.channel.name,
                        "frequency_hz": self.channel.frequency_hz,
                        **{k: v for k, v in e.items() if k != "pcm"},
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    def feed(self, iq):
        if self.process.poll() is not None:
            raise RuntimeError(f"TETRA çözücüsü kapandı: {self.directory}")
        n = np.arange(len(iq)) + self.position
        mixed = iq * np.exp(-2j * np.pi * self.offset / SAMPLE_RATE * (n % SAMPLE_RATE))
        filtered, self.state = signal.sosfilt(self.sos, mixed, zi=self.state)
        narrow = filtered[(-self.position) % 10 :: 10]
        self.position += len(iq)
        level = (
            float(10 * np.log10(max(float(np.mean(abs(narrow) ** 2)), 1e-12)))
            if len(narrow)
            else -120
        )
        meter = getattr(self, "rf_power", None)
        if meter is not None:
            meter.observe(level, len(iq) / SAMPLE_RATE)
        assert self.process.stdin is not None
        self.process.stdin.write(narrow.astype("<c8").tobytes())
        self.process.stdin.flush()
        while not self.events.empty():
            self._event(self.events.get_nowait())
        for slot in list(self.calls):
            call = self.calls[slot]
            if time.monotonic() - call["last"] > 0.8:
                self._finish(slot)
        return {
            **(meter.latest if meter is not None else {}),
            "name": self.channel.name,
            "level": round(level, 1),
            "active": bool(self.calls),
            "completed": self.completed,
            "mode": "TETRA",
            "data": self.data,
            "voice": time.monotonic() - self.last_voice < 0.8,
            "control_channel": self.control_confirmations >= 3,
        }

    def _finish(self, slot, reason="voice_gap"):
        call = self.calls.pop(slot)
        pcm = b"".join(call["chunks"])
        if not pcm or not np.any(np.frombuffer(pcm, dtype="<i2")):
            return
        started = call["started"]
        duration = len(pcm) / 16000
        directory = self.archive.root / "recordings" / started.astimezone().strftime("%Y-%m-%d")
        directory.mkdir(parents=True, exist_ok=True)
        meter = getattr(self, "rf_power", None)
        power = (
            meter.summary(
                started.timestamp() - 0.06,
                call.get("last_utc", started.timestamp() + duration),
                timing="host_audio_window",
            )
            if meter is not None
            else {}
        )
        path = available_path(directory, recording_name("TETRA", started, duration, power=power))
        with wave.open(str(path), "wb") as wav:
            wav.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
            wav.writeframes(pcm)
        path = self.archive.protect_file(path)
        with self.archive.connect() as db:
            db.execute(
                "INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason,system,color_code,protocol_slot,timing_basis,rf_peak_dbfs,rf_peak_dbm,rf_power_info) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex,
                    self.channel.name,
                    self.channel.frequency_hz,
                    started.isoformat(),
                    duration,
                    str(path.relative_to(self.archive.root)),
                    "TETRA/local",
                    reason,
                    self.channel.system,
                    self.cc,
                    slot,
                    "host_first_audio",
                    power.get("rf_peak_dbfs"),
                    power.get("rf_peak_dbm"),
                    power.get("rf_power_info"),
                ),
            )
        self.completed += 1

    def close(self):
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=3)
        self.thread.join(timeout=2)
        while not self.events.empty():
            self._event(self.events.get_nowait())
        for slot in list(self.calls):
            self._finish(slot)
        if self.process.stdout is not None:
            self.process.stdout.close()
        self.log.close()
