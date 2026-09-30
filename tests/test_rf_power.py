import json
import time
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pytest
from test_dmr import fixture_call

from biem_radia.dmr import DmrImporter, parse_event
from biem_radia.models import AUDIO_RATE, Channel
from biem_radia.recorder import CallRecorder
from biem_radia.rf_power import PowerCalibrations, PowerContext, RFPowerMeter, device_identity
from biem_radia.storage import Archive
from biem_radia.tetra import TetraBackend


def meter_at(tmp_path, mode="NFM"):
    channel = Channel("RF test", 424000000, mode=mode)
    return RFPowerMeter(channel, PowerContext("unique USB", 19.0, 15), PowerCalibrations(tmp_path))


def test_external_reference_persists_and_not_gain_subtraction(tmp_path):
    meter = meter_at(tmp_path)
    reading = meter.observe(-30, 0.02)
    assert reading["rf_dbm"] is None
    meter.calibrations.save_reference(reading, -70)
    meter.calibrations = PowerCalibrations(tmp_path)
    assert meter.observe(-25, 0.02)["rf_dbm"] == -65
    meter.context.gain_db = 29
    assert meter.observe(-15, 0.02)["rf_dbm"] is None
    meter.calibrations.save_reference(meter.latest, -70)
    assert meter.observe(-15, 0.02)["rf_dbm"] == -70
    meter.context.gain_db = 19
    assert meter.observe(-30, 0.02)["rf_dbm"] == -70
    meter.channel = replace(meter.channel, frequency_hz=425000000)
    assert meter.observe(-30, 0.02)["rf_dbm"] is None


@pytest.mark.parametrize(
    "field,value", [("gain_db", None), ("device", None), ("clipped", True), ("settling", True)]
)
def test_agc_unknown_device_clipping_and_settling_never_label_dbm(tmp_path, field, value):
    meter = meter_at(tmp_path)
    meter.calibrations.save_reference(meter.observe(-30, 0.02), -70)
    setattr(meter.context, field, value)
    reading = meter.observe(-25, 0.02)
    assert reading["rf_dbm"] is None
    with pytest.raises(ValueError):
        meter.calibrations.save_reference(reading, -70)


def test_stale_reference_and_corrupt_profile_fail_closed(tmp_path):
    meter = meter_at(tmp_path)
    with pytest.raises(ValueError):
        meter.calibrations.save_reference(meter.observe(-25, 0.02, end=time.time() - 5), -70)
    meter.calibrations.path.write_text('{"profiles":[{"offset_db": "nan"}]}')
    restored = PowerCalibrations(tmp_path)
    assert restored.error and not restored.entries


def test_peak_is_numerical_max_with_context_and_missing_intervals(tmp_path):
    meter = meter_at(tmp_path)
    meter.calibrations.save_reference(meter.observe(-30, 0.02), -70)
    meter.history.clear()
    for end, level in [(1, -60), (2, -20), (3, -45)]:
        meter.observe(level, 1, end=end)
    result = meter.summary(0, 3)
    assert result["rf_peak_dbfs"] == -20 and result["rf_peak_dbm"] == -60
    assert json.loads(result["rf_power_info"])["peak_dbfs_context"]["gain_db"] == 19
    assert meter.summary(2, 3)["rf_peak_dbm"] == -85
    assert meter.summary(6, 7) == {}
    assert meter.summary(-2, 3)["rf_peak_dbm"] is None
    meter.observe(-10, 1, end=5)  # gap: cannot claim complete call maximum in dBm
    assert meter.summary(0, 5)["rf_peak_dbm"] is None


