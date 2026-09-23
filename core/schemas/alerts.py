"""Model-independent alert contracts for the Phase 7 delivery boundary."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import normalize_utc_timestamp

__all__ = [
    "AlertMessage",
    "AlertResult",
    "AlertStatus",
]


class AlertStatus(str, Enum):
    """Stable adapter delivery state."""

    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"


def _normalize_optional_snapshot(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("snapshot must be a relative POSIX path or None")
    candidate = value.strip()
    path = PurePosixPath(candidate)
    if (
        path.is_absolute()
        or "\\" in candidate
        or re.match(r"^[A-Za-z]:/", candidate) is not None
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("snapshot must be a safe relative POSIX path")
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class AlertMessage:
    """One alert request shared by all adapters."""

    event_id: str
    timestamp: str
    track_id: int
    alert_type: ComplianceEventType
    confidence: float
    snapshot: str | None
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id cannot be empty")
        object.__setattr__(self, "event_id", self.event_id.strip())
        object.__setattr__(
            self,
            "timestamp",
            normalize_utc_timestamp(self.timestamp),
        )
        if isinstance(self.track_id, bool) or not isinstance(self.track_id, int):
            raise TypeError("track_id must be an integer")
        if self.track_id < 0:
            raise ValueError("track_id cannot be negative")
        try:
            alert_type = ComplianceEventType(self.alert_type)
        except ValueError as exc:
            raise ValueError("alert_type must be a supported event type") from exc
        object.__setattr__(self, "alert_type", alert_type)
        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence, (int, float)
        ):
            raise TypeError("confidence must be numeric")
        confidence = float(self.confidence)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be finite and between 0 and 1")
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(
            self,
            "snapshot",
            _normalize_optional_snapshot(self.snapshot),
        )
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message cannot be empty")
        object.__setattr__(self, "message", self.message.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "track_id": self.track_id,
            "alert_type": self.alert_type.value,
            "confidence": self.confidence,
            "snapshot": self.snapshot,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class AlertResult:
    """One adapter delivery result; failure is never reported as success."""

    event_id: str
    adapter: str
    status: AlertStatus
    timestamp: str
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id cannot be empty")
        if not isinstance(self.adapter, str) or not self.adapter.strip():
            raise ValueError("adapter cannot be empty")
        object.__setattr__(self, "event_id", self.event_id.strip())
        object.__setattr__(self, "adapter", self.adapter.strip())
        try:
            status = AlertStatus(self.status)
        except ValueError as exc:
            raise ValueError("status must be delivered, failed or skipped") from exc
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "timestamp",
            normalize_utc_timestamp(self.timestamp),
        )
        if self.error_code is not None and (
            not isinstance(self.error_code, str) or not self.error_code.strip()
        ):
            raise ValueError("error_code must be a non-empty string or None")
        if self.error_message is not None and (
            not isinstance(self.error_message, str)
            or not self.error_message.strip()
        ):
            raise ValueError("error_message must be a non-empty string or None")
        if status is AlertStatus.DELIVERED and (
            self.error_code is not None or self.error_message is not None
        ):
            raise ValueError("delivered alerts cannot include an error")
        if status is AlertStatus.FAILED and self.error_code is None:
            raise ValueError("failed alerts require an error_code")

    @property
    def delivered(self) -> bool:
        return self.status is AlertStatus.DELIVERED

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "adapter": self.adapter,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }
