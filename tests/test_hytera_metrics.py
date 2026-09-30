import json
import struct
import tkinter as tk
from tkinter import ttk

import pytest

from biem_radia.hytera_metrics import DATA_BASE, decode_measurement, measurement_cell
from biem_radia.hytera_snmp import SnmpMessage, SnmpMonitor
from biem_radia.repeater_settings import RepeaterSettingsPanel


def raw_float(value):
    return "hex:" + struct.pack("<f", value).hex()


def test_captured_voltage_and_temperature_and_valid_negative_temperature():
    volts = decode_measurement(1, 4, "hex:00c55f41")
    assert volts.value == pytest.approx(13.9855957) and volts.text == "13.99 V"
    assert decode_measurement(2, 4, "hex:0000e041").text == "28.0 °C"
    assert decode_measurement(2, 4, raw_float(-1)).text == "-1.0 °C"
    assert decode_measurement(2, 4, raw_float(0)).text == "0.0 °C"
    assert decode_measurement(4, 4, raw_float(1.2)).text == "1.20:1"


@pytest.mark.parametrize(
    "raw",
    [
        "hex:000080bf",
        "hex:00000000",
        "hex:0000c07f",
        "hex:0000807f",
        "hex:00000001",
        "hex:415fc500",
        "hex:nooooooo",
        "hex:00",
        None,
    ],
)
def test_unavailable_malformed_wrong_endian_and_nonfinite_are_never_valid_voltage(raw):
    assert decode_measurement(1, 4, raw).value is None


def test_units_enums_rssi_sentinel_and_wrong_tags():
    assert decode_measurement(9, 2, -200).value is None
    assert decode_measurement(9, 2, -47).text == "-47 dB"  # MIB does not promise dBm
    assert decode_measurement(11, 2, 0).text == "DC"
    assert decode_measurement(12, 2, 0).text == "Bağlı değil"
    assert decode_measurement(12, 2, 1).text == "Bağlı"
    assert decode_measurement(11, 2, 7).value is None
    assert decode_measurement(13, 4, raw_float(-1)).value is None
    assert decode_measurement(4, 4, raw_float(0)).value is None
    assert decode_measurement(1, 2, 14).value is None
    assert decode_measurement(5, 4, raw_float(30)).value is None


def test_metric_log_and_per_field_staleness(tmp_path, monkeypatch):
    monitor = SnmpMonitor(tmp_path)
    monitor.observe(
        SnmpMessage("response", 1, 0, "", ((DATA_BASE + "1.0", 4, raw_float(13.9)),)), now=100
    )
    record = monitor.snapshot()["measurements"][1]
    assert measurement_cell(record, 110, True) == ("13.90 V", "10 sn önce")
    # Fresh unrelated traps must not make an old voltage current.
    monitor.observe(SnmpMessage("trap", None, 0, "unrelated", ()), now=145)
    assert "eski" in measurement_cell(record, 146, True)[1]
    assert "eski" in measurement_cell(record, 110, False)[1]
    # Invalid new reading replaces the old number, instead of displaying stale voltage as new.
    monitor.observe(
        SnmpMessage("response", 2, 0, "", ((DATA_BASE + "1.0", 4, raw_float(-1)),)), now=150
    )
    assert monitor.snapshot()["measurements"][1]["value"] is None
    items = [
        json.loads(line)
        for path in (tmp_path / "hytera-status").glob("*")
        for line in path.read_text("utf-8").splitlines()
    ]
    assert "13.90 V" in items[0]["raw"] and items[0]["category"] == "SNMP ölçüm"
    assert items[0]["values"][0][2] == raw_float(13.9)


def test_numeric_panel_displays_measurement_and_alarm_separately(tmp_path, monkeypatch):
    def no_socket(*args, **kwargs):
        raise AssertionError("UI test must not use network")

    monkeypatch.setattr("socket.socket", no_socket)
    root = tk.Tk()
    root.withdraw()
    try:
        panel = RepeaterSettingsPanel(ttk.Notebook(root), tmp_path)
        panel.snmp.observe(
            SnmpMessage("response", 1, 0, "", ((DATA_BASE + "1.0", 4, raw_float(13.9)),))
        )
        panel.show_health()
        assert "13.90 V" in panel.measurement_text.get()
        assert panel.health_fields.set("1", "reading") == "13.90 V"
        assert panel.health_fields.set("1", "value") == "Henüz bildirilmedi"
        assert "eski" in panel.health_fields.set("1", "age")  # service is stopped
        assert panel.health_fields.exists("metric11")
    finally:
        root.destroy()
