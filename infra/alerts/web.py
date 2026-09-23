"""In-process web alert adapter."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from threading import Lock
from typing import Callable

from core.schemas.alerts import AlertMessage, AlertResult
from infra.alerts.base import BaseAlertAdapter


class WebAlertAdapter(BaseAlertAdapter):
    """Publish alerts to an observable bounded in-process inbox."""

    name = "web"

    def __init__(
        self,
        *,
        publisher: Callable[[AlertMessage], None] | None = None,
        max_history: int = 200,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(clock=clock)
        if isinstance(max_history, bool) or not isinstance(max_history, int):
            raise TypeError("max_history must be an integer")
        if max_history <= 0:
            raise ValueError("max_history must be positive")
        self.publisher = publisher
        self._history: deque[AlertMessage] = deque(maxlen=max_history)
        self._history_lock = Lock()

    def send(self, message: AlertMessage) -> AlertResult:
        if not isinstance(message, AlertMessage):
            raise TypeError("message must be an AlertMessage")
        existing = self.existing(message.event_id)
        if existing is not None:
            return existing
        try:
            if self.publisher is not None:
                self.publisher(message)
            with self._history_lock:
                self._history.append(message)
        except Exception as exc:
            return self.failed(message.event_id, exc)
        return self.delivered(message.event_id)

    def history(self) -> tuple[AlertMessage, ...]:
        with self._history_lock:
            return tuple(reversed(self._history))
