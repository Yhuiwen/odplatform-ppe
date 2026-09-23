"""Console alert adapter."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Callable

from core.schemas.alerts import AlertMessage, AlertResult
from infra.alerts.base import BaseAlertAdapter


class ConsoleAlertAdapter(BaseAlertAdapter):
    """Write deterministic JSON alert lines to an injectable console sink."""

    name = "console"

    def __init__(
        self,
        *,
        sink: Callable[[str], None] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(clock=clock)
        self.sink = sink or print

    def send(self, message: AlertMessage) -> AlertResult:
        if not isinstance(message, AlertMessage):
            raise TypeError("message must be an AlertMessage")
        existing = self.existing(message.event_id)
        if existing is not None:
            return existing
        try:
            self.sink(
                json.dumps(
                    message.to_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        except Exception as exc:
            return self.failed(message.event_id, exc)
        return self.delivered(message.event_id)
