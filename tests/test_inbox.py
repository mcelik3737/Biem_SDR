import json

from biem_radia.inbox import InboxStore, raw_message


def test_private_target_is_not_group():
    row = raw_message(
        {"raw": "Slot 1 Data Header - Indiv - Short Data: Defined Source: 3737 Target: 5"}
    )
    assert row["source_id"] == 3737
    assert row["call_type"] == "private"
    assert raw_message({"raw": "SLOT 1 TGT=5 SRC=3737 Group Voice"}) is None


def test_inbox_indexes_once_and_filters_without_touching_source(tmp_path):
    log = tmp_path / "dmr-sessions/test/digital.jsonl"
    log.parent.mkdir(parents=True)
    event = {
        "observed_utc": "2026-09-12T12:00:00+00:00",
        "channel": "Test",
        "protocol": "DMR",
        "raw": "Slot 1 Data Header - Group - Short Data: Defined Source: 3737 Target: 21",
    }
    original = json.dumps(event) + "\n"
    log.write_text(original, "utf-8")
    store = InboxStore(tmp_path)
    assert store.poll()
    assert not store.poll()
    row = store.search("3737")[0]
    assert row["group_id"] == "21"
    assert row["kind"].startswith("Ham veri")
    assert len(store.search(day=row["at_local"][:10])) == 1
    assert not store.search("missing")
    assert not InboxStore(tmp_path).poll()
    assert len(store.search()) == 1
    assert log.read_text("utf-8") == original


def test_private_message_persists_without_group(tmp_path):
    store = InboxStore(tmp_path)
    store.add(
        {"source_id": 3737, "target_id": 5, "call_type": "private", "text": "Test"}, "test", "1"
    )
    row = store.search()[0]
    assert row["group_id"] == ""
    assert row["target_id"] == "5"
