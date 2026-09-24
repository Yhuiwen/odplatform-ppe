"""TTS alert adapter with event idempotency and track/type cooldown."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable

from core.schemas.alerts import AlertMessage, AlertResult, AlertStatus
from infra.alerts.base import BaseAlertAdapter
from infra.tts.tts_service import TTSService, TTSServiceError

__all__ = ["TTSAlertAdapter"]


class TTSAlertAdapter(BaseAlertAdapter):
    """Speak confirmed alerts without allowing backend failure to escape."""

    name = "tts"

    def __init__(
        self,
        service: TTSService | None = None,
        *,
        enabled: bool = True,
        cooldown_seconds: float = 30.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(clock=clock)
        if service is not None and not isinstance(service, TTSService):
            raise TypeError("service must be a TTSService or None")
        if isinstance(cooldown_seconds, bool) or not isinstance(
            cooldown_seconds, (int, float)
        ):
            raise TypeError("cooldown_seconds must be numeric")
        normalized_cooldown = float(cooldown_seconds)
        if normalized_cooldown < 0:
            raise ValueError("cooldown_seconds cannot be negative")
        self.service = service or TTSService()
        self.enabled = bool(enabled)
        self.cooldown_seconds = normalized_cooldown
        self._last_spoken: dict[tuple[int, str], datetime] = {}
        self._cooldown_lock = Lock()

    def send(self, message: AlertMessage) -> AlertResult:
        if not isinstance(message, AlertMessage):
            raise TypeError("message must be an AlertMessage")
        if not self.enabled:
            return AlertResult(
                event_id=message.event_id,
                adapter=self.name,
                status=AlertStatus.SKIPPED,
                timestamp=self._timestamp(),
                error_code="TTS_DISABLED",
                error_message="TTS alert adapter is disabled",
            )

        existing = self.existing(message.event_id)
        if existing is not None:
            return existing

        now = self.clock()
        key = (message.track_id, message.alert_type.value)
        with self._cooldown_lock:
            previous = self._last_spoken.get(key)
            if (
                previous is not None
                and now - previous
                < timedelta(seconds=self.cooldown_seconds)
            ):
                return AlertResult(
                    event_id=message.event_id,
                    adapter=self.name,
                    status=AlertStatus.SKIPPED,
                    timestamp=self._timestamp(),
                    error_code="TTS_COOLDOWN",
                    error_message="alert is inside the TTS cooldown window",
                )

        try:
            self.service.speak(message.message)
        except TTSServiceError as exc:
            return AlertResult(
                event_id=message.event_id,
                adapter=self.name,
                status=AlertStatus.FAILED,
                timestamp=self._timestamp(),
                error_code=exc.code,
                error_message=str(exc),
            )
        except Exception as exc:
            return self.failed(message.event_id, exc)

        with self._cooldown_lock:
            self._last_spoken[key] = now
        return self.delivered(message.event_id)
