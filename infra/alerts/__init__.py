"""Built-in alert adapters."""

from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter

__all__ = ["ConsoleAlertAdapter", "WebAlertAdapter"]
