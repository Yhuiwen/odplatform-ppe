"""Append-only Agent audit service with bounded metadata sanitization."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping

from core.schemas.agent import (
    AGENT_POLICY_VERSION,
    AGENT_TOOL_REGISTRY_VERSION,
    AgentAuditStatus,
    AgentIntent,
    AgentPlan,
    AgentRole,
    AuditEvent,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
    sha256_arguments,
)
from infra.storage.agent_audit_store import (
    AgentAuditStore,
    AgentAuditStoreError,
    InMemoryAgentAuditStore,
)

__all__ = [
    "AgentAuditError",
    "AgentAuditService",
    "derive_plan_id",
    "sanitize_audit_metadata",
]

_SAFE_METADATA_FIELDS = frozenset(
    {
        "duration_ms",
        "fallback_used",
        "policy_version",
        "registry_version",
        "report_generation_status",
        "row_count",
        "tool_version",
    }
)
_SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_SAFE_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,79}$")


class AgentAuditError(RuntimeError):
    """A bounded audit failure that prevents successful response release."""

    def __init__(self, code: str, message: str) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message
        super().__init__(message)


def _safe_metadata_value(key: str, value: Any) -> Any:
    if key not in _SAFE_METADATA_FIELDS:
        return None
    if key == "duration_ms":
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
        ):
            return None
        return float(value)
    if key == "row_count":
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            return None
        return value
    if key == "fallback_used":
        return value if isinstance(value, bool) else None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if key == "tool_version":
        if _SAFE_VERSION.fullmatch(normalized) is None:
            return None
        return normalized
    if key == "policy_version":
        return (
            normalized if normalized == AGENT_POLICY_VERSION else None
        )
    if key == "registry_version":
        return (
            normalized
            if normalized == AGENT_TOOL_REGISTRY_VERSION
            else None
        )
    if key == "report_generation_status":
        if _SAFE_CODE.fullmatch(normalized) is None:
            return None
        return normalized
    if not normalized or _SAFE_REFERENCE.fullmatch(normalized) is None:
        return None
    return normalized


def sanitize_audit_metadata(
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Keep only bounded, non-sensitive allowlisted audit metadata values."""

    if metadata is None:
        return {}
    if not isinstance(metadata, Mapping):
        raise AgentAuditError(
            "INVALID_METADATA",
            "audit metadata must be a mapping or None",
        )
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str) or key not in _SAFE_METADATA_FIELDS:
            continue
        safe_value = _safe_metadata_value(key, value)
        if safe_value is not None:
            sanitized[key] = safe_value
    return sanitized


