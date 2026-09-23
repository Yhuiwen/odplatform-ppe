"""Phase 7 persisted event contracts.

These contracts project a Phase 6 ``ComplianceEvent`` into storage without
changing the frozen four-field JSONL wire representation.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, Mapping

from core.schemas.compliance import ComplianceEventType

__all__ = [
    "EventPage",
    "EventQuery",
    "EventStatistics",
    "EventStatus",
    "PersistedEvent",
    "PERSISTED_EVENT_SCHEMA_VERSION",
    "SnapshotReference",
    "StoredEvent",
    "format_utc_timestamp",
    "normalize_utc_timestamp",
]

PERSISTED_EVENT_SCHEMA_VERSION = "phase7-event-v1"


class EventStatus(str, Enum):
    """Frozen dashboard-visible event lifecycle."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


def format_utc_timestamp(value: datetime) -> str:
    """Return one UTC ISO 8601 timestamp with a trailing ``Z``."""

    if not isinstance(value, datetime):
        raise TypeError("timestamp must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")

    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_utc_timestamp(value: str) -> str:
    """Validate and canonicalize a persisted ISO 8601 UTC timestamp."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO 8601 string")
    candidate = value.strip()
    parse_value = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate
    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as exc:
        raise ValueError("timestamp must be valid ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return format_utc_timestamp(parsed)


def _validate_track_id(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("track_id must be an integer")
    if value < 0:
        raise ValueError("track_id cannot be negative")
    return value


def _validate_confidence(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("confidence must be numeric")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError("confidence must be finite and between 0 and 1")
    return normalized


def _normalize_snapshot(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("snapshot must be a non-empty relative POSIX path or None")
    candidate = value.strip()
    path = PurePosixPath(candidate)
    if (
        path.is_absolute()
        or "\\" in candidate
        or re.match(r"^[A-Za-z]:/", candidate) is not None
    ):
        raise ValueError("snapshot must be a relative POSIX path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("snapshot cannot contain empty, current or parent segments")
    return path.as_posix()


def _normalize_bbox(
    value: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError("bbox must be a mapping or None")
    normalized = dict(value)
    for key, item in normalized.items():
        if not isinstance(key, str) or not key:
            raise ValueError("bbox keys must be non-empty strings")
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("bbox numeric values must be finite")
    return normalized


def _validate_positive_dimension(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_sha256(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("sha256 must be a string")
    normalized = value.lower()
    if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
        raise ValueError("sha256 must be a 64-character hexadecimal digest")
    return normalized


@dataclass(frozen=True, slots=True)
class PersistedEvent:
    """Frozen seven-field event projection for queries and UI output."""

    id: str
    timestamp: str
    track_id: int
    type: ComplianceEventType
    confidence: float
    snapshot: str | None
    status: EventStatus

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id cannot be empty")
        object.__setattr__(self, "timestamp", normalize_utc_timestamp(self.timestamp))
        object.__setattr__(self, "track_id", _validate_track_id(self.track_id))
        try:
            event_type = ComplianceEventType(self.type)
        except ValueError as exc:
            raise ValueError("type must be a supported compliance event type") from exc
        object.__setattr__(self, "type", event_type)
        object.__setattr__(
            self, "confidence", _validate_confidence(self.confidence)
        )
        object.__setattr__(self, "snapshot", _normalize_snapshot(self.snapshot))
        try:
            status = EventStatus(self.status)
        except ValueError as exc:
            raise ValueError("status must be a supported event status") from exc
        object.__setattr__(self, "status", status)

    def to_dict(self) -> dict[str, Any]:
        """Return the persisted-event JSON projection."""

        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "track_id": self.track_id,
            "type": self.type.value,
            "confidence": self.confidence,
            "snapshot": self.snapshot,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class SnapshotReference:
    """Verified evidence-file metadata associated with one event."""

    snapshot_id: str
    event_id: str
    relative_path: str
    sha256: str
    width: int
    height: int
    mime_type: str
    captured_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_id, str) or not self.snapshot_id.strip():
            raise ValueError("snapshot_id cannot be empty")
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id cannot be empty")
        snapshot_path = _normalize_snapshot(self.relative_path)
        if snapshot_path is None:
            raise ValueError("relative_path cannot be empty")
        object.__setattr__(self, "snapshot_id", self.snapshot_id.strip())
        object.__setattr__(self, "event_id", self.event_id.strip())
        object.__setattr__(self, "relative_path", snapshot_path)
        object.__setattr__(self, "sha256", _normalize_sha256(self.sha256))
        object.__setattr__(
            self,
            "width",
            _validate_positive_dimension(self.width, "width"),
        )
        object.__setattr__(
            self,
            "height",
            _validate_positive_dimension(self.height, "height"),
        )
        if self.mime_type != "image/jpeg":
            raise ValueError("mime_type must be image/jpeg")
        object.__setattr__(
            self,
            "captured_at",
            normalize_utc_timestamp(self.captured_at),
        )

    def has_same_identity(self, other: "SnapshotReference") -> bool:
        """Return whether two references describe the same evidence file."""

        return (
            self.snapshot_id == other.snapshot_id
            and self.event_id == other.event_id
            and self.relative_path == other.relative_path
            and self.sha256 == other.sha256
            and self.width == other.width
            and self.height == other.height
            and self.mime_type == other.mime_type
            and self.captured_at == other.captured_at
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot metadata projection."""

        return {
            "snapshot_id": self.snapshot_id,
            "event_id": self.event_id,
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "width": self.width,
            "height": self.height,
            "mime_type": self.mime_type,
            "captured_at": self.captured_at,
        }