def test_analog_peak_per_segment_and_raw_rf_independent_of_audio_gate(tmp_path):
    archive = Archive(tmp_path)
    epoch = datetime(2026, 9, 30, tzinfo=timezone.utc)
    recorder = CallRecorder(archive, Channel("A", 424000000), "USB", epoch)
    recorder.rf_power = meter_at(tmp_path)
    for second in range(185):
        # Strongest signal during the two-second pause must not contaminate either file.
        level = -5 if second in (90, 91, 182, 183) else -21 if second < 90 else -35
        recorder.feed(np.ones(AUDIO_RATE) * 0.1, -30, rf_level=level)
    recorder.finish("stopped")
    rows = sorted(archive.search(), key=lambda row: row["started_utc"])
    assert [r["duration"] for r in rows] == [90, 90, 1]
    assert [r["rf_peak_dbfs"] for r in rows] == [-21, -35, -35]
    assert all(r["rf_peak_dbm"] is None for r in rows)
    assert "_max-21.0dBFS.wav" in rows[0]["path"]
    recorder = CallRecorder(archive, Channel("Gate", 424000000), "USB", epoch)
    recorder.rf_power = meter_at(tmp_path)
    recorder.feed(np.ones(1600) * 0.1, -30, rf_level=-24)
    recorder.feed(np.zeros(1600), -120, rf_level=-15)
    recorder.finish("stopped")
    assert archive.search("Gate")[0]["rf_peak_dbfs"] == -15


def test_dmr_slots_keep_identity_and_save_shared_channel_peak(tmp_path):
    archive = Archive(tmp_path / "data")
    session = tmp_path / "session"
    fixture_call(session, radio=101, slot=1)
    fixture_call(session, radio=102, slot=2)
    importer = DmrImporter(archive, Channel("DMR", 424000000, mode="DMR"), session)
    meter = meter_at(tmp_path, "DMR")
    meter.calibrations.save_reference(meter.observe(-30, 0.02), -70)
    meter.history.clear()
    event = parse_event((session / "events.log").read_text().splitlines()[0])
    assert event is not None
    end = event.observed.timestamp()
    meter.observe(-29, 0.5, end=end - 0.5)
    meter.observe(-25, 0.5, end=end)
    importer.rf_power = meter
    assert importer.scan() == 2
    rows = archive.search()
    assert {r["slot"] for r in rows} == {1, 2}
    for row in rows:
        assert row["rf_peak_dbm"] == -65
        assert "_max-65.0dBm.wav" in row["path"]
        info = json.loads(row["rf_power_info"])
        assert info["channel_shared_rf"] and info["timing"] == "decoder_estimated_window"


def test_tetra_finish_stores_peak_and_preserves_protocol_slot(tmp_path):
    backend = TetraBackend.__new__(TetraBackend)
    backend.archive = Archive(tmp_path)
    backend.channel = Channel("T", 424000000, 25000, 25000, mode="TETRA")
    backend.cc, backend.completed = 11, 0
    start = datetime(2026, 9, 30, tzinfo=timezone.utc)
    backend.calls = {
        2: {"started": start, "chunks": [b"\x01\x00" * 480], "last_utc": start.timestamp() + 0.06}
    }
    backend.rf_power = RFPowerMeter(backend.channel, PowerContext(), PowerCalibrations(tmp_path))
    backend.rf_power.observe(-32.5, 0.12, end=start.timestamp() + 0.06)
    backend._finish(2)
    row = backend.archive.search()[0]
    assert row["protocol_slot"] == 2 and row["color_code"] == 11
    assert row["rf_peak_dbfs"] == -32.5 and "_max-32.5dBFS.wav" in row["path"]


def test_usb_calibration_never_binds_duplicate_serial_or_index(tmp_path):
    devices = [dict(serial="01", manufacturer="Test", product="SDR")]
    source = SimpleNamespace(library=SimpleNamespace(inventory=lambda: devices))
    identity = device_identity(source, 0)
    assert identity
    devices.insert(0, dict(serial="02"))
    assert device_identity(source, 1) == identity
    devices.append(devices[1])
    assert device_identity(source, 1) is None
    assert device_identity(SimpleNamespace(), 0) is None


def test_existing_archive_migration_does_not_invent_historical_power(tmp_path):
    archive = Archive(tmp_path)
    recorder = CallRecorder(archive, Channel("Old", 424000000), "USB", datetime.now(timezone.utc))
    recorder.feed(np.ones(1600) * 0.1, -30)
    recorder.finish("stopped")
    path = archive.search()[0]["path"]
    with archive.connect() as db:
        for column in ("rf_peak_dbfs", "rf_peak_dbm", "rf_power_info"):
            db.execute(f"ALTER TABLE calls DROP COLUMN {column}")
    row = Archive(tmp_path).search()[0]
    assert row["path"] == path and (tmp_path / path).is_file()
    assert (
        row["rf_peak_dbfs"] is None and row["rf_peak_dbm"] is None and row["rf_power_info"] is None
    )
