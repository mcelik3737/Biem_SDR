import json
import tkinter as tk
from pathlib import Path
from types import SimpleNamespace

import pytest

from biem_radia.calibration import CalibrationPanel, reference_ppm
from biem_radia.sources import USBSource


@pytest.mark.parametrize("observed,expected", [(427554500, -9), (427544500, 15), (427550000, 2)])
def test_reference_correction_sign_and_existing_ppm(observed, expected):
    target = reference_ppm(427550000, observed, 2)
    assert target == expected
    # Physical clock model: the displayed frequency scales with (1 + applied PPM).
    corrected_display = observed * (1 + target / 1e6) / (1 + 2 / 1e6)
    assert abs(corrected_display - 427550000) <= 214  # half of a 1 PPM step


@pytest.mark.parametrize(
    "reference,observed,current",
    [
        (0, 427550000, 0),
        (427550000, float("nan"), 0),
        (427550000, 420000000, 0),
        (427550000, 427550000, 201),
    ],
)
def test_invalid_calibration_is_rejected(reference, observed, current):
    with pytest.raises(ValueError):
        reference_ppm(reference, observed, current)


@pytest.mark.parametrize("requested,result,actual", [(0, -2, 0), (-9, 0, -9), (15, -2, 15)])
def test_ppm_command_readback_and_unchanged_return(requested, result, actual):
    commands = []
    source = USBSource.__new__(USBSource)
    source.handle = object()
    source.library = SimpleNamespace(
        lib=SimpleNamespace(
            rtlsdr_set_freq_correction=lambda handle, ppm: commands.append(ppm) or result,
            rtlsdr_get_freq_correction=lambda handle: actual,
        )
    )
    source.apply_ppm(requested)
    assert commands == [requested]
    source.library.lib.rtlsdr_get_freq_correction = lambda handle: 123
    with pytest.raises(RuntimeError):
        source.apply_ppm(requested)


def test_calibration_persists_without_compounding_or_touching_channels(tmp_path, monkeypatch):
    root = tk.Tk()
    root.withdraw()
    path = tmp_path / "receiver.json"
    path.write_text(json.dumps({"ppm": "2", "usb_gain": "29", "source": "USB"}), "utf-8")
    app = SimpleNamespace(
        ppm=tk.StringVar(value="2"),
        receiver_config_path=path,
        receiver=SimpleNamespace(running=False),
        radio=SimpleNamespace(running=False),
        spectrum=SimpleNamespace(worker=SimpleNamespace(running=False)),
    )
    errors = []
    monkeypatch.setattr(
        "biem_radia.calibration.messagebox.showerror", lambda *args: errors.append(args)
    )
    try:
        panel = CalibrationPanel(root, app)
        panel.observed.set("427,5545")
        panel.preview()
        assert app.ppm.get() == "2"
        panel.save()
        panel.save()  # same measured PPM, so no second correction is added
        assert app.ppm.get() == "-9"
        assert json.loads(path.read_text("utf-8")) == {
            "ppm": "-9",
            "usb_gain": "29",
            "source": "USB",
        }
        panel.observed.set("427.5445")
        app.receiver.running = True
        panel.save()
        assert errors and app.ppm.get() == "-9"
        assert panel.measurement_ppm.get() == "2"
    finally:
        root.destroy()


@pytest.mark.parametrize("ppm", [0, -9, 15])
def test_saved_ppm_is_sent_on_every_usb_open_before_streaming(monkeypatch, ppm):
    commands = []

    class Library:
        def __init__(self, path):
            self.ppm = 0
            self.lib = self
            self.callback_type = lambda callback: callback

        def devices(self):
            return ["test"]

        def rtlsdr_open(self, handle, index):
            handle._obj.value = 1
            return 0

        def rtlsdr_set_freq_correction(self, handle, value):
            commands.append(("ppm", value))
            if self.ppm == value:
                return -2
            self.ppm = value
            return 0

        def rtlsdr_get_freq_correction(self, handle):
            return self.ppm

        def rtlsdr_get_tuner_gains(self, handle, gains):
            if gains is not None:
                gains[0] = 190
            return 1

        def __getattr__(self, name):
            return lambda *args: commands.append((name, args[-1])) or 0

    monkeypatch.setattr("biem_radia.sources.RtlLibrary", Library)
    for _ in range(2):
        source = USBSource(Path("fake.dll"), 427650000, ppm=ppm, synchronous=True)
        source.close()
    assert commands.count(("ppm", ppm)) == 2
    assert next(i for i, item in enumerate(commands) if item[0] == "ppm") < next(
        i for i, item in enumerate(commands) if item[0] == "rtlsdr_reset_buffer"
    )
