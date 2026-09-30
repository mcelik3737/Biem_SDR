import tkinter as tk
from types import SimpleNamespace

import numpy as np
import pytest

from biem_radia.app import RadiaApp
from biem_radia.spectrum_plot import display_limits, prominent_peaks


def test_peak_threshold_and_scale_validation():
    values = np.full(900, -80.0)
    values[100], values[500], values[800] = -45, -25, -65
    assert prominent_peaks(values, -50) == [500, 100]
    assert display_limits(-25, 50) == (-75, -25)
    with pytest.raises(ValueError):
        display_limits(float("nan"), 50)
    with pytest.raises(ValueError):
        display_limits(-25, 0)


def test_marker_hold_waterfall_redraw_and_rf_change_reset(tmp_path):
    root = tk.Tk()
    root.withdraw()
    app = RadiaApp(root, tmp_path)
    p = app.spectrum
    try:
        values = np.full(900, -80.0)
        values[450] = -30
        first = {"values": values, "low": 420e6, "high": 421e6, "settings": (29, False, 15)}
        p.draw(first)
        left, right, _, _ = p.plot_bounds
        p.pointer(SimpleNamespace(x=left + 450 * (right - left) / 899), lock=True)
        locked = p.locked_hz
        assert "-30.0 dBFS" in p.marker.get()
        assert "bilinmiyor" in p.marker.get()
        p.zoom.set(4)
        p.redraw()
        low, high = p.visible_band()
        assert high - low == pytest.approx(250000, abs=2300)
        assert p.locked_hz == locked and "-30.0 dBFS" in p.marker.get()
        assert len(p.rows) == 1
        p.pan.set(100)
        p.redraw()
        assert p.visible_band()[1] == 421e6
        p.pan.set(0)
        p.redraw()
        assert p.visible_band()[0] == 420e6
        p.threshold.set(-35)
        p.full_band()
        assert p.visible_band() == (420e6, 421e6)
        assert "+5.0 dB" in p.marker.get()
        p.redraw()
        assert len(p.rows) == 1  # Mouse/resize/scale does not manufacture history.
        p.draw({**first, "values": values - 10})
        assert p.locked_hz == locked and p.maximum[450] == -30
        assert "-40.0 dBFS" in p.marker.get()
        p.auto_scale()
        assert float(p.reference.get()) > -40
        p.reset_peaks()
        assert p.maximum[450] == -40
        p.draw({**first, "settings": (19, False, 15)})
        assert len(p.rows) == 1
        assert p.photo.width() == int(right - left) + 1
        p.zoom_marker()
        assert float(p.high.get()) - float(p.low.get()) == pytest.approx(0.25)
        p.unlock()
        assert p.locked_hz is None
    finally:
        for token in root.tk.splitlist(root.tk.call("after", "info")):
            root.after_cancel(token)
        root.destroy()
