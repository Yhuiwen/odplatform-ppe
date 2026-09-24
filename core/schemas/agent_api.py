"""Phase 8 final integration application API contracts.

These schemas define the typed in-process boundary used by future web code.
They do not expose planner, provider, registry, audit or tool internals.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from core.schemas.agent import AgentCapability, AgentOutcome, AgentRole, ToolError

__all__ = [
    "AGENT_API_SCHEMA_VERSION",
    "AgentApiOperation",
    "AgentApiRequest",
    "AgentApiResponse",
    "AgentApiValidationError",
    "AgentPresentationState",
    "ProviderStatus",
    "TrustedIdentity",
    "TrustedIdentityProvider",
]

AGENT_API_SCHEMA_VERSION = "phase8-agent-api-v1"

_SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_MAX_MAPPING_BYTES = 8192
_MAX_MAPPING_FIELDS = 16
_MAX_QUESTION_BYTES = 2000


class AgentApiValidationError(ValueError):
    """A bounded caller-contract validation failure."""


class AgentApiOperation(str, Enum):
    """User-facing workflows accepted by the application boundary."""

    ASK = "ASK"
    GENERATE_REPORT = "GENERATE_REPORT"


class AgentPresentationState(str, Enum):
    """UI-safe state derived from the frozen AgentOutcome vocabulary."""

    SUCCESS = "success"
    EMPTY = "empty"
    OUT_OF_SCOPE = "out_of_scope"
    REFUSED = "refused"
    TOOL_ERROR = "tool_error"
    AUDIT_UNAVAILABLE = "audit_unavailable"


class ProviderStatus(str, Enum):
    """Sanitized report generation status; never raw provider output."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    LLM = "LLM"
    TEMPLATE_FALLBACK = "TEMPLATE_FALLBACK"
    REPORT_UNAVAILABLE = "REPORT_UNAVAILABLE"


