"""Common adapter protocol used by the alert service."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.schemas.alerts import AlertMessage, AlertResult


@runtime_checkable
class AlertAdapter(Protocol):
    """Deliver one alert without changing the shared message contract."""

    name: str

    def send(self, message: AlertMessage) -> AlertResult:
        ...