def derive_plan_id(plan: AgentPlan) -> str:
    """Derive a deterministic opaque plan identity without exposing arguments."""

    if not isinstance(plan, AgentPlan):
        raise AgentAuditError(
            "INVALID_PLAN",
            "plan_id derivation requires an AgentPlan",
        )
    payload = {
        "schema_version": plan.schema_version,
        "intent": plan.intent.value,
        "tool_name": plan.tool_name,
        "tool_version": plan.tool_version,
        "arguments_sha256": sha256_arguments(plan.arguments),
        "question_sha256": plan.question_sha256,
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return "PLAN-" + digest[:16]


class AgentAuditService:
    """Record append-only Agent events without retaining sensitive payloads."""

    def __init__(
        self,
        store: AgentAuditStore | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if store is not None and not isinstance(store, AgentAuditStore):
            raise TypeError(
                "store must implement the append-only AgentAuditStore contract"
            )
        self.store = store or InMemoryAgentAuditStore()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        if not callable(self._clock):
            raise TypeError("clock must be callable")

    def record_event(
        self,
        *,
        request_id: str,
        principal_ref: str,
        role_ref: AgentRole | str,
        intent: AgentIntent | str,
        plan_id: str,
        tools_requested: Iterable[str],
        execution_status: AgentAuditStatus | str,
        failure_status: str | None = None,
        question_sha256: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> AuditEvent:
        """Validate, sanitize and append one audit event."""

        try:
            normalized_tools = tuple(tools_requested)
        except TypeError as exc:
            raise AgentAuditError(
                "INVALID_AUDIT_EVENT",
                "tools_requested must be an iterable of tool names",
            ) from exc
        normalized_metadata = sanitize_audit_metadata(metadata)
        normalized_timestamp = self._normalize_timestamp(timestamp)
        try:
            audit_id = self._audit_id(
                request_id=request_id,
                timestamp=normalized_timestamp,
                principal_ref=principal_ref,
                role_ref=role_ref,
                intent=intent,
                plan_id=plan_id,
                tools_requested=normalized_tools,
                execution_status=execution_status,
                failure_status=failure_status,
                question_sha256=question_sha256,
                safe_metadata=normalized_metadata,
            )
        except (TypeError, ValueError) as exc:
            raise AgentAuditError(
                "INVALID_AUDIT_EVENT",
                "audit event fields are not deterministically serializable",
            ) from exc
        try:
            event = AuditEvent(
                audit_id=audit_id,
                request_id=request_id,
                timestamp=normalized_timestamp,
                principal_ref=principal_ref,
                role_ref=role_ref,
                intent=intent,
                plan_id=plan_id,
                tools_requested=normalized_tools,
                execution_status=execution_status,
                failure_status=failure_status,
                question_sha256=question_sha256,
                safe_metadata=normalized_metadata,
            )
        except (TypeError, ValueError) as exc:
            raise AgentAuditError(
                "INVALID_AUDIT_EVENT",
                "audit event does not satisfy the frozen contract",
            ) from exc
        try:
            self.store.append(event)
        except AgentAuditStoreError as exc:
            raise AgentAuditError(
                "AUDIT_UNAVAILABLE",
                "append-only audit storage rejected the event",
            ) from exc
        return event

    def record_plan(
        self,
        plan: AgentPlan,
        context: ToolExecutionContext,
        *,
        execution_status: AgentAuditStatus | str = AgentAuditStatus.PLANNED,
        failure_status: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> AuditEvent:
        """Record one planner output without storing its arguments."""

        if not isinstance(plan, AgentPlan):
            raise AgentAuditError(
                "INVALID_PLAN",
                "plan audit requires a validated AgentPlan",
            )
        if not isinstance(context, ToolExecutionContext):
            raise AgentAuditError(
                "INVALID_CONTEXT",
                "plan audit requires a validated ToolExecutionContext",
            )
        return self.record_event(
            request_id=context.request_id,
            principal_ref=context.principal_ref,
            role_ref=context.role,
            intent=plan.intent,
            plan_id=derive_plan_id(plan),
            tools_requested=(plan.tool_name,),
            execution_status=execution_status,
            failure_status=failure_status,
            question_sha256=plan.question_sha256,
            metadata=metadata,
            timestamp=timestamp,
        )

    def record_tool_result(
        self,
        result: ToolResult,
        context: ToolExecutionContext,
        *,
        intent: AgentIntent | str,
        plan_id: str,
        metadata: Mapping[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> AuditEvent:
        """Record a bounded result projection without storing tool data."""

        if not isinstance(result, ToolResult):
            raise AgentAuditError(
                "INVALID_TOOL_RESULT",
                "audit requires a validated ToolResult",
            )
        if not isinstance(context, ToolExecutionContext):
            raise AgentAuditError(
                "INVALID_CONTEXT",
                "tool audit requires a validated ToolExecutionContext",
            )
        if result.status is ToolExecutionStatus.SUCCESS:
            status = AgentAuditStatus.SUCCESS
            failure_status = None
        elif result.status is ToolExecutionStatus.REFUSED:
            status = AgentAuditStatus.REFUSED
            failure_status = (
                None if result.safe_error is None else result.safe_error.code
            )
        else:
            status = AgentAuditStatus.FAILURE
            failure_status = (
                "TOOL_ERROR"
                if result.safe_error is None
                else result.safe_error.code
            )

        result_metadata = {
            "duration_ms": result.duration_ms,
            "row_count": result.row_count,
            "tool_version": result.tool_version,
        }
        if result.audit_metadata is not None:
            result_metadata.update(
                {
                    "policy_version": result.audit_metadata.policy_version,
                    "registry_version": result.audit_metadata.registry_version,
                    "report_generation_status": (
                        result.audit_metadata.report_generation_status
                    ),
                    "fallback_used": result.audit_metadata.fallback_used,
                }
            )
        if metadata is not None:
            result_metadata.update(metadata)

        return self.record_event(
            request_id=context.request_id,
            principal_ref=context.principal_ref,
            role_ref=context.role,
            intent=intent,
            plan_id=plan_id,
            tools_requested=(result.tool_name,),
            execution_status=status,
            failure_status=failure_status,
            metadata=result_metadata,
            timestamp=timestamp,
        )

    def record_unknown_tool(
        self,
        *,
        request_id: str,
        principal_ref: str,
        role_ref: AgentRole | str,
        intent: AgentIntent | str,
        tool_name: str,
        question_sha256: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> AuditEvent:
        """Record an unknown-tool attempt as a bounded failure event."""

        try:
            normalized_intent = AgentIntent(intent)
        except ValueError as exc:
            raise AgentAuditError(
                "INVALID_AUDIT_EVENT",
                "unknown-tool audit requires a supported AgentIntent",
            ) from exc
        plan_id = "PLAN-" + hashlib.sha256(
            (
                f"{request_id}:{normalized_intent.value}:"
                f"{tool_name}:{question_sha256 or ''}"
            ).encode("utf-8")
        ).hexdigest()[:16]
        return self.record_event(
            request_id=request_id,
            principal_ref=principal_ref,
            role_ref=role_ref,
            intent=normalized_intent,
            plan_id=plan_id,
            tools_requested=(tool_name,),
            execution_status=AgentAuditStatus.UNKNOWN_TOOL,
            failure_status="TOOL_NOT_FOUND",
            question_sha256=question_sha256,
            metadata=metadata,
            timestamp=timestamp,
        )

    def events(self) -> tuple[AuditEvent, ...]:
        """Return the append-order audit snapshot."""

        return self.store.events()

    def serialize(self) -> tuple[str, ...]:
        """Return deterministic canonical JSON records in append order."""

        return tuple(event.to_json() for event in self.events())

    def _normalize_timestamp(self, timestamp: str | None) -> str:
        if timestamp is None:
            current = self._clock()
            if not isinstance(current, datetime) or current.tzinfo is None:
                raise AgentAuditError(
                    "INVALID_TIMESTAMP",
                    "audit clock must return a timezone-aware datetime",
                )
            return current.astimezone(timezone.utc).isoformat(
                timespec="seconds"
            ).replace("+00:00", "Z")
        if not isinstance(timestamp, str) or not timestamp.strip():
            raise AgentAuditError(
                "INVALID_TIMESTAMP",
                "timestamp must be a non-empty normalized string",
            )
        return timestamp.strip()

    @staticmethod
    def _audit_id(**fields: Any) -> str:
        digest = hashlib.sha256(
            json.dumps(
                fields,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        return "AUD-" + digest[:16]
