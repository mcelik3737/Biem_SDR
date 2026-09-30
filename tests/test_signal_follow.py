from dataclasses import replace

import numpy as np
import pytest
from scipy import signal

from biem_radia.dmr import DmrDiscriminator
from biem_radia.models import SAMPLE_RATE, Channel, center_for
from biem_radia.signal_follow import SignalFollower, candidates
from biem_radia.signal_peak import PeakMonitor


def fsk(channel, center, offset, samples=196608):
    rng = np.random.default_rng(17)
    hz = np.repeat(rng.choice([-1944, -648, 648, 1944], samples // 200 + 1), 200)[:samples]
    phase = np.cumsum(hz + channel.frequency_hz - center + offset) * (2 * np.pi / SAMPLE_RATE)
    return (0.15 * np.exp(1j * phase)).astype(np.complex64)


def spectrum(channels, center, iq):
    monitor = PeakMonitor(channels, center)
    monitor.feed(iq)
    monitor.measure()
    assert monitor.power is not None
    return monitor.axis, monitor.power


@pytest.mark.parametrize("offset", [-6200, -5500, -2000, 0, 2000, 5500, 6200])
def test_four_fsk_lock_shifts_decoding_to_nominal_without_changing_channel(offset):
    channel = Channel("DMR", 424000000, mode="DMR")
    center = center_for([channel])
    iq = fsk(channel, center, offset)
    axis, power = spectrum([channel], center, iq)
    follower = SignalFollower(channel, [channel])
    follower.observe(axis, power, 0)
    assert follower.offset is None
    follower.observe(axis, power, 0.2)
    assert follower.offset == pytest.approx(offset, abs=250)
    assert follower.telemetry()["follow_state"] == "locked"
    corrected = follower.process(iq)
    demod = DmrDiscriminator(channel, center)
    demod.process(corrected)
    assert abs(demod.offset_hz) < 250
    assert channel.frequency_hz == 424000000
    np.testing.assert_allclose(iq, fsk(channel, center, offset))


def cw(channel, center, offset, amplitude=0.1, samples=196608):
    return amplitude * np.exp(
        2j * np.pi * (channel.frequency_hz - center + offset) * np.arange(samples) / SAMPLE_RATE
    )


def test_stronger_neighbour_does_not_steal_an_active_lock_and_loss_releases_it():
    channel = Channel("Test", 424000000)
    center = center_for([channel])
    follower = SignalFollower(channel, [channel])
    axis, power = spectrum([channel], center, cw(channel, center, -5000))
    for now in (0, 0.2):
        follower.observe(axis, power, now)
    assert follower.offset == pytest.approx(-5000, abs=5)
    _, two_signals = spectrum(
        [channel], center, cw(channel, center, -5000) + cw(channel, center, 5000, amplitude=0.7)
    )
    follower.observe(axis, two_signals, 0.4)
    assert follower.offset == pytest.approx(-5000, abs=5)
    follower.observe(axis, None, 0.6)
    assert follower.telemetry()["follow_state"] == "holding"
    follower.observe(axis, np.zeros_like(power), 1.3)
    assert follower.offset is None and follower.telemetry()["follow_state"] == "searching"


@pytest.mark.parametrize("offset", [-12500, -7000, 7000, 12500])
def test_outside_range_is_not_acquired(offset):
    channel = Channel("Test", 424000000)
    center = center_for([channel])
    follower = SignalFollower(channel, [channel])
    axis, power = spectrum([channel], center, cw(channel, center, offset))
    for now in (0, 0.2, 0.4):
        follower.observe(axis, power, now)
    assert follower.offset is None


def test_noise_neighbour_ownership_and_disabled_mode():
    channel = Channel("A", 424000000)
    other = Channel("B", 424012500)
    center = center_for([channel, other])
    iq = cw(channel, center, 6400)  # nearer to B than A
    axis, power = spectrum([channel, other], center, iq)
    follower = SignalFollower(channel, [channel, other])
    follower.observe(axis, power, 0)
    follower.observe(axis, power, 0.2)
    assert follower.offset is None
    disabled = SignalFollower(replace(channel, follow_signal=False), [channel])
    for now in (0, 0.2):
        disabled.observe(axis, power, now)
    assert disabled.process(iq) is iq and disabled.telemetry()["follow_state"] == "disabled"
    rng = np.random.default_rng(18)
    noise = 0.05 * (rng.normal(size=len(iq)) + 1j * rng.normal(size=len(iq)))
    axis, power = spectrum([channel], center, noise)
    assert not candidates(axis, power, channel)


def test_frequency_translation_is_phase_continuous_across_blocks():
    channel = Channel("A", 424000000)
    one = SignalFollower(channel, [channel])
    split = SignalFollower(channel, [channel])
    one.offset = split.offset = -5500
    iq = np.ones(5017, dtype=complex)
    expected = one.process(iq)
    actual = np.concatenate(
        [split.process(iq[:333]), split.process(iq[333:2399]), split.process(iq[2399:])]
    )
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    before = split.phase
    split.offset = 4300
    assert split.process(np.ones(1))[0] == pytest.approx(np.exp(1j * before))


@pytest.mark.parametrize("offset", [-6200, 6200])
def test_wide_qpsk_candidate_uses_modulated_band_centre(offset):
    channel = Channel("Wide", 424000000, 25000, 25000, mode="TETRA")
    center = center_for([channel])
    rng = np.random.default_rng(82)
    symbols = np.exp(1j * (rng.integers(0, 4, 4096) * np.pi / 2 + np.pi / 4))
    base = signal.resample_poly(symbols, 160, 3)[:196608] * 0.15
    iq = base * cw(channel, center, offset, amplitude=1, samples=len(base))
    axis, power = spectrum([channel], center, iq)
    result = candidates(axis, power, channel)
    assert len(result) == 1 and result[0].offset_hz == pytest.approx(offset, abs=250)


def test_initial_lock_chooses_stronger_eligible_signal():
    channel = Channel("A", 424000000)
    center = center_for([channel])
    iq = cw(channel, center, -5000) + cw(channel, center, 5000, amplitude=0.3)
    axis, power = spectrum([channel], center, iq)
    follower = SignalFollower(channel, [channel])
    for now in (0, 0.2):
        follower.observe(axis, power, now)
    assert follower.offset == pytest.approx(5000, abs=5)
