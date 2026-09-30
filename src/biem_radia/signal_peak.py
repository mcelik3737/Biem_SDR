"""Read-only, channel-local FFT peak telemetry. Never adjusts the receiver."""

from __future__ import annotations

from collections import deque

import numpy as np

from .models import SAMPLE_RATE, Channel


class PeakMonitor:
    SIZE = 8192

    def __init__(self, channels: list[Channel], center: int):
        self.channels = channels
        self.axis = np.fft.fftshift(np.fft.fftfreq(self.SIZE, 1 / SAMPLE_RATE)) + center
        self.window = np.hanning(self.SIZE)
        self.blocks: deque[np.ndarray] = deque()
        self.samples = 0
        self.power: np.ndarray | None = None
        self.capacity = SAMPLE_RATE // 4
        self.masks = {
            c.name: abs(self.axis - c.frequency_hz)
            <= (25000 if c.mode == "AUTO" else c.bandwidth_hz) / 2
            for c in channels
        }
        # Exclude configured channels and the tuner DC bins from the noise reference.
        background = abs(self.axis - center) > 2 * SAMPLE_RATE / self.SIZE
        for mask in self.masks.values():
            background &= ~mask
        self.references = {
            c.name: background & (abs(self.axis - c.frequency_hz) <= 50000) for c in channels
        }

    def feed(self, iq: np.ndarray):
        # Keep a short continuous observation so TDMA gaps don't erase every other readout.
        block = iq[-self.capacity :].copy()
        self.blocks.append(block)
        self.samples += len(block)
        while self.blocks and self.samples > self.capacity:
            excess = min(self.samples - self.capacity, len(self.blocks[0]))
            first = self.blocks.popleft()[excess:]
            self.samples -= excess
            if len(first):
                self.blocks.appendleft(first)

    def measure(self) -> dict[str, dict[str, float | None]]:
        self.power = None
        result: dict[str, dict[str, float | None]] = {
            c.name: {"peak_hz": None, "peak_offset_hz": None} for c in self.channels
        }
        if self.samples < self.SIZE * 2:
            return result
        iq = np.concatenate(tuple(self.blocks))
        self.blocks.clear()
        self.samples = 0
        frames = iq[: len(iq) // self.SIZE * self.SIZE].reshape(-1, self.SIZE)
        power = np.mean(
            abs(np.fft.fftshift(np.fft.fft(frames * self.window, axis=1), axes=1)) ** 2,
            axis=0,
        ) / (self.SIZE * np.sum(self.window**2))
        if not np.isfinite(power).all():
            return result
        self.power = power
        for channel in self.channels:
            indices = np.flatnonzero(self.masks[channel.name])
            reference = power[self.references[channel.name]]
            if len(indices) < 3 or len(reference) < 16:
                continue
            peak_index = int(indices[np.argmax(power[indices])])
            # A boundary maximum can be leakage from a neighbouring channel.
            if peak_index in (indices[0], indices[-1]):
                continue
            channel_db = 10 * np.log10(max(float(power[indices].sum()), 1e-20))
            noise = max(float(np.median(reference)), 1e-20)
            if channel_db < channel.squelch_db or power[peak_index] < noise * 10**1.2:
                continue
            # Sub-bin interpolation helps narrow peaks; it is not a carrier/AFC estimate.
            left, middle, right = np.log(np.maximum(power[peak_index - 1 : peak_index + 2], 1e-20))
            curvature = left - 2 * middle + right
            fraction = float(0.5 * (left - right) / curvature) if curvature < 0 else 0.0
            peak_hz = float(
                self.axis[peak_index] + np.clip(fraction, -0.5, 0.5) * SAMPLE_RATE / self.SIZE
            )
            result[channel.name] = {
                "peak_hz": peak_hz,
                "peak_offset_hz": peak_hz - channel.frequency_hz,
            }
        return result
