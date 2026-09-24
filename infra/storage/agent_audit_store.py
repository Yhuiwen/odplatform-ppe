"""Append-only in-memory storage contract for Agent audit events."""

from __future__ import annotations

import threading
from typing import Protocol, runtime_checkable

from core.schemas.agent import AuditEvent

__all__ = [
    "AgentAuditStore",
    "AgentAuditStoreError",
    "InMemoryAgentAuditStore",
]


class AgentAuditStoreError(RuntimeError):
    """Raised when an append-only audit store cannot accept an event."""

    code = "AUDIT_STORE_ERROR"


@runtime_checkable
class AgentAuditStore(Protocol):
    """Minimal append-only store abstraction."""

    def append(self, event: AuditEvent) -> None:
        """Append one validated audit event."""

    def events(self) -> tuple[AuditEvent, ...]:
        """Return an immutable snapshot in append order."""


class InMemoryAgentAuditStore:
    """Thread-safe append-only in-memory audit store.

    This store intentionally exposes no update, delete, clear or persistence
    method. Durable storage belongs to a later phase.
    """

    def __init__(self) -> None:
        self._events: tuple[AuditEvent, ...] = ()
        self._lock = threading.Lock()

    def append(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            raise AgentAuditStoreError(
                "append requires a validated AuditEvent"
            )
        with self._lock:
            self._events = (*self._events, event)

    def events(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return self._events

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)