@dataclass(frozen=True, slots=True)
class StoredEvent:
    """Complete internal row used at the persistence boundary."""

    id: str
    timestamp: str
    track_id: int
    type: ComplianceEventType
    confidence: float
    source_timestamp: float
    source: str
    snapshot: str | None = None
    status: EventStatus = EventStatus.OPEN
    frame_id: int | None = None
    bbox: Mapping[str, Any] | None = None
    worker_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id cannot be empty")
        timestamp = normalize_utc_timestamp(self.timestamp)
        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "track_id", _validate_track_id(self.track_id))
        try:
            event_type = ComplianceEventType(self.type)
        except ValueError as exc:
            raise ValueError("type must be a supported compliance event type") from exc
        object.__setattr__(self, "type", event_type)
        object.__setattr__(
            self, "confidence", _validate_confidence(self.confidence)
        )
        if (
            isinstance(self.source_timestamp, bool)
            or not isinstance(self.source_timestamp, (int, float))
        ):
            raise TypeError("source_timestamp must be numeric")
        source_timestamp = float(self.source_timestamp)
        if not math.isfinite(source_timestamp) or source_timestamp < 0:
            raise ValueError("source_timestamp must be finite and non-negative")
        object.__setattr__(self, "source_timestamp", source_timestamp)
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source cannot be empty")
        source = self.source.strip()
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "snapshot", _normalize_snapshot(self.snapshot))
        try:
            status = EventStatus(self.status)
        except ValueError as exc:
            raise ValueError("status must be a supported event status") from exc
        object.__setattr__(self, "status", status)
        if self.frame_id is not None:
            if isinstance(self.frame_id, bool) or not isinstance(self.frame_id, int):
                raise TypeError("frame_id must be an integer or None")
            if self.frame_id < 0:
                raise ValueError("frame_id cannot be negative")
        object.__setattr__(self, "bbox", _normalize_bbox(self.bbox))
        if self.worker_id is not None:
            if not isinstance(self.worker_id, str) or not self.worker_id.strip():
                raise ValueError("worker_id must be a non-empty string or None")
            object.__setattr__(self, "worker_id", self.worker_id.strip())

        created_at = (
            normalize_utc_timestamp(self.created_at)
            if self.created_at is not None
            else timestamp
        )
        updated_at = (
            normalize_utc_timestamp(self.updated_at)
            if self.updated_at is not None
            else created_at
        )
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)

    @property
    def bbox_json(self) -> str | None:
        """Return a deterministic JSON encoding for optional bbox metadata."""

        if self.bbox is None:
            return None
        import json

        return json.dumps(
            self.bbox,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    def to_persisted(self) -> PersistedEvent:
        return PersistedEvent(
            id=self.id,
            timestamp=self.timestamp,
            track_id=self.track_id,
            type=self.type,
            confidence=self.confidence,
            snapshot=self.snapshot,
            status=self.status,
        )

    def has_same_identity(self, other: "StoredEvent") -> bool:
        """Return whether another row has equivalent immutable event data."""

        return (
            self.id == other.id
            and self.track_id == other.track_id
            and self.type is other.type
            and self.confidence == other.confidence
            and self.source_timestamp == other.source_timestamp
            and self.source == other.source
            and self.frame_id == other.frame_id
            and self.bbox == other.bbox
            and self.worker_id == other.worker_id
        )


@dataclass(frozen=True, slots=True)
class EventQuery:
    """Validated dashboard-facing event query."""

    start_at: str | None = None
    end_at: str | None = None
    track_id: int | None = None
    event_type: ComplianceEventType | None = None
    status: EventStatus | None = None
    source: str | None = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        if self.start_at is not None:
            object.__setattr__(
                self, "start_at", normalize_utc_timestamp(self.start_at)
            )
        if self.end_at is not None:
            object.__setattr__(
                self, "end_at", normalize_utc_timestamp(self.end_at)
            )
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.start_at > self.end_at
        ):
            raise ValueError("start_at cannot be after end_at")
        if self.track_id is not None:
            object.__setattr__(
                self, "track_id", _validate_track_id(self.track_id)
            )
        if self.event_type is not None:
            try:
                event_type = ComplianceEventType(self.event_type)
            except ValueError as exc:
                raise ValueError(
                    "event_type must be a supported compliance event type"
                ) from exc
            object.__setattr__(self, "event_type", event_type)
        if self.status is not None:
            try:
                status = EventStatus(self.status)
            except ValueError as exc:
                raise ValueError("status must be a supported event status") from exc
            object.__setattr__(self, "status", status)
        if self.source is not None:
            if not isinstance(self.source, str) or not self.source.strip():
                raise ValueError("source must be a non-empty string or None")
            object.__setattr__(self, "source", self.source.strip())
        if isinstance(self.limit, bool) or not isinstance(self.limit, int):
            raise TypeError("limit must be an integer")
        if not 1 <= self.limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        if isinstance(self.offset, bool) or not isinstance(self.offset, int):
            raise TypeError("offset must be an integer")
        if self.offset < 0:
            raise ValueError("offset cannot be negative")


