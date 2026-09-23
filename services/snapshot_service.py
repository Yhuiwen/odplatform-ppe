"""Orchestrate verified evidence files and their SQLite metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from core.schemas.events import (
    SnapshotReference,
    format_utc_timestamp,
    normalize_utc_timestamp,
)
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage

__all__ = [
    "SnapshotService",
    "SnapshotServiceConflictError",
    "SnapshotServiceError",
    "SnapshotServiceEventNotFoundError",
]


class SnapshotServiceError(RuntimeError):
    """Base snapshot orchestration failure with a stable machine code."""

    code = "SNAPSHOT_SERVICE_FAILED"


class SnapshotServiceEventNotFoundError(SnapshotServiceError):
    code = "SNAPSHOT_EVENT_NOT_FOUND"


class SnapshotServiceConflictError(SnapshotServiceError):
    code = "SNAPSHOT_CONFLICT"


class SnapshotService:
    """Attach one immutable, verified evidence image to an existing event."""

    def __init__(
        self,
        event_repository: EventRepository,
        snapshot_repository: SnapshotRepository,
        storage: SnapshotStorage,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(event_repository, EventRepository):
            raise TypeError("event_repository must be an EventRepository")
        if not isinstance(snapshot_repository, SnapshotRepository):
            raise TypeError("snapshot_repository must be a SnapshotRepository")
        if not isinstance(storage, SnapshotStorage):
            raise TypeError("storage must be a SnapshotStorage")
        self.event_repository = event_repository
        self.snapshot_repository = snapshot_repository
        self.storage = storage
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _capture_time(self, captured_at: datetime | str | None) -> str:
        if captured_at is None:
            return format_utc_timestamp(self.clock())
        if isinstance(captured_at, datetime):
            return format_utc_timestamp(captured_at)
        if isinstance(captured_at, str):
            return normalize_utc_timestamp(captured_at)
        raise TypeError("captured_at must be a datetime, ISO 8601 string or None")

    @staticmethod
    def _snapshot_id(event_id: str) -> str:
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event_id cannot be empty")
        return f"SNP-{event_id}"

    def capture(
        self,
        event_id: str,
        image: Any,
        *,
        captured_at: datetime | str | None = None,
    ) -> SnapshotReference:
        """Persist one evidence snapshot and return its verified metadata."""

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id cannot be empty")
        normalized_event_id = event_id.strip()
        if self.event_repository.get_record(normalized_event_id) is None:
            raise SnapshotServiceEventNotFoundError(
                f"event does not exist: {normalized_event_id}"
            )
        if image is None:
            raise ValueError("image cannot be None")

        encoded = self.storage.encode(image)
        existing = self.snapshot_repository.get_by_event(
            normalized_event_id
        )
        if existing is not None:
            self.storage.verify(
                existing.relative_path,
                expected_sha256=existing.sha256,
                expected_width=existing.width,
                expected_height=existing.height,
            )
            if (
                existing.sha256 != encoded.sha256
                or existing.width != encoded.width
                or existing.height != encoded.height
                or existing.mime_type != encoded.mime_type
            ):
                raise SnapshotServiceConflictError(
                    "event already has different evidence: "
                    f"{normalized_event_id}"
                )
            return existing

        capture_timestamp = self._capture_time(captured_at)
        relative_path = self.storage.build_relative_path(
            normalized_event_id,
            capture_timestamp,
        )
        stored = self.storage.save_encoded(encoded, relative_path)
        reference = SnapshotReference(
            snapshot_id=self._snapshot_id(normalized_event_id),
            event_id=normalized_event_id,
            relative_path=stored.relative_path,
            sha256=stored.sha256,
            width=stored.width,
            height=stored.height,
            mime_type=stored.mime_type,
            captured_at=capture_timestamp,
        )
        return self.snapshot_repository.get_or_insert(reference)
