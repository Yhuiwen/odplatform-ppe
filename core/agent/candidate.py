"""Strict parsing and validation for untrusted Agent plan candidates."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Mapping

from core.agent.permissions import (
    ToolPermissionError,
    ToolPermissionPolicy,
)
from core.agent.planner import (
    DEFAULT_MAX_QUESTION_BYTES,
    AgentPlanningError,
    DeterministicAgentPlanner,
)
from core.agent.tool_registry import ToolRegistry, ToolRegistryError
from core.schemas.agent import (
    AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
    AGENT_PLAN_SCHEMA_VERSION,
    AGENT_REQUEST_SCHEMA_VERSION,
    AGENT_TOOL_REGISTRY_VERSION,
    AgentIntent,
    AgentPlan,
    AgentPlanCandidate,
    AgentPlanCandidateReason,
    ToolEffect,
    ToolExecutionContext,
)

__all__ = [
    "AgentPlanCandidateError",
    "AgentPlanCandidateParser",
    "AgentPlanCandidateValidator",
    "DEFAULT_MAX_CANDIDATE_BYTES",
    "build_agent_plan_request_binding",
    "normalize_agent_question",
]

DEFAULT_MAX_CANDIDATE_BYTES = 16384
DEFAULT_MAX_CANDIDATE_STRING_BYTES = 2048
DEFAULT_MAX_CANDIDATE_NODES = 128

_CANDIDATE_FIELDS = frozenset(
    {
        "schema_version",
        "request_binding_sha256",
        "proposed_intent",
        "proposed_tool_name",
        "proposed_tool_version",
        "proposed_arguments",
        "reason_code",
    }
)
_SUPPORTED_INTENT_TOOL = {
    AgentIntent.SAFETY_SUMMARY: "get_safety_summary",
    AgentIntent.EVENT_STATISTICS: "get_event_statistics",
    AgentIntent.EVENT_DETAIL: "get_event_details",
    AgentIntent.SAFETY_REPORT: "generate_safety_report",
}
_INTENT_PROXY_QUESTION = {
    AgentIntent.SAFETY_SUMMARY: "safety summary",
    AgentIntent.EVENT_STATISTICS: "event statistics",
    AgentIntent.EVENT_DETAIL: "show event details",
    AgentIntent.SAFETY_REPORT: "generate a safety report",
}
_REASON_FOR_INTENT = {
    AgentIntent.SAFETY_SUMMARY: (
        AgentPlanCandidateReason.SUMMARY_REQUEST
    ),
    AgentIntent.EVENT_STATISTICS: (
        AgentPlanCandidateReason.STATISTICS_REQUEST
    ),
    AgentIntent.EVENT_DETAIL: (
        AgentPlanCandidateReason.EVENT_DETAIL_REQUEST
    ),
    AgentIntent.SAFETY_REPORT: (
        AgentPlanCandidateReason.REPORT_REQUEST
    ),
}
_FORBIDDEN_MARKERS = re.compile(
    r"(?:sql|shell|command|filesystem|file_system|mutat|delete|drop|"
    r"truncate|execute|override|admin)",
    re.IGNORECASE,
)
_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(
        r"\b(?:select\s+.+\s+from|insert\s+into|update\s+.+\s+set|"
        r"delete\s+from|drop\s+(?:table|database)|truncate\s+table)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:^|\s)(?:/etc|/proc|/sys|c:\\windows)(?:[\\/]|\s|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:rm\s+-rf|cmd(?:\.exe)?\s+/c|powershell(?:\.exe)?\s+-|"
        r"bash\s+-c|sh\s+-c)\b",
        re.IGNORECASE,
    ),
)
_SEMANTIC_VERSION = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$"
)


class _DuplicateKeyError(ValueError):
    pass


class AgentPlanCandidateError(RuntimeError):
    """A fail-closed candidate parsing or validation error."""

    def __init__(self, code: str, message: str) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message
        super().__init__(message)


def normalize_agent_question(
    question: str,
    *,
    max_question_bytes: int = DEFAULT_MAX_QUESTION_BYTES,
) -> str:
    """Normalize a question with the same bounded shape as the planner."""

    if not isinstance(question, str):
        raise AgentPlanCandidateError(
            "INVALID_REQUEST",
            "question must be a UTF-8 string",
        )
    if (
        isinstance(max_question_bytes, bool)
        or not isinstance(max_question_bytes, int)
        or max_question_bytes <= 0
    ):
        raise ValueError("max_question_bytes must be a positive integer")
    normalized = " ".join(question.split())
    if not normalized:
        raise AgentPlanCandidateError(
            "INVALID_REQUEST",
            "question cannot be empty",
        )
    if len(normalized.encode("utf-8")) > max_question_bytes:
        raise AgentPlanCandidateError(
            "INVALID_REQUEST",
            "question exceeds the frozen byte limit",
        )
    return normalized


def build_agent_plan_request_binding(
    question: str,
    *,
    max_question_bytes: int = DEFAULT_MAX_QUESTION_BYTES,
) -> str:
    """Build the deterministic digest that binds a candidate to a request."""

    normalized = normalize_agent_question(
        question,
        max_question_bytes=max_question_bytes,
    )
    question_sha256 = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()
    payload = {
        "request_schema_version": AGENT_REQUEST_SCHEMA_VERSION,
        "plan_schema_version": AGENT_PLAN_SCHEMA_VERSION,
        "registry_version": AGENT_TOOL_REGISTRY_VERSION,
        "question_sha256": question_sha256,
        "intent_tool_order": [
            {
                "intent": intent.value,
                "tool_name": tool_name,
            }
            for intent, tool_name in _SUPPORTED_INTENT_TOOL.items()
        ],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AgentPlanCandidateParser:
    """Parse only a bounded, exact JSON ``phase8-agent-plan-candidate-v1``."""

    def __init__(
        self,
        *,
        maximum_candidate_bytes: int = DEFAULT_MAX_CANDIDATE_BYTES,
        maximum_string_bytes: int = DEFAULT_MAX_CANDIDATE_STRING_BYTES,
        maximum_nodes: int = DEFAULT_MAX_CANDIDATE_NODES,
    ) -> None:
        for field_name, value in (
            ("maximum_candidate_bytes", maximum_candidate_bytes),
            ("maximum_string_bytes", maximum_string_bytes),
            ("maximum_nodes", maximum_nodes),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):
                raise ValueError(
                    f"{field_name} must be a positive integer"
                )
        self.maximum_candidate_bytes = maximum_candidate_bytes
        self.maximum_string_bytes = maximum_string_bytes
        self.maximum_nodes = maximum_nodes

    def parse(self, raw_candidate: bytes) -> AgentPlanCandidate:
        """Parse an untrusted candidate without repairing malformed output."""

        if not isinstance(raw_candidate, bytes):
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate must be raw UTF-8 bytes",
            )
        if not raw_candidate:
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate is empty",
            )
        if len(raw_candidate) > self.maximum_candidate_bytes:
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate exceeds the configured byte limit",
            )
        try:
            text = raw_candidate.decode("utf-8")
        except UnicodeDecodeError:
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate must be strict UTF-8",
            ) from None
        if not text.strip():
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate is empty",
            )
        if text.startswith("\ufeff"):
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate must not contain a BOM",
            )

        try:
            payload = json.loads(
                text,
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_non_finite_constant,
            )
        except _DuplicateKeyError:
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate contains duplicate JSON keys",
            ) from None
        except (json.JSONDecodeError, ValueError):
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate is not valid strict JSON",
            ) from None

        self._validate_json_tree(payload)
        try:
            candidate = _build_candidate(payload)
        except AgentPlanCandidateError:
            raise
        except (TypeError, ValueError):
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate does not satisfy "
                "phase8-agent-plan-candidate-v1",
            ) from None
        return candidate

    def _validate_json_tree(self, payload: Any) -> None:
        node_count = 0
        stack: list[tuple[Any, int]] = [(payload, 0)]
        while stack:
            value, depth = stack.pop()
            node_count += 1
            if node_count > self.maximum_nodes:
                raise AgentPlanCandidateError(
                    "INVALID_CANDIDATE",
                    "candidate exceeds the configured node limit",
                )
            if depth > 4:
                raise AgentPlanCandidateError(
                    "INVALID_CANDIDATE",
                    "candidate exceeds the configured nesting limit",
                )
            if isinstance(value, str):
                if len(value.encode("utf-8")) > self.maximum_string_bytes:
                    raise AgentPlanCandidateError(
                        "INVALID_CANDIDATE",
                        "candidate contains an oversized string",
                    )
            elif isinstance(value, bool) or value is None:
                continue
            elif isinstance(value, int):
                if abs(value) > 2**63 - 1:
                    raise AgentPlanCandidateError(
                        "INVALID_CANDIDATE",
                        "candidate contains an out-of-range integer",
                    )
            elif isinstance(value, float):
                if not math.isfinite(value):
                    raise AgentPlanCandidateError(
                        "INVALID_CANDIDATE",
                        "candidate contains a non-finite number",
                    )
            elif isinstance(value, list):
                stack.extend((item, depth + 1) for item in value)
            elif isinstance(value, dict):
                for key, item in value.items():
                    if not isinstance(key, str):
                        raise AgentPlanCandidateError(
                            "INVALID_CANDIDATE",
                            "candidate object keys must be strings",
                        )
                    stack.append((key, depth + 1))
                    stack.append((item, depth + 1))
            else:
                raise AgentPlanCandidateError(
                    "INVALID_CANDIDATE",
                    "candidate contains an unsupported JSON value",
                )


class AgentPlanCandidateValidator:
    """Convert a strictly parsed candidate into one validated AgentPlan."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        policy: ToolPermissionPolicy | None = None,
        planner: DeterministicAgentPlanner | None = None,
        max_question_bytes: int = DEFAULT_MAX_QUESTION_BYTES,
    ) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TypeError("registry must be a ToolRegistry")
        if policy is not None and not isinstance(
            policy,
            ToolPermissionPolicy,
        ):
            raise TypeError("policy must be a ToolPermissionPolicy or None")
        if planner is not None and not isinstance(
            planner,
            DeterministicAgentPlanner,
        ):
            raise TypeError(
                "planner must be a DeterministicAgentPlanner or None"
            )
        if (
            isinstance(max_question_bytes, bool)
            or not isinstance(max_question_bytes, int)
            or max_question_bytes <= 0
        ):
            raise ValueError("max_question_bytes must be a positive integer")

        self.registry = registry
        self.policy = policy or ToolPermissionPolicy()
        self.planner = planner or DeterministicAgentPlanner(
            registry,
            policy=self.policy,
            max_question_bytes=max_question_bytes,
        )
        self.max_question_bytes = max_question_bytes

    def validate(
        self,
        candidate: AgentPlanCandidate,
        *,
        question: str,
        context: ToolExecutionContext,
    ) -> AgentPlan:
        """Validate candidate semantics and return a new non-executable plan."""

        if not isinstance(candidate, AgentPlanCandidate):
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate must be an AgentPlanCandidate",
            )
        if not isinstance(context, ToolExecutionContext):
            raise AgentPlanCandidateError(
                "INVALID_REQUEST",
                "a validated Agent execution context is required",
            )

        normalized_question = normalize_agent_question(
            question,
            max_question_bytes=self.max_question_bytes,
        )
        expected_binding = build_agent_plan_request_binding(
            normalized_question,
            max_question_bytes=self.max_question_bytes,
        )
        if candidate.request_binding_sha256 != expected_binding:
            raise AgentPlanCandidateError(
                "INVALID_REQUEST_BINDING",
                "candidate request binding does not match the request",
            )

        intent = candidate.proposed_intent
        if intent not in _SUPPORTED_INTENT_TOOL:
            raise AgentPlanCandidateError(
                "UNKNOWN_INTENT",
                "candidate intent is not supported by the deterministic "
                "planner",
            )
        expected_tool_name = _SUPPORTED_INTENT_TOOL[intent]
        expected_reason = _REASON_FOR_INTENT[intent]
        if candidate.reason_code is not expected_reason:
            raise AgentPlanCandidateError(
                "INVALID_CANDIDATE",
                "candidate reason_code does not match the proposed intent",
            )

        deterministic_intent = self.planner.classify(normalized_question)
        if deterministic_intent is AgentIntent.FORBIDDEN_REQUEST:
            raise AgentPlanCandidateError(
                "FORBIDDEN_REQUEST",
                "the request asks for a mutation, administration or "
                "system action outside the read-only Agent scope",
            )
        if (
            deterministic_intent in _SUPPORTED_INTENT_TOOL
            and deterministic_intent is not intent
        ):
            raise AgentPlanCandidateError(
                "INTENT_CONFLICT",
                "candidate conflicts with the deterministic intent",
            )

        self._reject_forbidden_candidate_fields(candidate)
        try:
            tool = self.registry.resolve(
                candidate.proposed_tool_name,
                candidate.proposed_tool_version,
            )
        except ToolRegistryError as exc:
            raise AgentPlanCandidateError(exc.code, exc.message) from exc
        if not tool.descriptor.enabled:
            raise AgentPlanCandidateError(
                "TOOL_DISABLED",
                "candidate tool is disabled by the frozen registry",
            )
        if tool.descriptor.effect is not ToolEffect.READ_ONLY:
            raise AgentPlanCandidateError(
                "FORBIDDEN_CAPABILITY",
                "candidate tool is not read-only",
            )
        if candidate.proposed_tool_name != expected_tool_name:
            raise AgentPlanCandidateError(
                "INTENT_TOOL_MISMATCH",
                "candidate tool does not match the frozen intent mapping",
            )

        try:
            self.policy.authorize(
                context,
                tool.descriptor.required_capabilities,
            )
        except ToolPermissionError as exc:
            raise AgentPlanCandidateError(exc.code, exc.message) from exc

        period, filters = self._split_arguments(
            candidate.proposed_arguments,
            allowed_fields=tool.descriptor.input_schema,
        )
        proxy_question = _INTENT_PROXY_QUESTION[intent]
        try:
            validated_plan = self.planner.plan(
                (
                    normalized_question
                    if deterministic_intent in _SUPPORTED_INTENT_TOOL
                    else proxy_question
                ),
                context=context,
                requested_period=period,
                filters=filters,
            )
        except AgentPlanningError as exc:
            raise AgentPlanCandidateError(exc.code, exc.message) from exc

        if (
            validated_plan.tool_name != candidate.proposed_tool_name
            or validated_plan.tool_version
            != candidate.proposed_tool_version
        ):
            raise AgentPlanCandidateError(
                "INTENT_TOOL_MISMATCH",
                "validated plan does not match the candidate tool identity",
            )

        question_sha256 = hashlib.sha256(
            normalized_question.encode("utf-8")
        ).hexdigest()
        return AgentPlan(
            intent=validated_plan.intent,
            tool_name=validated_plan.tool_name,
            tool_version=validated_plan.tool_version,
            arguments=validated_plan.arguments,
            question_sha256=question_sha256,
        )

    @staticmethod
    def _reject_forbidden_candidate_fields(
        candidate: AgentPlanCandidate,
    ) -> None:
        if _FORBIDDEN_MARKERS.search(candidate.proposed_tool_name):
            raise AgentPlanCandidateError(
                "FORBIDDEN_CAPABILITY",
                "candidate requests a forbidden tool capability",
            )
        for key, value in candidate.proposed_arguments.items():
            if _FORBIDDEN_MARKERS.search(key):
                raise AgentPlanCandidateError(
                    "FORBIDDEN_CAPABILITY",
                    "candidate contains a forbidden argument capability",
                )
            if isinstance(value, str) and any(
                pattern.search(value)
                for pattern in _FORBIDDEN_VALUE_PATTERNS
            ):
                raise AgentPlanCandidateError(
                    "FORBIDDEN_CAPABILITY",
                    "candidate argument contains a forbidden payload",
                )

    @staticmethod
    def _split_arguments(
        arguments: Mapping[str, Any],
        *,
        allowed_fields: tuple[str, ...],
    ) -> tuple[dict[str, str] | None, dict[str, Any]]:
        if not isinstance(arguments, Mapping):
            raise AgentPlanCandidateError(
                "INVALID_ARGUMENTS",
                "candidate arguments must be a mapping",
            )
        allowed = set(allowed_fields)
        for key in arguments:
            if not isinstance(key, str) or key not in allowed:
                if isinstance(key, str) and _FORBIDDEN_MARKERS.search(key):
                    raise AgentPlanCandidateError(
                        "FORBIDDEN_CAPABILITY",
                        "candidate contains a forbidden argument capability",
                    )
                raise AgentPlanCandidateError(
                    "INVALID_ARGUMENTS",
                    "candidate arguments contain an unsupported field",
                )

        has_start = "start_at" in arguments
        has_end = "end_at" in arguments
        if has_start != has_end:
            raise AgentPlanCandidateError(
                "INVALID_ARGUMENTS",
                "candidate period requires both start_at and end_at",
            )
        period = (
            {
                "start_at": arguments["start_at"],
                "end_at": arguments["end_at"],
            }
            if has_start
            else None
        )
        filters = {
            key: value
            for key, value in arguments.items()
            if key not in {"start_at", "end_at"}
        }
        return period, filters