@dataclass(frozen=True, slots=True)
class EventPage:
    """One deterministic page of persisted events."""

    items: tuple[PersistedEvent, ...]
    total_count: int
    generated_at: str
    limit: int
    offset: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "generated_at", normalize_utc_timestamp(self.generated_at)
        )
        if self.total_count < 0:
            raise ValueError("total_count cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "generated_at": self.generated_at,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass(frozen=True, slots=True)
class EventStatistics:
    """Read-only aggregate projection derived from the event source table."""

    total_count: int
    by_type: tuple[tuple[ComplianceEventType, int], ...]
    by_status: tuple[tuple[EventStatus, int], ...]
    by_source: tuple[tuple[str, int], ...]
    by_day: tuple[tuple[str, int], ...]
    earliest_at: str | None
    latest_at: str | None
    generated_at: str

    def __post_init__(self) -> None:
        if isinstance(self.total_count, bool) or not isinstance(
            self.total_count, int
        ):
            raise TypeError("total_count must be an integer")
        if self.total_count < 0:
            raise ValueError("total_count cannot be negative")

        normalized_types: list[tuple[ComplianceEventType, int]] = []
        for event_type, count in self.by_type:
            normalized_types.append((ComplianceEventType(event_type), int(count)))
        normalized_statuses: list[tuple[EventStatus, int]] = []
        for status, count in self.by_status:
            normalized_statuses.append((EventStatus(status), int(count)))
        normalized_sources: list[tuple[str, int]] = []
        for source, count in self.by_source:
            if not isinstance(source, str) or not source.strip():
                raise ValueError("source counts require non-empty strings")
            normalized_sources.append((source.strip(), int(count)))
        normalized_days: list[tuple[str, int]] = []
        for day, count in self.by_day:
            if not isinstance(day, str) or len(day) != 10:
                raise ValueError("day buckets must use YYYY-MM-DD")
            normalized_days.append((day, int(count)))
        for count in (
            *(count for _, count in normalized_types),
            *(count for _, count in normalized_statuses),
            *(count for _, count in normalized_sources),
            *(count for _, count in normalized_days),
        ):
            if count < 0:
                raise ValueError("aggregate counts cannot be negative")

        object.__setattr__(self, "by_type", tuple(normalized_types))
        object.__setattr__(self, "by_status", tuple(normalized_statuses))
        object.__setattr__(self, "by_source", tuple(normalized_sources))
        object.__setattr__(self, "by_day", tuple(normalized_days))
        if self.earliest_at is not None:
            object.__setattr__(
                self,
                "earliest_at",
                normalize_utc_timestamp(self.earliest_at),
            )
        if self.latest_at is not None:
            object.__setattr__(
                self,
                "latest_at",
                normalize_utc_timestamp(self.latest_at),
            )
        object.__setattr__(
            self,
            "generated_at",
            normalize_utc_timestamp(self.generated_at),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_count": self.total_count,
            "by_type": {key.value: value for key, value in self.by_type},
            "by_status": {key.value: value for key, value in self.by_status},
            "by_source": dict(self.by_source),
            "by_day": dict(self.by_day),
            "earliest_at": self.earliest_at,
            "latest_at": self.latest_at,
            "generated_at": self.generated_at,
        }
