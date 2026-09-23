"""Alert adapter protocol and contracts."""

from core.alerts.interfaces import AlertAdapter
from core.schemas.alerts import AlertMessage, AlertResult, AlertStatus

__all__ = ["AlertAdapter", "AlertMessage", "AlertResult", "AlertStatus"]
