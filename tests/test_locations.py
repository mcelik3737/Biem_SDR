import json
import tkinter as tk
from datetime import datetime, timezone

from biem_radia.locations import LocationParser, LocationReader, coordinates
from biem_radia.map_panel import MapPanel
from biem_radia.storage import Archive


def message_events(source=101, lat=39.9, lon=32.8):
    text = f"Boylam:\nE {lon}°\nEnlem:\nN {lat}°\nZaman:\n12:34:56\nTarih:\n2026-09-12"
    payload = b"\x00\x03" + text.encode("utf-16-le") + b"\x00\x00\x00\xd8\x00\xd8"
    lines = [
        "12:34:56 Sync: +DMR MS/DM MODE/MONO | Color Code=01 | DATA",
        f"Slot 1 Data Header - Indiv - Short Data: Defined - Response Requested - Source: {source} Target: 5",
        "SD:D - FMT 15 [UTF-16LE] - Confirmed Data",
        "Slot 1 - Multi Block PDU Message",
        *[payload[i : i + 11].hex() for i in range(0, len(payload), 11)],
        "DMR PDU Payload [00]",
    ]
    return [
        {
            "raw": line,
            "protocol": "DMR",
            "observed_utc": "2026-09-12T09:34:56+00:00",
            "channel": "Test",
            "frequency_hz": 427500000,
        }
        for line in lines
    ]


def test_location_parser_header_and_utf16_crc_bytes():
    parser = LocationParser()
    results = [r for e in message_events() if (r := parser.feed(e))]
    assert len(results) == 1
    assert results[0]["latitude"] == 39.9 and results[0]["longitude"] == 32.8
    assert results[0]["source_id"] == 101 and results[0]["target_id"] == 5
    # A bare decoder LOCN guess cannot create a map point or reuse old identity.
    assert parser.feed({"raw": "NMEA / LOCN; Source: 153; (0,0)", "protocol": "DMR"}) is None


def test_reject_missing_header_bad_coordinates_and_error():
    for events in [message_events()[3:], message_events(lat=99)]:
        parser = LocationParser()
        assert not any(parser.feed(e) for e in events)
    events = message_events()
    events.insert(3, {**events[0], "raw": "CRC ERR"})
    parser = LocationParser()
    assert not any(parser.feed(e) for e in events)
    assert coordinates("Boylam: E 29°") is None


def test_reader_new_location_persists_and_empty_packet_keeps_previous(tmp_path):
    directory = tmp_path / "dmr-sessions/test"
    directory.mkdir(parents=True)
    path = directory / "digital.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in message_events()) + "\n", "utf-8")
    reader = LocationReader(tmp_path)
    assert reader.poll()
    assert reader.latest["source_id"] == 101
    assert not reader.poll()
    assert LocationReader(tmp_path).latest == reader.latest
    with path.open("a", encoding="utf-8") as f:
        for e in message_events(source=202, lon=33.2):
            e["observed_utc"] = "2026-09-12T09:35:56+00:00"
            f.write(json.dumps(e) + "\n")
    assert reader.poll() and reader.latest["source_id"] == 202
    assert reader.latest["longitude"] == 33.2


def test_map_radio_projection_and_zoom(tmp_path):
    root = tk.Tk()
    root.withdraw()
    try:
        panel = MapPanel(root, Archive(tmp_path))
        panel.pack(fill="both", expand=True)
        root.geometry("1100x700")
        root.deiconify()
        root.update()
        panel.reader.latest = {
            "latitude": 39.9,
            "longitude": 32.8,
            "source_id": 101,
            "observed_utc": datetime.now(timezone.utc).isoformat(),
        }
        panel.refresh_labels()
        panel.render()
        x, y = panel.screen(32.8, 39.9)
        assert 0 < x < panel.canvas.winfo_width() and 0 < y < panel.canvas.winfo_height()
        assert panel.canvas.find_withtag("radio")
        # Identity does not provide a location; an explicitly decoded GNSS fix does.
        identity = {"alias": "Test rölesi", "radio_id": 3700}
        panel.set_repeater(identity)
        assert not panel.canvas.find_withtag("repeater")
        assert "henüz alınmadı" in panel.repeater_text.get()
        fix = {
            "latitude": 39.9,
            "longitude": 32.8,
            "observed_utc": datetime.now(timezone.utc).isoformat(),
            "fix_valid": True,
            "basis": "Hytera SNMP GNSS",
        }
        panel.set_repeater(identity, {**fix, "latitude": float("nan")})
        assert not panel.canvas.find_withtag("repeater")
        panel.set_repeater(identity, {**fix, "fix_valid": False})
        assert not panel.canvas.find_withtag("repeater")
        panel.set_repeater(identity, fix)
        assert panel.canvas.find_withtag("repeater")
        assert panel.canvas.find_withtag("radio")  # distinct symbols coexist
        panel.focus_repeater()
        rx, ry = panel.screen(32.8, 39.9)
        assert rx == panel.canvas.winfo_width() / 2
        assert ry == panel.canvas.winfo_height() / 2
        panel.reset()
        initial_height = panel.radio_size
        assert panel.canvas.find_withtag("radio-photo")
        panel.focus_radio()
        x, y = panel.screen(32.8, 39.9)
        assert abs(x - panel.canvas.winfo_width() / 2) < 0.01
        assert abs(y - panel.canvas.winfo_height() / 2) < 0.01
        assert panel.radio_size > initial_height
        assert panel.canvas.coords(panel.canvas.find_withtag("radio-photo")[0]) == [x, y]
        panel.reset()
        assert panel.zoom == 1
        assert panel.radio_size == initial_height
        assert len(panel.detail_layer.provinces) == 81
        assert panel.canvas.find_withtag("province")
        assert panel.canvas.find_withtag("city")
        assert panel.canvas.find_withtag("lake")
        assert panel.canvas.find_withtag("scale")
        panel.show_cities.set(False)
        panel.render()
        assert not panel.canvas.find_withtag("city")
        assert panel.canvas.find_withtag("radio")
    finally:
        root.destroy()
