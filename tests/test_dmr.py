from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from biem_radia.dmr import DmrDiscriminator, DmrImporter, parse_event
from biem_radia.models import SAMPLE_RATE, Channel
from biem_radia.storage import Archive


def fixture_call(
    directory: Path, *, radio=101, target=201, slot=1, second=10, kind="GROUP", cc=11, silent=False
):
    directory.mkdir(exist_ok=True)
    stamp = f"20260912_1200{second:02}"
    path = directory / f"{stamp}_{radio:05}_DMR_CC_{cc}_{kind}_TGT_{target}_SRC_{radio}.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        pcm = (
            np.zeros(8000, dtype="<i2")
            if silent
            else (np.sin(np.arange(8000) * 0.5) * 10000).astype("<i2")
        )
        wav.writeframes(pcm.tobytes())
    line = f"2026-09-12 12:00:{second:02} DMR TGT: {target:08}; SRC: {radio:08}; CC: {cc:02}; {kind.title()}; "
    if slot is not None:
        line += f"Slot {slot}; "
    with (directory / "events.log").open("a", encoding="utf-8") as log:
        log.write(line + "\n")
    return path


def test_two_slots_have_independent_ids_audio_and_scoped_aliases(tmp_path):
    archive = Archive(tmp_path / "archive")
    archive.set_alias("Plant A", "radio", "101", "Güvenlik")
    archive.set_alias("Plant B", "radio", "101", "Başka Tesis")
    channel = Channel("DMR", 427500000, mode="DMR", system="Plant A", color_code=11)
    session = tmp_path / "session"
    fixture_call(session, radio=101, slot=1)
    fixture_call(session, radio=102, slot=2)
    importer = DmrImporter(archive, channel, session)
    assert importer.scan() == 2
    assert importer.scan() == 0
    calls = archive.search()
    assert {(c["radio_id"], c["group_id"], c["slot"]) for c in calls} == {
        ("101", "201", 1),
        ("102", "201", 2),
    }
    assert len({str(archive.audio_path(c["id"])) for c in calls}) == 2
    assert len(archive.search("GÜVENLİK", slot=1, system="Plant A")) == 1
    assert not archive.search("Başka Tesis")
    assert len(archive.search("102", slot=2)) == 1
    assert DmrImporter(archive, channel, session).scan() == 2  # re-import is DB-idempotent
    assert len(archive.search()) == 2


def test_private_destination_is_not_a_group_and_dmo_slot_is_unknown(tmp_path):
    session = tmp_path / "session"
    fixture_call(session, target=55, kind="PRIVATE", slot=None)
    archive = Archive(tmp_path / "archive")
    importer = DmrImporter(archive, Channel("A", 427500000, mode="DMR"), session)
    importer.scan()
    call = archive.search()[0]
    assert call["destination_id"] == "55" and call["group_id"] is None
    assert call["slot"] is None
    assert call["call_type"] == "private"
    assert archive.search("55")


def test_missing_event_does_not_inherit_previous_call_identity(tmp_path):
    session = tmp_path / "session"
    fixture_call(session)
    archive = Archive(tmp_path / "archive")
    importer = DmrImporter(archive, Channel("A", 427500000, mode="DMR"), session)
    assert importer.scan() == 1
    before = (session / "events.log").read_text()
    fixture_call(session, radio=102, second=11)
    (session / "events.log").write_text(before)
    assert importer.scan() == 0
    assert len(archive.search()) == 1


def test_ambiguous_same_ids_in_both_slots_are_quarantined(tmp_path):
    session = tmp_path / "session"
    fixture_call(session, slot=1)
    line = (session / "events.log").read_text().replace("Slot 1", "Slot 2")
    with (session / "events.log").open("a") as f:
        f.write(line)
    archive = Archive(tmp_path / "archive")
    importer = DmrImporter(archive, Channel("A", 427500000, mode="DMR"), session)
    assert importer.scan() == 0
    assert not archive.search()
    assert list(session.glob("*.wav"))


@pytest.mark.parametrize("case", ["silent", "encrypted", "color"])
def test_non_audio_and_excluded_calls_are_not_reported_as_recorded(tmp_path, case):
    session = tmp_path / "session"
    fixture_call(session, silent=case == "silent", cc=10 if case == "color" else 11)
    if case == "encrypted":
        p = session / "events.log"
        p.write_text(p.read_text().replace("Group;", "ENC; Group;"))
    archive = Archive(tmp_path / "archive")
    assert (
        DmrImporter(archive, Channel("A", 427500000, mode="DMR", color_code=11), session).scan()
        == 0
    )
    assert not archive.search()


def test_metadata_only_unknown_ids_and_invalid_lines():
    event = parse_event("2026-09-12 12:00:10 DMR TGT: 00000000; SRC: 00000000; CC: 11;")
    assert event is not None and event.radio is None and event.target is None and event.slot is None
    assert parse_event("SLOT 1 TGT=101 SRC=201 Group Call") is None
    assert parse_event("2026-09-12 12:00:10 DMR TGT: 00000001; SRC: 00000001; CC: 99;") is None


def test_discriminator_preserves_dc_and_four_level_signal_in_irregular_blocks():
    c = Channel("A", 427500000, mode="DMR")
    n = SAMPLE_RATE // 10
    # A constant outer symbol must remain constant; the analog voice HPF would remove it.
    iq = 0.2 * np.exp(2j * np.pi * (-100000 + 1944) * np.arange(n) / SAMPLE_RATE)
    d = DmrDiscriminator(c, c.frequency_hz + 100000)
    blocks = [d.process(iq[i : i + 8191])[0] for i in range(0, n, 8191)]
    pcm = np.frombuffer(b"".join(blocks), dtype="<i2")
    assert len(pcm) == 4800
    assert np.median(pcm[1000:]) == pytest.approx(1944 * 32767 / 12000, abs=2)
    entire = DmrDiscriminator(c, c.frequency_hz + 100000).process(iq)[0]
    np.testing.assert_allclose(pcm, np.frombuffer(entire, dtype="<i2"), atol=1)


def test_dmr_is_not_a_6250_hz_filter_setting():
    with pytest.raises(ValueError, match="12500"):
        Channel("A", 427500000, mode="DMR", spacing_hz=6250)
