from types import SimpleNamespace

from biem_radia.sources import USBSource


def test_tuner_gain_rounding_and_auto_mode_without_usb():
    commands = []
    lib = SimpleNamespace(
        rtlsdr_set_tuner_gain_mode=lambda handle, mode: commands.append(("mode", mode)) or 0,
        rtlsdr_set_tuner_gain=lambda handle, gain: commands.append(("gain", gain)) or 0,
    )
    source = USBSource.__new__(USBSource)
    source.library = SimpleNamespace(lib=lib)
    source.handle = None
    source.gains = [90, 190, 240, 290, 340]
    assert "29" in source.set_gain(28)
    assert commands == [("mode", 1), ("gain", 290)]
    assert source.set_gain(29, True) == "Tuner AGC açık"
    assert source.gain_db is None and commands[-1] == ("mode", 0)
    source.set_gain(19, False)
    assert source.gain_db == 19 and commands[-2:] == [("mode", 1), ("gain", 190)]
