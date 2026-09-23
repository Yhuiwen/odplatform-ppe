"""Shared idempotency and result helpers for alert adapters."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Callable

from core.schemas.alerts import AlertMessage, AlertResult, AlertStatus
from core.schemas.events import format_utc_timestamp


class BaseAlertAdapter:
    """Base class for idempotent delivery by ``event_id``."""

    name = "base"

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._completed: dict[str, AlertResult] = {}
        self._lock = Lock()

    def _timestamp(self) -> str:
        return format_utc_timestamp(self.clock())

    def existing(self, event_id: str) -> AlertResult | None:
        with self._lock:
            existing = self._completed.get(event_id)
            if existing is None:
                return None
            return AlertResult(
                event_id=existing.event_id,
                adapter=existing.adapter,
                status=AlertStatus.SKIPPED,
                timestamp=self._timestamp(),
                error_code="ALERT_DUPLICATE",
                error_message="event was already delivered by this adapter",
            )

    def delivered(self, event_id: str) -> AlertResult:
        result = AlertResult(
            event_id=event_id,
            adapter=self.name,
            status=AlertStatus.DELIVERED,
            timestamp=self._timestamp(),
        )
        with self._lock:
            self._completed[event_id] = result
        return result

    def failed(self, event_id: str, exc: Exception) -> AlertResult:
        return AlertResult(
            event_id=event_id,
            adapter=self.name,
            status=AlertStatus.FAILED,
            timestamp=self._timestamp(),
            error_code="ALERT_ADAPTER_FAILED",
            error_message=f"{type(exc).__name__}: {exc}",
        )
