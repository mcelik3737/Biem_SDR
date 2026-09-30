import numpy as np
import pytest

from biem_radia.models import SAMPLE_RATE, Channel, center_for
from biem_radia.signal_peak import PeakMonitor


def tone(frequency, center, length=65536, amplitude=0.1):
    return amplitude * np.exp(2j * np.pi * (frequency - center) * np.arange(length) / SAMPLE_RATE)


@pytest.mark.parametrize("offset", [-4500, 0, 4500])
def test_signed_peak_readout_does_not_change_iq_or_channel(offset):
    channel = Channel("Test", 427550000, mode="DMR")
    center = center_for([channel])
    monitor = PeakMonitor([channel], center)
    iq = tone(channel.frequency_hz + offset, center)
    original = iq.copy()
    monitor.feed(iq)
    result = monitor.measure()[channel.name]
    assert result["peak_hz"] == pytest.approx(channel.frequency_hz + offset, abs=3)
    assert result["peak_offset_hz"] == pytest.approx(offset, abs=3)
    assert channel.frequency_hz == 427550000
    np.testing.assert_array_equal(iq, original)
    assert monitor.measure()[channel.name]["peak_hz"] is None


def test_channel_local_peak_ignores_stronger_neighbour_and_noise():
    channels = [Channel("A", 427550000), Channel("B", 427575000)]
    center = center_for(channels)
    monitor = PeakMonitor(channels, center)
    monitor.feed(tone(427551500, center, amplitude=0.01) + tone(427573000, center, amplitude=0.8))
    result = monitor.measure()
    assert result["A"]["peak_offset_hz"] == pytest.approx(1500, abs=3)
    assert result["B"]["peak_offset_hz"] == pytest.approx(-2000, abs=3)
    rng = np.random.default_rng(721)
    noise = 0.05 * (rng.normal(size=65536) + 1j * rng.normal(size=65536))
    monitor.feed(noise)
    assert all(item["peak_hz"] is None for item in monitor.measure().values())
    monitor.feed(tone(427573000, center))
    assert monitor.measure()["A"]["peak_hz"] is None


def test_weak_short_invalid_and_silent_input_have_no_peak():
    channel = Channel("Test", 427550000)
    center = center_for([channel])
    for iq in (
        tone(channel.frequency_hz, center, amplitude=1e-4),
        np.zeros(65536),
        np.full(65536, np.nan),
        np.ones(100),
    ):
        monitor = PeakMonitor([channel], center)
        monitor.feed(iq)
        assert monitor.measure()[channel.name]["peak_hz"] is None


def test_tdma_burst_observation_and_auto_bandwidth():
    channel = Channel("Auto", 427550000, mode="AUTO")
    center = center_for([channel])
    monitor = PeakMonitor([channel], center)
    # A burst followed by idle samples still belongs to the same short observation.
    monitor.feed(tone(427559000, center, length=16384))
    monitor.feed(np.zeros(16384))
    assert monitor.measure()[channel.name]["peak_offset_hz"] == pytest.approx(9000, abs=3)
    monitor.feed(np.zeros(32768))
    assert monitor.measure()[channel.name]["peak_hz"] is None
    for _ in range(40):
        monitor.feed(np.zeros(16384))
    assert monitor.samples <= monitor.capacity
    assert sum(map(len, monitor.blocks)) == monitor.samples
