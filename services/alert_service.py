"""Ordered alert fan-out with adapter-level failure isolation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable

from core.alerts.interfaces import AlertAdapter
from core.schemas.alerts import AlertMessage, AlertResult, AlertStatus
from core.schemas.compliance import ComplianceEventType
from core.schemas.events import PersistedEvent, format_utc_timestamp

__all__ = ["AlertService"]

_ALERT_TEXT = {
    ComplianceEventType.NO_HELMET: "未佩戴安全帽",
    ComplianceEventType.NO_VEST: "未穿反光背心",
    ComplianceEventType.PPE_UNKNOWN: "PPE 状态未知",
}


class AlertService:
    """Dispatch one alert to ordered adapters without blocking the others."""

    def __init__(
        self,
        adapters: Iterable[AlertAdapter],
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.adapters = tuple(adapters)
        names: set[str] = set()
        for adapter in self.adapters:
            name = getattr(adapter, "name", None)
            send = getattr(adapter, "send", None)
            if not isinstance(name, str) or not name:
                raise TypeError("each alert adapter must expose a non-empty name")
            if not callable(send):
                raise TypeError("each alert adapter must expose send(message)")
            if name in names:
                raise ValueError(f"duplicate alert adapter name: {name}")
            names.add(name)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _timestamp(self) -> str:
        return format_utc_timestamp(self.clock())

    @staticmethod
    def message_for_event(event: PersistedEvent) -> AlertMessage:
        """Build one stable alert message from a persisted event."""

        if not isinstance(event, PersistedEvent):
            raise TypeError("event must be a PersistedEvent")
        return AlertMessage(
            event_id=event.id,
            timestamp=event.timestamp,
            track_id=event.track_id,
            alert_type=event.type,
            confidence=event.confidence,
            snapshot=event.snapshot,
            message=(
                f"track {event.track_id}: "
                f"{_ALERT_TEXT[event.type]} ({event.confidence:.2f})"
            ),
        )

    def dispatch(self, message: AlertMessage) -> tuple[AlertResult, ...]:
        """Fan out one message and return every adapter result in order."""

        if not isinstance(message, AlertMessage):
            raise TypeError("message must be an AlertMessage")
        results: list[AlertResult] = []
        for adapter in self.adapters:
            try:
                result = adapter.send(message)
                if not isinstance(result, AlertResult):
                    raise TypeError("adapter returned a non-AlertResult value")
            except Exception as exc:
                result = AlertResult(
                    event_id=message.event_id,
                    adapter=adapter.name,
                    status=AlertStatus.FAILED,
                    timestamp=self._timestamp(),
                    error_code="ALERT_ADAPTER_FAILED",
                    error_message=f"{type(exc).__name__}: {exc}",
                )
            results.append(result)
        return tuple(results)

    def dispatch_event(
        self,
        event: PersistedEvent,
    ) -> tuple[AlertResult, ...]:
        """Convert one persisted event and dispatch it."""

        return self.dispatch(self.message_for_event(event))
