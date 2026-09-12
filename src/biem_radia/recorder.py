from __future__ import annotations

import uuid
import wave
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from .models import AUDIO_RATE, Channel
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
        max_seconds: float = 180,
    ):
        self.archive, self.channel, self.source, self.epoch = archive, channel, source, epoch
        self.pre_samples = int(pre_seconds * AUDIO_RATE)
        self.hang_samples = int(hang_seconds * AUDIO_RATE)
        self.max_samples = int(max_seconds * AUDIO_RATE)
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

    @property
    def active(self) -> bool:
        return self.writer is not None

    def feed(self, audio: np.ndarray, level: float):
        if not len(audio):
            return
        threshold = self.channel.squelch_db - (3 if self.active else 0)
        opened = level >= threshold
        if not self.active and opened:
            self._start()
        if self.writer is not None:
            self._write(audio)
            self.silence = 0 if opened else self.silence + len(audio)
            if self.written >= self.max_samples:
                self.finish("max_duration")
            elif self.silence >= self.hang_samples:
                self.finish("squelch")
        else:
            self.pre.append(audio.copy())
            self.pre_count += len(audio)
            while self.pre and self.pre_count > self.pre_samples:
                excess = self.pre_count - self.pre_samples
                first = self.pre.popleft()
                if len(first) > excess:
                    self.pre.appendleft(first[excess:])
                    self.pre_count -= excess
                else:
                    self.pre_count -= len(first)
        self.total += len(audio)

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
        final = self.pending.with_suffix("")
        self.pending.rename(final)
        # If database insertion fails, retain the WAV for manual recovery.
        with self.archive.connect() as db:
            db.execute(
                """INSERT INTO calls(id,channel,frequency_hz,started_utc,duration,path,source,end_reason)
                          VALUES(?,?,?,?,?,?,?,?)""",
                (
                    self.call_id,
                    self.channel.name,
                    self.channel.frequency_hz,
                    self.started.isoformat(),
                    self.written / AUDIO_RATE,
                    str(final.relative_to(self.archive.root)),
                    self.source,
                    reason,
                ),
            )
        self.completed += 1
