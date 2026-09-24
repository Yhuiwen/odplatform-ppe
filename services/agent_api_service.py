"""Application facade for the frozen Phase 8 Agent service."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

from core.schemas.agent import (
    AgentOutcome,
    AgentRequest,
    AgentResult,
    ToolError,
)
from core.schemas.agent_api import (
    AgentApiOperation,
    AgentApiRequest,
    AgentApiResponse,
    AgentPresentationState,
    ProviderStatus,
    TrustedIdentity,
    TrustedIdentityProvider,
)
from services.agent_service import AgentService

__all__ = ["AgentApplicationService"]

_REPORT_QUESTION = "Generate a safety report"
_MAX_PROJECTION_DEPTH = 6
_MAX_PROJECTION_STRING = 4096
_PROHIBITED_KEYS = frozenset(
    {
        "api_key",
        "arguments",
        "arguments_sha256",
        "audit_metadata",
        "candidate",
        "credentials",
        "filesystem_path",
        "prompt",
        "provider_output",
        "raw_candidate",
        "raw_output",
        "raw_provider_response",
        "shell",
        "sql",
        "token",
        "tool_name",
        "tool_version",
        "traceback",
    }
)
_PROHIBITED_VALUE_PATTERNS = (
    re.compile(r"(?:^|[\s\"'])select\s+.+\s+from\b", re.IGNORECASE),
    re.compile(r"\b(?:insert\s+into|delete\s+from|drop\s+table)\b", re.IGNORECASE),
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\b(?:powershell|cmd(?:\.exe)?|bash|sh)\s+", re.IGNORECASE),
)
_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:^\\\\|^/|^[A-Za-z]:[\\/])"
)


class AgentApplicationService:
    """Resolve trusted identity, call AgentService once and project safely."""

    def __init__(
        self,
        agent_service: AgentService,
        identity_provider: TrustedIdentityProvider,
        *,
        report_question: str = _REPORT_QUESTION,
    ) -> None:
        if not isinstance(agent_service, AgentService):
            raise TypeError("agent_service must be an AgentService")
        if not callable(getattr(identity_provider, "resolve", None)):
            raise TypeError(
                "identity_provider must expose resolve(request_id)"
            )
        normalized_report_question = " ".join(report_question.split())
        if not normalized_report_question:
            raise ValueError("report_question cannot be empty")
        if len(normalized_report_question.encode("utf-8")) > 2000:
            raise ValueError("report_question exceeds the frozen byte limit")

        self._agent_service = agent_service
        self._identity_provider = identity_provider
        self.report_question = normalized_report_question

    def execute(self, request: AgentApiRequest) -> AgentApiResponse:
        """Execute one bounded application request without exposing internals."""

        if not isinstance(request, AgentApiRequest):
            raise TypeError("request must be an AgentApiRequest")

        try:
            identity = self._identity_provider.resolve(request.request_id)
        except Exception:
            return self._failure(
                request_id=request.request_id,
                status=AgentOutcome.REFUSED,
                code="IDENTITY_PROVIDER_ERROR",
                message="trusted identity could not be resolved",
            )
        if identity is None:
            return self._failure(
                request_id=request.request_id,
                status=AgentOutcome.REFUSED,
                code="UNAUTHENTICATED",
                message="trusted identity is required",
            )
        if not isinstance(identity, TrustedIdentity):
            return self._failure(
                request_id=request.request_id,
                status=AgentOutcome.REFUSED,
                code="INVALID_IDENTITY",
                message="trusted identity provider returned an invalid value",
            )

        question = (
            self.report_question
            if request.operation is AgentApiOperation.GENERATE_REPORT
            else request.question
        )
        try:
            domain_request = AgentRequest(
                request_id=request.request_id,
                principal_ref=identity.principal_ref,
                role=identity.role,
                question=question,
                requested_period=request.requested_period,
                filters=request.filters,
                capabilities=identity.capabilities,
            )
        except (TypeError, ValueError):
            return self._failure(
                request_id=request.request_id,
                status=AgentOutcome.REFUSED,
                code="INVALID_REQUEST",
                message="request does not satisfy the Agent contract",
            )

        try:
            result = self._agent_service.execute(domain_request)
        except Exception:
            return self._failure(
                request_id=request.request_id,
                status=AgentOutcome.TOOL_ERROR,
                code="AGENT_EXECUTION_ERROR",
                message="the Agent failed safely",
            )

        try:
            return self._project(request.request_id, result)
        except _UnsafeProjection:
            return self._failure(
                request_id=request.request_id,
                status=AgentOutcome.TOOL_ERROR,
                code="UNSAFE_AGENT_RESULT",
                message="the Agent result could not be safely released",
                audit_id=(
                    result.audit_id
                    if isinstance(result, AgentResult)
                    else None
                ),
            )

    @staticmethod
    def _project(
        request_id: str,
        result: AgentResult,
    ) -> AgentApiResponse:
        if not isinstance(result, AgentResult):
            raise _UnsafeProjection
        if result.request_id != request_id:
            raise _UnsafeProjection

        presentation_state = _presentation_state(result.status)
        if result.status in {
            AgentOutcome.ANSWERED,
            AgentOutcome.INSUFFICIENT_DATA,
        }:
            if result.status is AgentOutcome.INSUFFICIENT_DATA:
                facts: tuple[Mapping[str, Any], ...] = ()
                metrics: tuple[Mapping[str, Any], ...] = ()
                event_refs: tuple[str, ...] = ()
                evidence_refs: tuple[str, ...] = ()
                report = None
            else:
                facts = _safe_mapping_sequence(result.facts, "facts")
                metrics = _safe_mapping_sequence(result.metrics, "metrics")
                event_refs = _safe_reference_sequence(
                    result.event_refs,
                    "event_refs",
                )
                evidence_refs = _safe_reference_sequence(
                    result.evidence_refs,
                    "evidence_refs",
                )
                report = (
                    None
                    if result.report is None
                    else _safe_mapping(result.report, "report", depth=0)
                )
            provider_status, degraded = _report_status(report)
            return AgentApiResponse(
                request_id=request_id,
                audit_id=result.audit_id,
                status=result.status,
                presentation_state=presentation_state,
                answer=_safe_answer(result.answer),
                facts=facts,
                metrics=metrics,
                event_refs=event_refs,
                evidence_refs=evidence_refs,
                report=report,
                provider_status=provider_status,
                degraded=degraded,
            )

        if result.safe_error is None:
            raise _UnsafeProjection
        try:
            answer = _safe_answer(result.answer)
        except _UnsafeProjection:
            answer = _failure_answer(result.status)
        return AgentApiResponse(
            request_id=request_id,
            audit_id=result.audit_id,
            status=result.status,
            presentation_state=presentation_state,
            answer=answer,
            safe_error=_safe_error(result.safe_error),
        )

    @staticmethod
    def _failure(
        *,
        request_id: str,
        status: AgentOutcome,
        code: str,
        message: str,
        audit_id: str | None = None,
    ) -> AgentApiResponse:
        return AgentApiResponse(
            request_id=request_id,
            audit_id=audit_id,
            status=status,
            presentation_state=_presentation_state(status),
            answer=_failure_answer(status),
            safe_error=ToolError(code=code, message=message),
        )


class _UnsafeProjection(ValueError):
    pass


def _presentation_state(status: AgentOutcome) -> AgentPresentationState:
    if status is AgentOutcome.ANSWERED:
        return AgentPresentationState.SUCCESS
    if status is AgentOutcome.INSUFFICIENT_DATA:
        return AgentPresentationState.EMPTY
    if status is AgentOutcome.OUT_OF_SCOPE:
        return AgentPresentationState.OUT_OF_SCOPE
    if status is AgentOutcome.REFUSED:
        return AgentPresentationState.REFUSED
    if status is AgentOutcome.TOOL_ERROR:
        return AgentPresentationState.TOOL_ERROR
    return AgentPresentationState.AUDIT_UNAVAILABLE


def _failure_answer(status: AgentOutcome) -> str:
    if status is AgentOutcome.OUT_OF_SCOPE:
        return "The request is outside the supported read-only scope."
    if status is AgentOutcome.REFUSED:
        return "The request was refused by the Agent policy."
    if status is AgentOutcome.AUDIT_UNAVAILABLE:
        return "Audit storage is unavailable; no successful result released."
    return "The request failed safely."


def _safe_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _UnsafeProjection(f"{field_name} must be non-empty")
    normalized = value.strip()
    if len(normalized) > 2000:
        raise _UnsafeProjection(f"{field_name} exceeds the response limit")
    return normalized


def _safe_answer(value: Any) -> str:
    normalized = _safe_text(value, "answer")
    projected = _safe_value(normalized, "answer", depth=0)
    if not isinstance(projected, str):
        raise _UnsafeProjection("answer must be a string")
    return projected


def _safe_error(error: ToolError) -> ToolError:
    try:
        message = _safe_value(
            error.message,
            "safe_error.message",
            depth=0,
        )
        if not isinstance(message, str):
            raise _UnsafeProjection("safe error message must be a string")
    except _UnsafeProjection:
        message = "the Agent request failed safely"
    return ToolError(code=error.code, message=message)


def _safe_reference_sequence(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise _UnsafeProjection(f"{field_name} contains an invalid reference")
        reference = value.strip()
        if (
            len(reference) > 300
            or reference.startswith(("/", "\\"))
            or re.match(r"^[A-Za-z]:[\\/]", reference) is not None
            or any(part in {"", ".", ".."} for part in reference.split("/"))
        ):
            raise _UnsafeProjection(
                f"{field_name} contains an unsafe reference"
            )
        normalized.append(reference)
    return tuple(normalized)


def _safe_mapping_sequence(
    values: tuple[Mapping[str, Any], ...],
    field_name: str,
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        _safe_mapping(value, f"{field_name}[{index}]", depth=0)
        for index, value in enumerate(values)
    )


def _safe_mapping(
    value: Mapping[str, Any],
    path: str,
    *,
    depth: int,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _UnsafeProjection(f"{path} must be a mapping")
    if depth > _MAX_PROJECTION_DEPTH:
        raise _UnsafeProjection(f"{path} exceeds the projection depth limit")
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise _UnsafeProjection(f"{path} contains an invalid key")
        normalized_key = key.strip()
        if normalized_key.lower() in _PROHIBITED_KEYS:
            raise _UnsafeProjection(
                f"{path} contains prohibited metadata"
            )
        normalized[normalized_key] = _safe_value(
            item,
            f"{path}.{normalized_key}",
            depth=depth + 1,
        )
    return normalized


def _safe_value(value: Any, path: str, *, depth: int) -> Any:
    if depth > _MAX_PROJECTION_DEPTH:
        raise _UnsafeProjection(f"{path} exceeds the projection depth limit")
    if isinstance(value, Mapping):
        return _safe_mapping(value, path, depth=depth)
    if isinstance(value, (list, tuple)):
        return [
            _safe_value(item, f"{path}[{index}]", depth=depth + 1)
            for index, item in enumerate(value)
        ]
    if isinstance(value, str):
        if len(value.encode("utf-8")) > _MAX_PROJECTION_STRING:
            raise _UnsafeProjection(f"{path} exceeds the string limit")
        if _ABSOLUTE_PATH_PATTERN.search(value) is not None:
            raise _UnsafeProjection(f"{path} contains an absolute path")
        if any(
            pattern.search(value)
            for pattern in _PROHIBITED_VALUE_PATTERNS
        ):
            raise _UnsafeProjection(
                f"{path} contains a prohibited command or query"
            )
        return value
    if isinstance(value, bool) or value is None or isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _UnsafeProjection(f"{path} contains a non-finite number")
        return value
    raise _UnsafeProjection(f"{path} contains an unsupported value")


def _report_status(
    report: Mapping[str, Any] | None,
) -> tuple[ProviderStatus, bool]:
    if report is None:
        return ProviderStatus.NOT_APPLICABLE, False
    generation = report.get("generation")
    if not isinstance(generation, Mapping):
        raise _UnsafeProjection(
            "report generation metadata is required"
        )
    try:
        provider_status = ProviderStatus(generation.get("mode"))
    except ValueError:
        raise _UnsafeProjection(
            "report generation mode is not supported"
        ) from None
    degraded = generation.get("degraded")
    if not isinstance(degraded, bool):
        raise _UnsafeProjection(
            "report degraded state must be a boolean"
        )
    return provider_status, degraded
