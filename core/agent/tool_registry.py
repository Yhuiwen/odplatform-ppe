"""Immutable registry and executor for the four frozen P8-6 read-only tools."""

from __future__ import annotations

import hashlib
import time
from dataclasses import replace
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping

from core.agent.permissions import (
    ToolPermissionError,
    ToolPermissionPolicy,
)
from core.schemas.agent import (
    AGENT_TOOL_REGISTRY_VERSION,
    AgentCapability,
    AgentTool,
    AgentToolDescriptor,
    ToolAuditMetadata,
    ToolEffect,
    ToolError,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
    sha256_arguments,
)

__all__ = [
    "STATIC_TOOL_DESCRIPTORS",
    "ToolExecutionError",
    "ToolRegistry",
    "ToolRegistryError",
]

_TOOL_ORDER = (
    "get_safety_summary",
    "get_event_statistics",
    "get_event_details",
    "generate_safety_report",
)

_SHARED_SUMMARY_INPUTS = (
    "start_at",
    "end_at",
    "event_type",
    "status",
    "track_id",
)

_STATIC_DESCRIPTOR_VALUES = MappingProxyType(
    {
        "get_safety_summary": {
            "description": (
                "Return a bounded deterministic safety summary for one "
                "reporting interval."
            ),
            "input_schema": _SHARED_SUMMARY_INPUTS,
            "output_schema": (
                "metadata",
                "observed_facts",
                "calculated_metrics",
                "unavailable_fields",
            ),
            "required_capabilities": (AgentCapability.SAFETY_READ,),
        },
        "get_event_statistics": {
            "description": (
                "Return read-only aggregate event statistics for one "
                "reporting interval."
            ),
            "input_schema": _SHARED_SUMMARY_INPUTS,
            "output_schema": (
                "total_count",
                "by_type",
                "by_status",
                "by_source_ref",
                "by_day",
                "earliest_at",
                "latest_at",
            ),
            "required_capabilities": (AgentCapability.STATISTICS_READ,),
        },
        "get_event_details": {
            "description": (
                "Return bounded persisted event metadata for verification or "
                "drill-down."
            ),
            "input_schema": (
                "event_id",
                "start_at",
                "end_at",
                "event_type",
                "status",
                "track_id",
                "limit",
                "offset",
            ),
            "output_schema": ("events", "total_count"),
            "required_capabilities": (AgentCapability.EVENTS_READ,),
        },
        "generate_safety_report": {
            "description": (
                "Generate a grounded safety report through the existing "
                "Phase 8 report service."
            ),
            "input_schema": _SHARED_SUMMARY_INPUTS,
            "output_schema": (
                "status",
                "generation_path",
                "degraded",
                "report",
            ),
            "required_capabilities": (AgentCapability.REPORTS_GENERATE,),
        },
    }
)


def _descriptor(tool_name: str) -> AgentToolDescriptor:
    values = _STATIC_DESCRIPTOR_VALUES[tool_name]
    return AgentToolDescriptor(
        tool_name=tool_name,
        tool_version="1.0.0",
        description=values["description"],
        effect=ToolEffect.READ_ONLY,
        input_schema=values["input_schema"],
        output_schema=values["output_schema"],
        required_capabilities=values["required_capabilities"],
        timeout_seconds=30.0,
        max_calls_per_request=1,
        enabled=True,
    )


STATIC_TOOL_DESCRIPTORS = tuple(
    _descriptor(tool_name) for tool_name in _TOOL_ORDER
)
_STATIC_BY_NAME = MappingProxyType(
    {descriptor.tool_name: descriptor for descriptor in STATIC_TOOL_DESCRIPTORS}
)


class ToolRegistryError(RuntimeError):
    """A registry contract failure that occurs before tool execution."""

    def __init__(self, code: str, message: str) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message
        super().__init__(message)


class ToolExecutionError(RuntimeError):
    """A handler-owned failure with a bounded public code."""

    def __init__(self, code: str, message: str) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message
        super().__init__(message)


