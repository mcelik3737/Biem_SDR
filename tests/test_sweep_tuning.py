from types import SimpleNamespace

import pytest

from biem_radia.sources import USBSource


def test_sweep_tuning_resets_after_changes_and_preserves_handle():
    actions = []
    source = USBSource.__new__(USBSource)
    source.synchronous = True
    source.closed = False
    source.handle = object()
    handle = source.handle
    source.tuning = (420250000, 15, 29, False)
    source.gains = [190, 290]
    source.library = SimpleNamespace(
        lib=SimpleNamespace(
            rtlsdr_set_freq_correction=lambda h, n: actions.append(("ppm", n)) or 0,
            rtlsdr_get_freq_correction=lambda h: 16,
            rtlsdr_set_center_freq=lambda h, n: actions.append(("freq", n)) or 0,
            rtlsdr_set_tuner_gain_mode=lambda h, n: actions.append(("mode", n)) or 0,
            rtlsdr_set_tuner_gain=lambda h, n: actions.append(("gain", n)) or 0,
            rtlsdr_reset_buffer=lambda h: actions.append(("reset", None)) or 0,
        )
    )
    assert source.tune_sweep(420750000, 16, 19, False)
    assert actions == [
        ("ppm", 16),
        ("mode", 1),
        ("gain", 190),
        ("freq", 420750000),
        ("reset", None),
    ]
    assert source.handle is handle
    actions.clear()
    assert not source.tune_sweep(420750000, 16, 19, False)
    assert actions == [("reset", None)]
    source.synchronous = False
    with pytest.raises(RuntimeError):
        source.tune_sweep(420250000, 16, 19, False)
