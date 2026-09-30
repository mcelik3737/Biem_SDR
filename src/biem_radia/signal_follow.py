"""Bounded per-channel RF acquisition; never retunes the shared SDR or changes PPM."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .models import SAMPLE_RATE, Channel

LOCK_RANGE_HZ = 6500
GREEN_RANGE_HZ = 2000


@dataclass(frozen=True)
class Candidate:
    offset_hz: float
    power: float


def candidates(axis: np.ndarray, power: np.ndarray, channel: Channel) -> list[Candidate]:
    """Find occupied spectral regions and their power centres, not individual FSK lobes."""
    width = 25000 if channel.mode == "AUTO" else channel.bandwidth_hz
    region = abs(axis - channel.frequency_hz) <= LOCK_RANGE_HZ + width
    indices = np.flatnonzero(region)
    if len(indices) < 32 or not np.isfinite(power).all():
        return []
    frequencies, values = axis[indices], power[indices]
    noise = max(float(np.quantile(values, 0.20)), 1e-20)
    step = float(axis[1] - axis[0])
    smooth = np.convolve(values, np.ones(9) / 9, mode="same")
    present = smooth > max(noise * 6.31, float(smooth.max()) * 0.01)
    edges = np.diff(np.r_[False, present, False].astype(int))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    regions: list[tuple[int, int]] = []
    for start, end in zip(starts, ends, strict=True):
        # Join gaps between modulation lobes, while retaining separated neighbouring carriers.
        if regions and (start - regions[-1][1]) * step <= 1500:
            regions[-1] = (regions[-1][0], int(end))
        else:
            regions.append((int(start), int(end)))
    result = []
    for start, end in regions:
        if start == 0 or end == len(values) or (end - start) * step > width * 1.5 + 1000:
            continue  # clipped/merged regions do not provide a trustworthy centre
        signal = np.maximum(values[start:end] - noise, 0)
        total = float(signal.sum())
        if (
            total <= 0
            or 10 * np.log10(total) < channel.squelch_db
            or float(values[start:end].max()) < noise * 10**1.2
        ):
            continue
        offset = float(np.sum((frequencies[start:end] - channel.frequency_hz) * signal) / total)
        if abs(offset) <= LOCK_RANGE_HZ:
            result.append(Candidate(offset, total))
    return result


class SignalFollower:
    """Acquire twice, then hold a centre for the burst; release after 0.8 s absence."""

    def __init__(self, channel: Channel, channels: list[Channel]):
        self.channel = channel
        self.neighbours = [
            c.frequency_hz for c in channels if c.frequency_hz != channel.frequency_hz
        ]
        self.offset: float | None = None
        self.pending: float | None = None
        self.pending_at = float("-inf")
        self.seen_at = float("-inf")
        self.fresh = False
        self.phase = 0.0
        self.oscillator = np.zeros(0, dtype=complex)
        self.oscillator_offset: float | None = None

    def observe(self, axis: np.ndarray, power: np.ndarray | None, now: float):
        if not self.channel.follow_signal:
            return
        available = (
            []
            if power is None
            else [
                c
                for c in candidates(axis, power, self.channel)
                if all(
                    abs(self.channel.frequency_hz + c.offset_hz - f) >= abs(c.offset_hz)
                    for f in self.neighbours
                )
            ]
        )
        self.fresh = False
        if self.offset is not None:
            # Do not jump to a newly stronger neighbour while the selected signal remains.
            self.fresh = any(abs(c.offset_hz - self.offset) <= 1500 for c in available)
            if self.fresh:
                self.seen_at = now
            if now - self.seen_at < 0.8:
                return
            self.offset = self.pending = None
        if not available:
            self.pending = None
            return
        strongest = max(available, key=lambda c: c.power)
        if (
            self.pending is not None
            and now - self.pending_at <= 0.5
            and abs(strongest.offset_hz - self.pending) <= 750
        ):
            self.offset = float(round((self.pending + strongest.offset_hz) / 2))
            self.seen_at = now
            self.fresh = True
            self.pending = None
        else:
            self.pending = strongest.offset_hz
            self.pending_at = now

    def process(self, iq: np.ndarray) -> np.ndarray:
        offset = self.offset or 0.0
        if offset == 0 and self.phase == 0:
            return iq
        step = -2 * np.pi * offset / SAMPLE_RATE
        if self.oscillator_offset != offset or len(self.oscillator) != len(iq):
            self.oscillator = np.exp(1j * np.arange(len(iq)) * step)
            self.oscillator_offset = offset
        rotation = np.exp(1j * self.phase)
        self.phase = float((self.phase + len(iq) * step) % (2 * np.pi))
        return iq * (rotation * self.oscillator)

    def telemetry(self) -> dict:
        state = (
            "disabled"
            if not self.channel.follow_signal
            else "searching"
            if self.offset is None
            else "locked"
            if self.fresh
            else "holding"
        )
        return {
            "follow_state": state,
            "locked_hz": None if self.offset is None else self.channel.frequency_hz + self.offset,
            "lock_offset_hz": self.offset,
        }