def _build_candidate(payload: Any) -> AgentPlanCandidate:
    candidate = _object(payload, "candidate", _CANDIDATE_FIELDS)
    if (
        candidate["schema_version"]
        != AGENT_PLAN_CANDIDATE_SCHEMA_VERSION
    ):
        raise ValueError("unsupported candidate schema_version")

    request_binding_sha256 = _string(
        candidate["request_binding_sha256"],
        "request_binding_sha256",
    )
    if re.fullmatch(r"[0-9a-f]{64}", request_binding_sha256) is None:
        raise ValueError(
            "request_binding_sha256 must be a lowercase SHA256"
        )

    proposed_intent_value = _string(
        candidate["proposed_intent"],
        "proposed_intent",
    )
    try:
        proposed_intent = AgentIntent(proposed_intent_value)
    except ValueError:
        raise ValueError("unsupported proposed_intent") from None

    proposed_tool_name = _string(
        candidate["proposed_tool_name"],
        "proposed_tool_name",
    )
    proposed_tool_version = _string(
        candidate["proposed_tool_version"],
        "proposed_tool_version",
    )
    if _SEMANTIC_VERSION.fullmatch(proposed_tool_version) is None:
        raise ValueError("proposed_tool_version must be a semantic version")
    proposed_arguments = _object_value(
        candidate["proposed_arguments"],
        "proposed_arguments",
    )

    reason_value = _string(candidate["reason_code"], "reason_code")
    try:
        reason_code = AgentPlanCandidateReason(reason_value)
    except ValueError:
        raise ValueError("unsupported reason_code") from None

    return AgentPlanCandidate(
        request_binding_sha256=request_binding_sha256,
        proposed_intent=proposed_intent,
        proposed_tool_name=proposed_tool_name,
        proposed_tool_version=proposed_tool_version,
        proposed_arguments=proposed_arguments,
        reason_code=reason_code,
    )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate key: {key}")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _object(
    value: Any,
    path: str,
    expected_fields: frozenset[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{path} must be an object")
    actual_fields = set(value)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        unknown = sorted(actual_fields - expected_fields)
        raise ValueError(
            f"{path} has invalid fields; missing={missing}, unknown={unknown}"
        )
    return value


def _object_value(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{path} must be an object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{path} must be a non-empty string")
    return value.strip()