class ToolRegistry:
    """An immutable registry containing exactly the frozen read-only tools."""

    version = AGENT_TOOL_REGISTRY_VERSION

    def __init__(
        self,
        tools: tuple[AgentTool, ...],
        *,
        policy: ToolPermissionPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(tools, tuple):
            raise TypeError("tools must be a tuple")
        if not tools:
            raise ToolRegistryError(
                "REGISTRY_INCOMPLETE",
                "the static registry must contain the frozen tool allowlist",
            )

        by_name: dict[str, AgentTool] = {}
        for tool in tools:
            if not isinstance(tool, AgentTool):
                raise ToolRegistryError(
                    "INVALID_TOOL_CONTRACT",
                    "registry entries must be AgentTool values",
                )
            name = tool.tool_name
            if name not in _STATIC_BY_NAME:
                raise ToolRegistryError(
                    "TOOL_NOT_ALLOWED",
                    "dynamic or unknown tools are not permitted",
                )
            if name in by_name:
                raise ToolRegistryError(
                    "DUPLICATE_TOOL",
                    "duplicate tool registration is not permitted",
                )
            if tool.descriptor != _STATIC_BY_NAME[name]:
                raise ToolRegistryError(
                    "TOOL_DESCRIPTOR_MISMATCH",
                    "tool descriptors must match the frozen static contract",
                )
            by_name[name] = tool

        if set(by_name) != set(_TOOL_ORDER):
            raise ToolRegistryError(
                "REGISTRY_INCOMPLETE",
                "the static registry must contain exactly four frozen tools",
            )

        self._tools = MappingProxyType(by_name)
        self._policy = policy or ToolPermissionPolicy()
        if not isinstance(self._policy, ToolPermissionPolicy):
            raise TypeError("policy must be a ToolPermissionPolicy")
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        if not callable(self._clock):
            raise TypeError("clock must be callable")
        self._monotonic = monotonic or time.perf_counter
        if not callable(self._monotonic):
            raise TypeError("monotonic must be callable")

    @property
    def tool_names(self) -> tuple[str, ...]:
        """Return the stable frozen registry order."""

        return _TOOL_ORDER

    @property
    def descriptors(self) -> tuple[AgentToolDescriptor, ...]:
        return STATIC_TOOL_DESCRIPTORS

    def resolve(self, tool_name: str, tool_version: str = "1.0.0") -> AgentTool:
        """Resolve one exact allowlisted tool name and version."""

        if not isinstance(tool_name, str):
            raise TypeError("tool_name must be a string")
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolRegistryError(
                "TOOL_NOT_FOUND",
                "tool is not in the static read-only allowlist",
            )
        if tool.tool_version != tool_version:
            raise ToolRegistryError(
                "TOOL_VERSION_MISMATCH",
                "tool version does not match the frozen descriptor",
            )
        return tool

    def execute(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Authorize and execute one static read-only tool."""

        tool = self.resolve(tool_name)
        if not isinstance(arguments, Mapping):
            return self._error_result(
                tool=tool,
                context=context,
                arguments={},
                code="INVALID_ARGUMENTS",
                message="tool arguments must be a mapping",
                duration_ms=0.0,
            )
        if not isinstance(context, ToolExecutionContext):
            raise TypeError("context must be a ToolExecutionContext")

        started = self._monotonic()
        if not tool.descriptor.enabled:
            return self._error_result(
                tool=tool,
                context=context,
                arguments=arguments,
                code="TOOL_DISABLED",
                message="tool is disabled by the frozen registry",
                duration_ms=self._duration_ms(started),
            )

        try:
            decision = self._policy.authorize(
                context,
                tool.descriptor.required_capabilities,
            )
        except ToolPermissionError as exc:
            return self._error_result(
                tool=tool,
                context=context,
                arguments=arguments,
                code=exc.code,
                message=exc.message,
                duration_ms=self._duration_ms(started),
                status=ToolExecutionStatus.REFUSED,
            )

        invalid_field = self._invalid_argument_field(
            arguments,
            tool.descriptor.input_schema,
        )
        if invalid_field is not None:
            return self._error_result(
                tool=tool,
                context=context,
                arguments=arguments,
                code="FORBIDDEN_ARGUMENT",
                message=(
                    "tool arguments contain a field outside the read-only "
                    "allowlist"
                ),
                duration_ms=self._duration_ms(started),
                status=ToolExecutionStatus.REFUSED,
            )

        effective_context = replace(
            context,
            capabilities=decision.granted_capabilities,
        )
        try:
            result = tool.handler(dict(arguments), effective_context)
        except ToolExecutionError as exc:
            return self._error_result(
                tool=tool,
                context=effective_context,
                arguments=arguments,
                code=exc.code,
                message=exc.message,
                duration_ms=self._duration_ms(started),
            )
        except Exception:
            return self._error_result(
                tool=tool,
                context=effective_context,
                arguments=arguments,
                code="TOOL_ERROR",
                message="tool execution failed safely",
                duration_ms=self._duration_ms(started),
            )

        if not isinstance(result, ToolResult):
            raise ToolRegistryError(
                "INVALID_TOOL_RESULT",
                "tool handler must return a ToolResult",
            )
        if (
            result.tool_name != tool.tool_name
            or result.tool_version != tool.tool_version
        ):
            raise ToolRegistryError(
                "TOOL_RESULT_MISMATCH",
                "tool result identity does not match the registry descriptor",
            )

        duration_ms = self._duration_ms(started)
        audit = self._audit_metadata(
            tool=tool,
            context=effective_context,
            arguments=arguments,
            result=result,
            duration_ms=duration_ms,
        )
        return replace(
            result,
            duration_ms=duration_ms,
            audit_metadata=audit,
        )

    def _error_result(
        self,
        *,
        tool: AgentTool,
        context: ToolExecutionContext,
        arguments: Mapping[str, Any],
        code: str,
        message: str,
        duration_ms: float,
        status: ToolExecutionStatus = ToolExecutionStatus.ERROR,
    ) -> ToolResult:
        if not isinstance(context, ToolExecutionContext):
            raise TypeError("context must be a ToolExecutionContext")
        safe_error = ToolError(code=code, message=message)
        provisional = ToolResult(
            tool_name=tool.tool_name,
            tool_version=tool.tool_version,
            status=status,
            data={},
            safe_error=safe_error,
        )
        audit = self._audit_metadata(
            tool=tool,
            context=context,
            arguments=arguments,
            result=provisional,
            duration_ms=duration_ms,
        )
        return replace(
            provisional,
            duration_ms=duration_ms,
            audit_metadata=audit,
        )

    def _audit_metadata(
        self,
        *,
        tool: AgentTool,
        context: ToolExecutionContext,
        arguments: Mapping[str, Any],
        result: ToolResult,
        duration_ms: float,
    ) -> ToolAuditMetadata:
        arguments_sha256 = sha256_arguments(arguments)
        audit_id = "AUD-" + hashlib.sha256(
            (
                f"{context.request_id}:{tool.tool_name}:"
                f"{tool.tool_version}:{arguments_sha256}"
            ).encode("utf-8")
        ).hexdigest()[:16]
        report_generation_status = result.data.get(
            "generation_path"
        )
        fallback_used = bool(result.data.get("degraded", False))
        return ToolAuditMetadata(
            audit_id=audit_id,
            request_id=context.request_id,
            timestamp=self._clock().astimezone(timezone.utc).isoformat(
                timespec="seconds"
            ).replace("+00:00", "Z"),
            principal_ref=context.principal_ref,
            role_ref=context.role,
            tool_name=tool.tool_name,
            tool_version=tool.tool_version,
            arguments_sha256=arguments_sha256,
            policy_version=self._policy.version,
            registry_version=self.version,
            outcome=result.status,
            safe_error_code=(
                None if result.safe_error is None else result.safe_error.code
            ),
            row_count=result.row_count,
            duration_ms=duration_ms,
            report_generation_status=(
                None
                if report_generation_status is None
                else str(report_generation_status)
            ),
            fallback_used=fallback_used,
        )

    @staticmethod
    def _invalid_argument_field(
        arguments: Mapping[str, Any],
        allowed_fields: tuple[str, ...],
    ) -> str | None:
        allowed = set(allowed_fields)
        for key in arguments:
            if not isinstance(key, str) or key not in allowed:
                return str(key)
        return None

    def _duration_ms(self, started: float) -> float:
        elapsed = (self._monotonic() - started) * 1000.0
        return max(0.0, round(elapsed, 6))
