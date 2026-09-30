from __future__ import annotations

import uuid
import wave
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from .filenames import available_path, recording_name
from .models import AUDIO_RATE, Channel
from .rf_power import RFPowerMeter
from .storage import Archive


class CallRecorder:
    """Carrier-triggered call segmentation; this is not speech recognition."""

    def __init__(
        self,
        archive: Archive,
        channel: Channel,
        source: str,
        epoch: datetime,
        pre_seconds: float = 0.30,
        hang_seconds: float = 0.60,
        max_seconds: float = 90,
        pause_seconds: float = 2,
    ):
        self.archive, self.channel, self.source, self.epoch = archive, channel, source, epoch
        self.pre_samples = int(pre_seconds * AUDIO_RATE)
        self.hang_samples = int(hang_seconds * AUDIO_RATE)
        self.max_samples = int(max_seconds * AUDIO_RATE)
        self.pause_samples = int(pause_seconds * AUDIO_RATE)
        self.cooldown = 0
        if self.max_samples <= 0 or self.pause_samples < 0:
            raise ValueError("Invalid recording duration or pause")
        self.pre: deque[np.ndarray] = deque()
        self.pre_count = 0
        self.total = 0
        self.written = 0
        self.silence = 0
        self.writer: wave.Wave_write | None = None
        self.pending: Path | None = None
        self.call_id = ""
        self.started = epoch
        self.completed = 0
        self.rf_power: RFPowerMeter | None = None

    @property
    def active(self) -> bool:
        return self.writer is not None

    def feed(self, audio: np.ndarray, level: float, *, rf_level: float | None = None):
        if not len(audio):
            return
        if self.rf_power is not None:
            self.rf_power.observe(
                level if rf_level is None else rf_level,
                len(audio) / AUDIO_RATE,
                end=self.epoch.timestamp() + (self.total + len(audio)) / AUDIO_RATE,
            )
        while len(audio):
            if self.cooldown:
                skipped = min(len(audio), self.cooldown)
                self.cooldown -= skipped
                self.total += skipped
                audio = audio[skipped:]
                continue
            threshold = self.channel.squelch_db - (3 if self.active else 0)
            opened = level >= threshold
            if not self.active and opened:
                self._start()
            if self.writer is not None:
                count = min(len(audio), self.max_samples - self.written)
                self._write(audio[:count])
                self.total += count
                audio = audio[count:]
                self.silence = 0 if opened else self.silence + count
                if self.written >= self.max_samples:
                    self.finish("max_duration")
                    self.cooldown = self.pause_samples
                    self.pre.clear()
                    self.pre_count = 0
                elif self.silence >= self.hang_samples:
                    self.finish("squelch")
            else:
                self.pre.append(audio.copy())
                self.pre_count += len(audio)
                limit = min(self.pre_samples, self.max_samples)
                while self.pre and self.pre_count > limit:
                    excess = self.pre_count - limit
                    first = self.pre.popleft()
                    if len(first) > excess:
                        self.pre.appendleft(first[excess:])
                        self.pre_count -= excess
                    else:
                        self.pre_count -= len(first)
                self.total += len(audio)
                break

    def _start(self):
        self.started = self.epoch + timedelta(seconds=(self.total - self.pre_count) / AUDIO_RATE)
        self.call_id = uuid.uuid4().hex
        directory = (
            self.archive.root / "recordings" / self.started.astimezone().strftime("%Y-%m-%d")
        )
        directory.mkdir(parents=True, exist_ok=True)
        self.pending = directory / f"{self.started.strftime('%H%M%S')}_{self.call_id}.wav.part"
        self.writer = wave.open(str(self.pending), "wb")
        self.writer.setparams((1, 2, AUDIO_RATE, 0, "NONE", "not compressed"))
        self.written = self.silence = 0
        for chunk in self.pre:
            self._write(chunk)
        self.pre.clear()
        self.pre_count = 0

    def _write(self, audio: np.ndarray):
        assert self.writer is not None
        pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
        self.writer.writeframes(pcm)
        self.written += len(audio)

    def finish(self, reason: str):
        if self.writer is None:
            return
        self.writer.close()
        self.writer = None
        assert self.pending is not None
        power = (
            self.rf_power.summary(
                self.started.timestamp(), self.started.timestamp() + self.written / AUDIO_RATE
            )
            if self.rf_power is not None
            else {}
        )
        final = available_path(
            self.pending.parent,
            recording_name("NFM", self.started, self.written / AUDIO_RATE, power=power),
        )
        self.pending.rename(final)
        final = self.archive.protect_file(final)
        # If database insertion fails, retain the WAV for manual recovery.
        with self.archive.connect() as db:
            db.execute(
                """INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason,rf_peak_dbfs,rf_peak_dbm,rf_power_info)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    self.call_id,
                    self.channel.name,
                    self.channel.frequency_hz,
                    self.started.isoformat(),
                    self.written / AUDIO_RATE,
                    str(final.relative_to(self.archive.root)),
                    self.source,
                    reason,
                    power.get("rf_peak_dbfs"),
                    power.get("rf_peak_dbm"),
                    power.get("rf_power_info"),
                ),
            )
        self.completed += 1
