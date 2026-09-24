"""Phase 8 Basic Safety Agent contracts.

These schemas are provider-independent and contain no network, filesystem,
tool execution or reasoning implementation.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol

__all__ = [
    "AGENT_AUDIT_VERSION",
    "AGENT_PLAN_SCHEMA_VERSION",
    "AGENT_PLAN_CANDIDATE_SCHEMA_VERSION",
    "AGENT_POLICY_VERSION",
    "AGENT_REQUEST_SCHEMA_VERSION",
    "AGENT_RESULT_SCHEMA_VERSION",
    "AGENT_TOOL_AUDIT_VERSION",
    "AGENT_TOOL_REGISTRY_VERSION",
    "AgentCapability",
    "AgentAuditStatus",
    "AgentIntent",
    "AgentOutcome",
    "AgentPlan",
    "AgentPlanCandidate",
    "AgentPlanCandidateReason",
    "AgentRequest",
    "AgentResult",
    "AgentRole",
    "AgentTool",
    "AgentToolDescriptor",
    "AgentToolHandler",
    "AuditEvent",
    "ToolAuditMetadata",
    "ToolEffect",
    "ToolError",
    "ToolExecutionContext",
    "ToolExecutionStatus",
    "ToolResult",
]

AGENT_REQUEST_SCHEMA_VERSION = "phase8-agent-request-v1"
AGENT_RESULT_SCHEMA_VERSION = "phase8-agent-result-v1"
AGENT_PLAN_SCHEMA_VERSION = "phase8-agent-plan-v1"
AGENT_PLAN_CANDIDATE_SCHEMA_VERSION = "phase8-agent-plan-candidate-v1"
AGENT_TOOL_REGISTRY_VERSION = "phase8-agent-tool-registry-v1"
AGENT_POLICY_VERSION = "phase8-agent-policy-v1"
AGENT_AUDIT_VERSION = "phase8-agent-audit-v1"
AGENT_TOOL_AUDIT_VERSION = "phase8-agent-tool-audit-v1"

_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,79}$")
_SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_SAFE_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")


class AgentCapability(str, Enum):
    """Frozen read/report capabilities; mutation capabilities do not exist."""

    SAFETY_READ = "safety:read"
    STATISTICS_READ = "statistics:read"
    EVENTS_READ = "events:read"
    REPORTS_GENERATE = "reports:generate"
    PROVIDER_INVOKE = "provider:invoke"


class AgentRole(str, Enum):
    """Project-owned principal roles for the first Agent implementation."""

    SAFETY_VIEWER = "safety_viewer"
    EVENT_VIEWER = "event_viewer"
    SAFETY_REPORTER = "safety_reporter"
    SYSTEM = "system"


class AgentOutcome(str, Enum):
    """Frozen Agent-facing outcome vocabulary."""

    ANSWERED = "ANSWERED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    TOOL_ERROR = "TOOL_ERROR"
    REFUSED = "REFUSED"
    AUDIT_UNAVAILABLE = "AUDIT_UNAVAILABLE"


class AgentIntent(str, Enum):
    """Frozen deterministic planner intent vocabulary."""

    SAFETY_SUMMARY = "SAFETY_SUMMARY"
    EVENT_STATISTICS = "EVENT_STATISTICS"
    EVENT_DETAIL = "EVENT_DETAIL"
    SAFETY_REPORT = "SAFETY_REPORT"
    UNKNOWN = "UNKNOWN"
    FORBIDDEN_REQUEST = "FORBIDDEN_REQUEST"


class AgentPlanCandidateReason(str, Enum):
    """Closed reason vocabulary for an untrusted plan candidate."""

    SUMMARY_REQUEST = "SUMMARY_REQUEST"
    STATISTICS_REQUEST = "STATISTICS_REQUEST"
    EVENT_DETAIL_REQUEST = "EVENT_DETAIL_REQUEST"
    REPORT_REQUEST = "REPORT_REQUEST"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


class AgentAuditStatus(str, Enum):
    """Frozen append-only Agent audit execution status vocabulary."""

    PLANNED = "PLANNED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REFUSED = "REFUSED"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"


class ToolEffect(str, Enum):
    """Only read-only tools are valid in P8-6."""

    READ_ONLY = "READ_ONLY"


class ToolExecutionStatus(str, Enum):
    """P8-6.1 execution result status."""

    SUCCESS = "SUCCESS"
    REFUSED = "REFUSED"
    ERROR = "ERROR"


def _safe_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if _SAFE_REFERENCE.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must use a safe opaque reference")
    return normalized


def _safe_code(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if _SAFE_CODE.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be a safe uppercase error code")
    return normalized


def _safe_result_reference(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if (
        len(normalized) > 300
        or normalized.startswith("/")
        or "\\" in normalized
        or re.match(r"^[A-Za-z]:/", normalized) is not None
    ):
        raise ValueError(f"{field_name} must be a relative opaque reference")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{field_name} must not contain unsafe path segments")
    return normalized


@dataclass(frozen=True, slots=True)
class ToolError:
    """One bounded, non-secret tool failure."""

    code: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _safe_code(self.code, "code"))
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a non-empty string")
        message = self.message.strip()
        if len(message) > 300:
            raise ValueError("message must be at most 300 characters")
        object.__setattr__(self, "message", message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True, slots=True)
class ToolExecutionContext:
    """Execution identity passed to one static tool handler."""

    request_id: str
    principal_ref: str
    role: AgentRole | str
    capabilities: frozenset[AgentCapability | str] = frozenset()
    deadline: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _safe_text(self.request_id, "request_id"),
        )
        object.__setattr__(
            self,
            "principal_ref",
            _safe_text(self.principal_ref, "principal_ref"),
        )
        try:
            role = AgentRole(self.role)
        except ValueError as exc:
            raise ValueError("role must be a supported AgentRole") from exc
        object.__setattr__(self, "role", role)

        normalized_capabilities: set[AgentCapability] = set()
        for capability in self.capabilities:
            try:
                normalized_capabilities.add(AgentCapability(capability))
            except ValueError as exc:
                raise ValueError(
                    "capabilities must contain supported read/report values"
                ) from exc
        object.__setattr__(
            self,
            "capabilities",
            frozenset(normalized_capabilities),
        )

        if self.deadline is not None:
            if (
                isinstance(self.deadline, bool)
                or not isinstance(self.deadline, (int, float))
            ):
                raise TypeError("deadline must be numeric or None")
            normalized_deadline = float(self.deadline)
            if not math.isfinite(normalized_deadline):
                raise ValueError("deadline must be finite")
            object.__setattr__(self, "deadline", normalized_deadline)


@dataclass(frozen=True, slots=True)
class AgentRequest:
    """One validated Agent request with trusted execution identity."""

    request_id: str
    principal_ref: str
    role: AgentRole | str
    question: str
    requested_period: Mapping[str, Any] | None = None
    filters: Mapping[str, Any] | None = None
    capabilities: frozenset[AgentCapability | str] = frozenset()
    schema_version: str = AGENT_REQUEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_REQUEST_SCHEMA_VERSION:
            raise ValueError("unsupported request schema_version")
        object.__setattr__(
            self,
            "request_id",
            _safe_text(self.request_id, "request_id"),
        )
        object.__setattr__(
            self,
            "principal_ref",
            _safe_text(self.principal_ref, "principal_ref"),
        )
        try:
            role = AgentRole(self.role)
        except ValueError as exc:
            raise ValueError("role must be a supported AgentRole") from exc
        object.__setattr__(self, "role", role)

        if not isinstance(self.question, str):
            raise TypeError("question must be a string")
        normalized_question = " ".join(self.question.split())
        if not normalized_question:
            raise ValueError("question cannot be empty")
        if len(normalized_question.encode("utf-8")) > 2000:
            raise ValueError("question exceeds the frozen byte limit")
        object.__setattr__(self, "question", normalized_question)

        if self.requested_period is not None:
            if not isinstance(self.requested_period, Mapping):
                raise TypeError("requested_period must be a mapping or None")
            object.__setattr__(
                self,
                "requested_period",
                MappingProxyType(dict(self.requested_period)),
            )
        if self.filters is not None:
            if not isinstance(self.filters, Mapping):
                raise TypeError("filters must be a mapping or None")
            object.__setattr__(
                self,
                "filters",
                MappingProxyType(dict(self.filters)),
            )

        normalized_capabilities: set[AgentCapability] = set()
        for capability in self.capabilities:
            try:
                normalized_capabilities.add(AgentCapability(capability))
            except ValueError as exc:
                raise ValueError(
                    "capabilities must contain supported read/report values"
                ) from exc
        object.__setattr__(
            self,
            "capabilities",
            frozenset(normalized_capabilities),
        )

    def to_context(self) -> ToolExecutionContext:
        """Return the trusted context used for planning and execution."""

        return ToolExecutionContext(
            request_id=self.request_id,
            principal_ref=self.principal_ref,
            role=self.role,
            capabilities=self.capabilities,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "principal_ref": self.principal_ref,
            "role": self.role.value,
            "question": self.question,
            "requested_period": (
                None
                if self.requested_period is None
                else dict(self.requested_period)
            ),
            "filters": None if self.filters is None else dict(self.filters),
            "capabilities": sorted(
                capability.value for capability in self.capabilities
            ),
        }


@dataclass(frozen=True, slots=True)
class ToolAuditMetadata:
    """Append-only audit projection emitted for one tool execution attempt."""

    audit_id: str
    request_id: str
    timestamp: str
    principal_ref: str
    role_ref: AgentRole
    tool_name: str
    tool_version: str
    arguments_sha256: str
    policy_version: str
    registry_version: str
    outcome: ToolExecutionStatus
    safe_error_code: str | None
    row_count: int
    duration_ms: float
    report_generation_status: str | None
    fallback_used: bool
    schema_version: str = AGENT_TOOL_AUDIT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_TOOL_AUDIT_VERSION:
            raise ValueError("unsupported audit schema_version")
        object.__setattr__(
            self,
            "audit_id",
            _safe_text(self.audit_id, "audit_id"),
        )
        object.__setattr__(
            self,
            "request_id",
            _safe_text(self.request_id, "request_id"),
        )
        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty string")
        object.__setattr__(
            self,
            "principal_ref",
            _safe_text(self.principal_ref, "principal_ref"),
        )
        try:
            role_ref = AgentRole(self.role_ref)
        except ValueError as exc:
            raise ValueError("role_ref must be a supported AgentRole") from exc
        object.__setattr__(self, "role_ref", role_ref)
        object.__setattr__(
            self,
            "tool_name",
            _safe_text(self.tool_name, "tool_name"),
        )
        object.__setattr__(
            self,
            "tool_version",
            _safe_text(self.tool_version, "tool_version"),
        )
        if re.fullmatch(r"[0-9a-f]{64}", self.arguments_sha256) is None:
            raise ValueError("arguments_sha256 must be a lowercase SHA256")
        if self.policy_version != AGENT_POLICY_VERSION:
            raise ValueError("unsupported policy_version")
        if self.registry_version != AGENT_TOOL_REGISTRY_VERSION:
            raise ValueError("unsupported registry_version")
        try:
            outcome = ToolExecutionStatus(self.outcome)
        except ValueError as exc:
            raise ValueError("outcome must be a ToolExecutionStatus") from exc
        object.__setattr__(self, "outcome", outcome)
        if self.safe_error_code is not None:
            object.__setattr__(
                self,
                "safe_error_code",
                _safe_code(self.safe_error_code, "safe_error_code"),
            )
        if (
            isinstance(self.row_count, bool)
            or not isinstance(self.row_count, int)
            or self.row_count < 0
        ):
            raise ValueError("row_count must be a non-negative integer")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, (int, float))
            or not math.isfinite(float(self.duration_ms))
            or float(self.duration_ms) < 0
        ):
            raise ValueError("duration_ms must be finite and non-negative")
        object.__setattr__(self, "duration_ms", float(self.duration_ms))
        if self.report_generation_status is not None:
            object.__setattr__(
                self,
                "report_generation_status",
                _safe_code(
                    self.report_generation_status,
                    "report_generation_status",
                ),
            )
        if not isinstance(self.fallback_used, bool):
            raise TypeError("fallback_used must be a boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "principal_ref": self.principal_ref,
            "role_ref": self.role_ref.value,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "arguments_sha256": self.arguments_sha256,
            "policy_version": self.policy_version,
            "registry_version": self.registry_version,
            "outcome": self.outcome.value,
            "safe_error_code": self.safe_error_code,
            "row_count": self.row_count,
            "duration_ms": self.duration_ms,
            "report_generation_status": self.report_generation_status,
            "fallback_used": self.fallback_used,
        }


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Typed result returned by every static read-only tool handler."""

    tool_name: str
    tool_version: str
    status: ToolExecutionStatus | str
    data: Mapping[str, Any]
    source_refs: tuple[str, ...] = ()
    row_count: int = 0
    duration_ms: float = 0.0
    safe_error: ToolError | None = None
    audit_metadata: ToolAuditMetadata | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tool_name",
            _safe_text(self.tool_name, "tool_name"),
        )
        object.__setattr__(
            self,
            "tool_version",
            _safe_text(self.tool_version, "tool_version"),
        )
        try:
            status = ToolExecutionStatus(self.status)
        except ValueError as exc:
            raise ValueError("status must be a ToolExecutionStatus") from exc
        object.__setattr__(self, "status", status)
        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a mapping")
        object.__setattr__(self, "data", dict(self.data))

        source_refs = tuple(self.source_refs)
        if any(
            not isinstance(item, str)
            or not item
            or len(item) > 160
            for item in source_refs
        ):
            raise ValueError("source_refs must contain bounded references")
        object.__setattr__(self, "source_refs", source_refs)

        if (
            isinstance(self.row_count, bool)
            or not isinstance(self.row_count, int)
            or self.row_count < 0
        ):
            raise ValueError("row_count must be a non-negative integer")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, (int, float))
            or not math.isfinite(float(self.duration_ms))
            or float(self.duration_ms) < 0
        ):
            raise ValueError("duration_ms must be finite and non-negative")
        object.__setattr__(self, "duration_ms", float(self.duration_ms))
        if self.safe_error is not None and not isinstance(
            self.safe_error,
            ToolError,
        ):
            raise TypeError("safe_error must be a ToolError or None")
        if self.audit_metadata is not None and not isinstance(
            self.audit_metadata,
            ToolAuditMetadata,
        ):
            raise TypeError(
                "audit_metadata must be ToolAuditMetadata or None"
            )
        if status is ToolExecutionStatus.SUCCESS and self.safe_error is not None:
            raise ValueError("successful results cannot include safe_error")
        if status is not ToolExecutionStatus.SUCCESS and self.safe_error is None:
            raise ValueError("refused or failed results require safe_error")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "status": self.status.value,
            "data": dict(self.data),
            "source_refs": list(self.source_refs),
            "row_count": self.row_count,
            "duration_ms": self.duration_ms,
            "safe_error": (
                None if self.safe_error is None else self.safe_error.to_dict()
            ),
            "audit_metadata": (
                None
                if self.audit_metadata is None
                else self.audit_metadata.to_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class AgentResult:
    """One structured, provider-independent Agent response."""

    request_id: str
    audit_id: str | None
    status: AgentOutcome | str
    answer: str
    facts: tuple[Mapping[str, Any], ...] = ()
    metrics: tuple[Mapping[str, Any], ...] = ()
    event_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    report: Mapping[str, Any] | None = None
    safe_error: ToolError | None = None
    schema_version: str = AGENT_RESULT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_RESULT_SCHEMA_VERSION:
            raise ValueError("unsupported result schema_version")
        object.__setattr__(
            self,
            "request_id",
            _safe_text(self.request_id, "request_id"),
        )
        if self.audit_id is not None:
            object.__setattr__(
                self,
                "audit_id",
                _safe_text(self.audit_id, "audit_id"),
            )
        try:
            status = AgentOutcome(self.status)
        except ValueError as exc:
            raise ValueError("status must be a supported AgentOutcome") from exc
        object.__setattr__(self, "status", status)

        if not isinstance(self.answer, str) or not self.answer.strip():
            raise ValueError("answer must be a non-empty string")
        answer = self.answer.strip()
        if len(answer) > 2000:
            raise ValueError("answer must be at most 2000 characters")
        object.__setattr__(self, "answer", answer)

        facts = tuple(self.facts)
        metrics = tuple(self.metrics)
        if any(not isinstance(item, Mapping) for item in facts):
            raise TypeError("facts must contain mappings")
        if any(not isinstance(item, Mapping) for item in metrics):
            raise TypeError("metrics must contain mappings")
        object.__setattr__(
            self,
            "facts",
            tuple(MappingProxyType(dict(item)) for item in facts),
        )
        object.__setattr__(
            self,
            "metrics",
            tuple(MappingProxyType(dict(item)) for item in metrics),
        )

        object.__setattr__(
            self,
            "event_refs",
            tuple(
                _safe_result_reference(item, "event_ref")
                for item in self.event_refs
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(
                _safe_result_reference(item, "evidence_ref")
                for item in self.evidence_refs
            ),
        )

        if self.report is not None:
            if not isinstance(self.report, Mapping):
                raise TypeError("report must be a mapping or None")
            object.__setattr__(
                self,
                "report",
                MappingProxyType(dict(self.report)),
            )

        if self.safe_error is not None and not isinstance(
            self.safe_error,
            ToolError,
        ):
            raise TypeError("safe_error must be a ToolError or None")
        if status in {AgentOutcome.ANSWERED, AgentOutcome.INSUFFICIENT_DATA}:
            if self.audit_id is None:
                raise ValueError("successful outcomes require an audit_id")
            if self.safe_error is not None:
                raise ValueError("successful outcomes cannot include safe_error")
        elif self.safe_error is None:
            raise ValueError("non-success outcomes require safe_error")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "audit_id": self.audit_id,
            "status": self.status.value,
            "answer": self.answer,
            "facts": [dict(item) for item in self.facts],
            "metrics": [dict(item) for item in self.metrics],
            "event_refs": list(self.event_refs),
            "evidence_refs": list(self.evidence_refs),
            "report": None if self.report is None else dict(self.report),
            "safe_error": (
                None if self.safe_error is None else self.safe_error.to_dict()
            ),
        }

    def to_json(self) -> str:
        """Return deterministic canonical JSON for one Agent response."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


@dataclass(frozen=True, slots=True)
class AgentToolDescriptor:
    """Immutable descriptor for one project-owned tool."""

    tool_name: str
    tool_version: str
    description: str
    effect: ToolEffect
    input_schema: tuple[str, ...]
    output_schema: tuple[str, ...]
    required_capabilities: tuple[AgentCapability, ...]
    timeout_seconds: float
    max_calls_per_request: int = 1
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tool_name",
            _safe_text(self.tool_name, "tool_name"),
        )
        object.__setattr__(
            self,
            "tool_version",
            _safe_text(self.tool_version, "tool_version"),
        )
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        object.__setattr__(self, "description", self.description.strip())
        try:
            effect = ToolEffect(self.effect)
        except ValueError as exc:
            raise ValueError("effect must be ToolEffect.READ_ONLY") from exc
        object.__setattr__(self, "effect", effect)

        input_schema = tuple(self.input_schema)
        output_schema = tuple(self.output_schema)
        if any(not isinstance(item, str) or not item for item in input_schema):
            raise ValueError("input_schema must contain non-empty names")
        if any(not isinstance(item, str) or not item for item in output_schema):
            raise ValueError("output_schema must contain non-empty names")
        if len(set(input_schema)) != len(input_schema):
            raise ValueError("input_schema cannot contain duplicates")
        object.__setattr__(self, "input_schema", input_schema)
        object.__setattr__(self, "output_schema", output_schema)

        capabilities: list[AgentCapability] = []
        for capability in self.required_capabilities:
            try:
                normalized = AgentCapability(capability)
            except ValueError as exc:
                raise ValueError(
                    "required_capabilities contain an unsupported value"
                ) from exc
            if normalized not in capabilities:
                capabilities.append(normalized)
        object.__setattr__(
            self,
            "required_capabilities",
            tuple(capabilities),
        )
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or float(self.timeout_seconds) <= 0
        ):
            raise ValueError("timeout_seconds must be finite and positive")
        object.__setattr__(
            self,
            "timeout_seconds",
            float(self.timeout_seconds),
        )
        if (
            isinstance(self.max_calls_per_request, bool)
            or not isinstance(self.max_calls_per_request, int)
            or self.max_calls_per_request < 1
        ):
            raise ValueError("max_calls_per_request must be positive")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean")


class AgentToolHandler(Protocol):
    """Callable contract for one static read-only tool."""

    def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        """Execute the tool without filesystem, shell or mutation access."""


@dataclass(frozen=True, slots=True)
class AgentTool:
    """A static descriptor bound to one implementation handler."""

    descriptor: AgentToolDescriptor
    handler: AgentToolHandler

    def __post_init__(self) -> None:
        if not isinstance(self.descriptor, AgentToolDescriptor):
            raise TypeError("descriptor must be an AgentToolDescriptor")
        if not callable(self.handler):
            raise TypeError("handler must be callable")

    @property
    def tool_name(self) -> str:
        return self.descriptor.tool_name

    @property
    def tool_version(self) -> str:
        return self.descriptor.tool_version


@dataclass(frozen=True, slots=True)
class AgentPlan:
    """One deterministic, non-executable plan for an allowlisted tool."""

    intent: AgentIntent | str
    tool_name: str
    tool_version: str
    arguments: Mapping[str, Any]
    question_sha256: str
    schema_version: str = AGENT_PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_PLAN_SCHEMA_VERSION:
            raise ValueError("unsupported plan schema_version")
        try:
            intent = AgentIntent(self.intent)
        except ValueError as exc:
            raise ValueError("intent must be a supported AgentIntent") from exc
        if intent not in {
            AgentIntent.SAFETY_SUMMARY,
            AgentIntent.EVENT_STATISTICS,
            AgentIntent.EVENT_DETAIL,
            AgentIntent.SAFETY_REPORT,
        }:
            raise ValueError("an execution plan requires a supported intent")
        object.__setattr__(self, "intent", intent)
        object.__setattr__(
            self,
            "tool_name",
            _safe_text(self.tool_name, "tool_name"),
        )
        object.__setattr__(
            self,
            "tool_version",
            _safe_text(self.tool_version, "tool_version"),
        )
        if not isinstance(self.arguments, Mapping):
            raise TypeError("arguments must be a mapping")
        normalized_arguments: dict[str, Any] = {}
        for key, value in self.arguments.items():
            if not isinstance(key, str) or not key:
                raise ValueError("argument names must be non-empty strings")
            normalized_arguments[key] = value
        object.__setattr__(
            self,
            "arguments",
            MappingProxyType(normalized_arguments),
        )
        if re.fullmatch(r"[0-9a-f]{64}", self.question_sha256) is None:
            raise ValueError("question_sha256 must be a lowercase SHA256")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "intent": self.intent.value,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "arguments": dict(self.arguments),
            "question_sha256": self.question_sha256,
        }


@dataclass(frozen=True, slots=True)
class AgentPlanCandidate:
    """One untrusted, non-executable plan proposal from a provider."""

    request_binding_sha256: str
    proposed_intent: AgentIntent | str
    proposed_tool_name: str
    proposed_tool_version: str
    proposed_arguments: Mapping[str, Any]
    reason_code: AgentPlanCandidateReason | str
    schema_version: str = AGENT_PLAN_CANDIDATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_PLAN_CANDIDATE_SCHEMA_VERSION:
            raise ValueError("unsupported candidate schema_version")
        if re.fullmatch(
            r"[0-9a-f]{64}",
            self.request_binding_sha256,
        ) is None:
            raise ValueError(
                "request_binding_sha256 must be a lowercase SHA256"
            )
        try:
            proposed_intent = AgentIntent(self.proposed_intent)
        except ValueError as exc:
            raise ValueError(
                "proposed_intent must be a supported AgentIntent"
            ) from exc
        object.__setattr__(self, "proposed_intent", proposed_intent)
        object.__setattr__(
            self,
            "proposed_tool_name",
            _safe_text(self.proposed_tool_name, "proposed_tool_name"),
        )
        object.__setattr__(
            self,
            "proposed_tool_version",
            _safe_text(
                self.proposed_tool_version,
                "proposed_tool_version",
            ),
        )
        if _SAFE_VERSION.fullmatch(self.proposed_tool_version) is None:
            raise ValueError(
                "proposed_tool_version must be a semantic version"
            )
        if not isinstance(self.proposed_arguments, Mapping):
            raise TypeError("proposed_arguments must be a mapping")
        normalized_arguments: dict[str, Any] = {}
        for key, value in self.proposed_arguments.items():
            if not isinstance(key, str) or not key:
                raise ValueError(
                    "proposed argument names must be non-empty strings"
                )
            normalized_arguments[key] = value
        object.__setattr__(
            self,
            "proposed_arguments",
            MappingProxyType(normalized_arguments),
        )
        try:
            reason_code = AgentPlanCandidateReason(self.reason_code)
        except ValueError as exc:
            raise ValueError(
                "reason_code must be a supported "
                "AgentPlanCandidateReason"
            ) from exc
        object.__setattr__(self, "reason_code", reason_code)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_binding_sha256": self.request_binding_sha256,
            "proposed_intent": self.proposed_intent.value,
            "proposed_tool_name": self.proposed_tool_name,
            "proposed_tool_version": self.proposed_tool_version,
            "proposed_arguments": dict(self.proposed_arguments),
            "reason_code": self.reason_code.value,
        }

    def to_json(self) -> str:
        """Return deterministic canonical JSON for this candidate."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


_AUDIT_METADATA_FIELDS = frozenset(
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


def _audit_metadata_value(key: str, value: Any) -> Any:
    if key not in _AUDIT_METADATA_FIELDS:
        raise ValueError("safe_metadata contains an unsupported field")
    if key == "duration_ms":
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
        ):
            raise ValueError("duration_ms must be finite and non-negative")
        return float(value)
    if key == "row_count":
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise ValueError("row_count must be a non-negative integer")
        return value
    if key == "fallback_used":
        if not isinstance(value, bool):
            raise TypeError("fallback_used must be a boolean")
        return value
    if key == "tool_version":
        if not isinstance(value, str) or _SAFE_VERSION.fullmatch(
            value.strip()
        ) is None:
            raise ValueError("tool_version must be a bounded semantic version")
        return value.strip()
    if key == "policy_version":
        if value != AGENT_POLICY_VERSION:
            raise ValueError("policy_version is not the frozen version")
        return value
    if key == "registry_version":
        if value != AGENT_TOOL_REGISTRY_VERSION:
            raise ValueError("registry_version is not the frozen version")
        return value
    if key == "report_generation_status":
        return _safe_code(value, "report_generation_status")
    raise ValueError("safe_metadata contains an unsupported field")


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One immutable append-only Agent audit record.

    The event records operational identity and outcomes only. Raw questions,
    tool arguments, provider output, credentials, filesystem paths and
    arbitrary metadata are not represented by this contract.
    """

    audit_id: str
    request_id: str
    timestamp: str
    principal_ref: str
    role_ref: AgentRole | str
    intent: AgentIntent | str
    plan_id: str
    tools_requested: tuple[str, ...]
    execution_status: AgentAuditStatus | str
    failure_status: str | None = None
    question_sha256: str | None = None
    safe_metadata: Mapping[str, Any] | None = None
    schema_version: str = AGENT_AUDIT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_AUDIT_VERSION:
            raise ValueError("unsupported audit schema_version")
        object.__setattr__(
            self,
            "audit_id",
            _safe_text(self.audit_id, "audit_id"),
        )
        object.__setattr__(
            self,
            "request_id",
            _safe_text(self.request_id, "request_id"),
        )
        object.__setattr__(
            self,
            "timestamp",
            _safe_text(self.timestamp, "timestamp"),
        )
        object.__setattr__(
            self,
            "principal_ref",
            _safe_text(self.principal_ref, "principal_ref"),
        )
        try:
            role_ref = AgentRole(self.role_ref)
        except ValueError as exc:
            raise ValueError("role_ref must be a supported AgentRole") from exc
        object.__setattr__(self, "role_ref", role_ref)
        try:
            intent = AgentIntent(self.intent)
        except ValueError as exc:
            raise ValueError("intent must be a supported AgentIntent") from exc
        object.__setattr__(self, "intent", intent)
        object.__setattr__(
            self,
            "plan_id",
            _safe_text(self.plan_id, "plan_id"),
        )

        tools_requested = tuple(self.tools_requested)
        if len(tools_requested) > 4:
            raise ValueError("tools_requested exceeds the frozen bound")
        if len(set(tools_requested)) != len(tools_requested):
            raise ValueError("tools_requested cannot contain duplicates")
        object.__setattr__(
            self,
            "tools_requested",
            tuple(
                _safe_text(tool_name, "tool_name")
                for tool_name in tools_requested
            ),
        )

        try:
            execution_status = AgentAuditStatus(self.execution_status)
        except ValueError as exc:
            raise ValueError(
                "execution_status must be a supported AgentAuditStatus"
            ) from exc
        object.__setattr__(self, "execution_status", execution_status)

        if self.failure_status is not None:
            object.__setattr__(
                self,
                "failure_status",
                _safe_code(self.failure_status, "failure_status"),
            )
        terminal_success = execution_status in {
            AgentAuditStatus.PLANNED,
            AgentAuditStatus.SUCCESS,
        }
        if terminal_success and self.failure_status is not None:
            raise ValueError(
                "planned or successful events cannot include failure_status"
            )
        if not terminal_success and self.failure_status is None:
            raise ValueError(
                "failure, refusal and unknown-tool events require failure_status"
            )

        if self.question_sha256 is not None and re.fullmatch(
            r"[0-9a-f]{64}",
            self.question_sha256,
        ) is None:
            raise ValueError("question_sha256 must be a lowercase SHA256")

        if self.safe_metadata is None:
            metadata: Mapping[str, Any] = {}
        elif isinstance(self.safe_metadata, Mapping):
            metadata = self.safe_metadata
        else:
            raise TypeError("safe_metadata must be a mapping or None")
        normalized_metadata = {
            key: _audit_metadata_value(key, value)
            for key, value in metadata.items()
        }
        object.__setattr__(
            self,
            "safe_metadata",
            MappingProxyType(normalized_metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "principal_ref": self.principal_ref,
            "role_ref": self.role_ref.value,
            "intent": self.intent.value,
            "plan_id": self.plan_id,
            "tools_requested": list(self.tools_requested),
            "execution_status": self.execution_status.value,
            "failure_status": self.failure_status,
            "question_sha256": self.question_sha256,
            "safe_metadata": dict(self.safe_metadata),
        }

    def to_json(self) -> str:
        """Return deterministic canonical JSON for one audit record."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


def sha256_arguments(arguments: Mapping[str, Any]) -> str:
    """Return a canonical SHA256 for audit use without retaining arguments."""

    if not isinstance(arguments, Mapping):
        raise TypeError("arguments must be a mapping")
    payload = json.dumps(
        dict(arguments),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
