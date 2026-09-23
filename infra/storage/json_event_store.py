"""Append-only JSONL storage for Phase 6 compliance events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from core.schemas.compliance import ComplianceEvent
from utils.paths import PROJECT_ROOT

__all__ = ["EventStoreError", "JSONEventStore"]


class EventStoreError(RuntimeError):
    """Raised when event evidence cannot be written or read safely."""

    code = "event_store_error"


class JSONEventStore:
    """Persist the frozen four-field event wire contract as JSON lines."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = (
            Path(path).expanduser().resolve()
            if path is not None
            else (PROJECT_ROOT / "outputs" / "events.jsonl")
        )

    def append(self, event: ComplianceEvent) -> None:
        """Append one validated event."""

        self.append_many((event,))

    def append_many(self, events: Iterable[ComplianceEvent]) -> int:
        """Append events in order and return the number written."""

        normalized = tuple(events)
        if not normalized:
            return 0
        for event in normalized:
            if not isinstance(event, ComplianceEvent):
                raise EventStoreError(
                    "JSONEventStore accepts ComplianceEvent objects only"
                )

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                for event in normalized:
                    handle.write(
                        json.dumps(
                            event.to_dict(),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                    )
                    handle.write("\n")
        except OSError as exc:
            raise EventStoreError(
                f"Could not append events to {self.path}"
            ) from exc
        return len(normalized)

    def read_all(self) -> list[dict[str, object]]:
        """Read all JSONL records and fail on malformed evidence."""

        if not self.path.exists():
            return []
        records: list[dict[str, object]] = []
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    if not isinstance(payload, dict):
                        raise EventStoreError(
                            f"Event line {line_number} must be a JSON object"
                        )
                    records.append(payload)
        except (OSError, json.JSONDecodeError) as exc:
            raise EventStoreError(
                f"Could not read valid event evidence from {self.path}"
            ) from exc
        return records