def _safe_reference(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentApiValidationError(
            f"{field_name} must be a non-empty string"
        )
    normalized = value.strip()
    if _SAFE_REFERENCE.fullmatch(normalized) is None:
        raise AgentApiValidationError(
            f"{field_name} must use a safe opaque reference"
        )
    return normalized


def _safe_result_reference(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentApiValidationError(
            f"{field_name} must be a non-empty string"
        )
    normalized = value.strip()
    if (
        len(normalized) > 300
        or normalized.startswith("/")
        or "\\" in normalized
        or re.match(r"^[A-Za-z]:/", normalized) is not None
    ):
        raise AgentApiValidationError(
            f"{field_name} must be a relative opaque reference"
        )
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise AgentApiValidationError(
            f"{field_name} must not contain unsafe path segments"
        )
    return normalized


def _normalize_question(value: str) -> str:
    if not isinstance(value, str):
        raise AgentApiValidationError("question must be a UTF-8 string")
    normalized = " ".join(value.split())
    if not normalized:
        raise AgentApiValidationError("question cannot be empty")
    if len(normalized.encode("utf-8")) > _MAX_QUESTION_BYTES:
        raise AgentApiValidationError(
            "question exceeds the frozen byte limit"
        )
    return normalized


def _bounded_mapping(
    value: Mapping[str, Any] | None,
    field_name: str,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise AgentApiValidationError(
            f"{field_name} must be a mapping or None"
        )
    if len(value) > _MAX_MAPPING_FIELDS:
        raise AgentApiValidationError(
            f"{field_name} exceeds the frozen field limit"
        )
    try:
        encoded = json.dumps(
            dict(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise AgentApiValidationError(
            f"{field_name} must contain bounded JSON values"
        ) from None
    if len(encoded) > _MAX_MAPPING_BYTES:
        raise AgentApiValidationError(
            f"{field_name} exceeds the frozen byte limit"
        )
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class AgentApiRequest:
    """One caller request that cannot select identity, tool or provider data."""

    request_id: str
    operation: AgentApiOperation | str
    question: str
    requested_period: Mapping[str, Any] | None = None
    filters: Mapping[str, Any] | None = None
    schema_version: str = AGENT_API_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_API_SCHEMA_VERSION:
            raise AgentApiValidationError(
                "unsupported application request schema_version"
            )
        object.__setattr__(
            self,
            "request_id",
            _safe_reference(self.request_id, "request_id"),
        )
        try:
            operation = AgentApiOperation(self.operation)
        except ValueError as exc:
            raise AgentApiValidationError(
                "operation must be ASK or GENERATE_REPORT"
            ) from exc
        object.__setattr__(self, "operation", operation)
        object.__setattr__(
            self,
            "question",
            _normalize_question(self.question),
        )
        object.__setattr__(
            self,
            "requested_period",
            _bounded_mapping(self.requested_period, "requested_period"),
        )
        object.__setattr__(
            self,
            "filters",
            _bounded_mapping(self.filters, "filters"),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "AgentApiRequest":
        """Build a request while rejecting caller-selected internal fields."""

        if not isinstance(payload, Mapping):
            raise AgentApiValidationError("request must be a mapping")
        allowed = {
            "schema_version",
            "request_id",
            "operation",
            "question",
            "requested_period",
            "filters",
        }
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise AgentApiValidationError(
                "request contains unsupported fields: " + ", ".join(unknown)
            )
        required = {"request_id", "operation", "question"}
        missing = sorted(required - set(payload))
        if missing:
            raise AgentApiValidationError(
                "request is missing required fields: " + ", ".join(missing)
            )
        return cls(
            request_id=payload["request_id"],
            operation=payload["operation"],
            question=payload["question"],
            requested_period=payload.get("requested_period"),
            filters=payload.get("filters"),
            schema_version=payload.get(
                "schema_version",
                AGENT_API_SCHEMA_VERSION,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "operation": self.operation.value,
            "question": self.question,
            "requested_period": (
                None
                if self.requested_period is None
                else dict(self.requested_period)
            ),
            "filters": None if self.filters is None else dict(self.filters),
        }


@dataclass(frozen=True, slots=True)
class TrustedIdentity:
    """Deployment-owned identity injected after authentication."""

    principal_ref: str
    role: AgentRole | str
    capabilities: frozenset[AgentCapability | str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "principal_ref",
            _safe_reference(self.principal_ref, "principal_ref"),
        )
        try:
            role = AgentRole(self.role)
        except ValueError as exc:
            raise AgentApiValidationError(
                "role must be a supported AgentRole"
            ) from exc
        object.__setattr__(self, "role", role)

        normalized_capabilities: set[AgentCapability] = set()
        for capability in self.capabilities:
            try:
                normalized_capabilities.add(AgentCapability(capability))
            except ValueError as exc:
                raise AgentApiValidationError(
                    "capabilities contain an unsupported value"
                ) from exc
        object.__setattr__(
            self,
            "capabilities",
            frozenset(normalized_capabilities),
        )


class TrustedIdentityProvider(Protocol):
    """Resolve the authenticated identity for one request."""

    def resolve(self, request_id: str) -> TrustedIdentity | None:
        """Return trusted identity or fail closed with None."""


def _normalize_mapping_sequence(
    values: tuple[Mapping[str, Any], ...],
    field_name: str,
) -> tuple[Mapping[str, Any], ...]:
    normalized: list[Mapping[str, Any]] = []
    for value in values:
        if not isinstance(value, Mapping):
            raise TypeError(f"{field_name} must contain mappings")
        normalized.append(MappingProxyType(dict(value)))
    return tuple(normalized)


_PRESENTATION_BY_OUTCOME = MappingProxyType(
    {
        AgentOutcome.ANSWERED: AgentPresentationState.SUCCESS,
        AgentOutcome.INSUFFICIENT_DATA: AgentPresentationState.EMPTY,
        AgentOutcome.OUT_OF_SCOPE: AgentPresentationState.OUT_OF_SCOPE,
        AgentOutcome.REFUSED: AgentPresentationState.REFUSED,
        AgentOutcome.TOOL_ERROR: AgentPresentationState.TOOL_ERROR,
        AgentOutcome.AUDIT_UNAVAILABLE: (
            AgentPresentationState.AUDIT_UNAVAILABLE
        ),
    }
)


@dataclass(frozen=True, slots=True)
class AgentApiResponse:
    """One bounded UI-safe projection of an AgentResult."""

    request_id: str
    audit_id: str | None
    status: AgentOutcome | str
    presentation_state: AgentPresentationState | str
    answer: str
    facts: tuple[Mapping[str, Any], ...] = ()
    metrics: tuple[Mapping[str, Any], ...] = ()
    event_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    report: Mapping[str, Any] | None = None
    safe_error: ToolError | None = None
    provider_status: ProviderStatus | str = ProviderStatus.NOT_APPLICABLE
    degraded: bool = False
    schema_version: str = AGENT_API_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != AGENT_API_SCHEMA_VERSION:
            raise AgentApiValidationError(
                "unsupported application response schema_version"
            )
        object.__setattr__(
            self,
            "request_id",
            _safe_reference(self.request_id, "request_id"),
        )
        if self.audit_id is not None:
            object.__setattr__(
                self,
                "audit_id",
                _safe_reference(self.audit_id, "audit_id"),
            )
        try:
            status = AgentOutcome(self.status)
        except ValueError as exc:
            raise AgentApiValidationError(
                "status must be a supported AgentOutcome"
            ) from exc
        object.__setattr__(self, "status", status)

        try:
            presentation_state = AgentPresentationState(
                self.presentation_state
            )
        except ValueError as exc:
            raise AgentApiValidationError(
                "presentation_state is not supported"
            ) from exc
        if presentation_state is not _PRESENTATION_BY_OUTCOME[status]:
            raise AgentApiValidationError(
                "presentation_state does not match status"
            )
        object.__setattr__(
            self,
            "presentation_state",
            presentation_state,
        )

        if not isinstance(self.answer, str) or not self.answer.strip():
            raise AgentApiValidationError(
                "answer must be a non-empty string"
            )
        answer = self.answer.strip()
        if len(answer) > _MAX_QUESTION_BYTES:
            raise AgentApiValidationError(
                "answer exceeds the frozen character limit"
            )
        object.__setattr__(self, "answer", answer)

        facts = tuple(self.facts)
        metrics = tuple(self.metrics)
        object.__setattr__(
            self,
            "facts",
            _normalize_mapping_sequence(facts, "facts"),
        )
        object.__setattr__(
            self,
            "metrics",
            _normalize_mapping_sequence(metrics, "metrics"),
        )
        object.__setattr__(
            self,
            "event_refs",
            tuple(
                _safe_result_reference(value, "event_ref")
                for value in self.event_refs
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(
                _safe_result_reference(value, "evidence_ref")
                for value in self.evidence_refs
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
                raise AgentApiValidationError(
                    "successful outcomes require an audit_id"
                )
            if self.safe_error is not None:
                raise AgentApiValidationError(
                    "successful outcomes cannot include safe_error"
                )
        elif self.safe_error is None:
            raise AgentApiValidationError(
                "non-success outcomes require safe_error"
            )

        if status in {
            AgentOutcome.INSUFFICIENT_DATA,
            AgentOutcome.OUT_OF_SCOPE,
            AgentOutcome.REFUSED,
            AgentOutcome.TOOL_ERROR,
            AgentOutcome.AUDIT_UNAVAILABLE,
        }:
            if (
                self.facts
                or self.metrics
                or self.event_refs
                or self.evidence_refs
                or self.report is not None
            ):
                raise AgentApiValidationError(
                    "non-answered outcomes cannot release result data"
                )

        try:
            provider_status = ProviderStatus(self.provider_status)
        except ValueError as exc:
            raise AgentApiValidationError(
                "provider_status is not supported"
            ) from exc
        object.__setattr__(self, "provider_status", provider_status)
        if not isinstance(self.degraded, bool):
            raise TypeError("degraded must be a boolean")
        if self.report is None:
            if (
                provider_status is not ProviderStatus.NOT_APPLICABLE
                or self.degraded
            ):
                raise AgentApiValidationError(
                    "responses without a report cannot claim provider status"
                )
        elif provider_status is ProviderStatus.NOT_APPLICABLE:
            raise AgentApiValidationError(
                "responses with a report require provider status"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "audit_id": self.audit_id,
            "status": self.status.value,
            "presentation_state": self.presentation_state.value,
            "answer": self.answer,
            "facts": [dict(item) for item in self.facts],
            "metrics": [dict(item) for item in self.metrics],
            "event_refs": list(self.event_refs),
            "evidence_refs": list(self.evidence_refs),
            "report": None if self.report is None else dict(self.report),
            "safe_error": (
                None if self.safe_error is None else self.safe_error.to_dict()
            ),
            "provider_status": self.provider_status.value,
            "degraded": self.degraded,
        }

    def to_json(self) -> str:
        """Return deterministic canonical JSON for one API response."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
