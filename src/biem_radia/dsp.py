from __future__ import annotations

import numpy as np
from scipy import signal

from .models import SAMPLE_RATE, Channel


class FMDemodulator:
    """Stateful complex channel filter, FM discriminator and voice-band audio filter."""

    def __init__(self, channel: Channel, center_hz: int):
        self.channel = channel
        self.offset = channel.frequency_hz - center_hz
        self.position = 0
        self.if_position = 0
        self.previous = 0j
        self.rf_sos = np.asarray(
            signal.butter(8, channel.bandwidth_hz / 2, fs=SAMPLE_RATE, output="sos")
        )
        self.rf_state = np.zeros((len(self.rf_sos), 2), dtype=np.complex128)
        high = min(3000, channel.bandwidth_hz * 0.32)
        self.audio_sos = np.asarray(
            signal.butter(5, [250, high], btype="bandpass", fs=48_000, output="sos")
        )
        self.audio_state = np.zeros((len(self.audio_sos), 2))

    def process(self, iq: np.ndarray) -> tuple[np.ndarray, float]:
        n = np.arange(len(iq), dtype=np.float64) + self.position
        mixed = iq * np.exp(-2j * np.pi * self.offset / SAMPLE_RATE * (n % SAMPLE_RATE))
        filtered, self.rf_state = signal.sosfilt(self.rf_sos, mixed, zi=self.rf_state)
        narrow = filtered[(-self.position) % 20 :: 20]
        self.position += len(iq)
        if not len(narrow):
            return np.zeros(0, dtype=np.float32), -120.0
        level = float(10 * np.log10(max(float(np.mean(np.abs(narrow) ** 2)), 1e-12)))
        previous = np.concatenate(([self.previous], narrow[:-1]))
        fm = np.angle(narrow * np.conj(previous))
        self.previous = narrow[-1]
        deviation = 5000 if self.channel.spacing_hz == 25000 else 2500
        audio, self.audio_state = signal.sosfilt(
            self.audio_sos, fm * (48_000 / (2 * np.pi * deviation)), zi=self.audio_state
        )
        result = audio[(-self.if_position) % 3 :: 3]
        self.if_position += len(narrow)
        return np.clip(result * 0.75, -1, 1).astype(np.float32), level
