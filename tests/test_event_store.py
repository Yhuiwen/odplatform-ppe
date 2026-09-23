import json

import pytest

from core.schemas.compliance import ComplianceEvent, ComplianceEventType
from infra.storage.json_event_store import EventStoreError, JSONEventStore


def _event() -> ComplianceEvent:
    return ComplianceEvent(
        event_id="EVT-test",
        track_id=7,
        event_type=ComplianceEventType.NO_HELMET,
        confidence=0.91,
        timestamp=1.25,
        evidence=("helmet=no_hardhat",),
    )


def test_event_store_appends_frozen_json_contract(tmp_path) -> None:
    store = JSONEventStore(tmp_path / "events.jsonl")

    assert store.append(_event()) is None
    records = store.read_all()

    assert records == [
        {
            "type": "NO_HELMET",
            "track_id": 7,
            "confidence": 0.91,
            "timestamp": 1.25,
        }
    ]


def test_event_store_does_not_create_file_for_empty_batch(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    store = JSONEventStore(path)

    assert store.append_many(()) == 0
    assert not path.exists()


def test_event_store_rejects_invalid_event_object(tmp_path) -> None:
    store = JSONEventStore(tmp_path / "events.jsonl")

    with pytest.raises(EventStoreError, match="ComplianceEvent"):
        store.append({"type": "NO_HELMET"})  # type: ignore[arg-type]


def test_event_store_reports_malformed_json(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(EventStoreError, match="valid event evidence"):
        JSONEventStore(path).read_all()


def test_event_store_records_are_json_lines(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    JSONEventStore(path).append_many((_event(), _event()))

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert all(set(json.loads(line)) == {
        "type",
        "track_id",
        "confidence",
        "timestamp",
    } for line in lines)
