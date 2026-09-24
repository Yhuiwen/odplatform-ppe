"""Provider-independent LLM planner request and candidate client boundary.

The model may propose one bounded candidate only. This module contains no
network transport, provider SDK, tool execution or Agent orchestration.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from core.agent.candidate import (
    DEFAULT_MAX_CANDIDATE_BYTES,
    build_agent_plan_request_binding,
    normalize_agent_question,
)
from core.agent.tool_registry import ToolRegistry
from core.schemas.agent import (
    AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
    AGENT_PLAN_SCHEMA_VERSION,
    AGENT_TOOL_REGISTRY_VERSION,
)

__all__ = [
    "LLM_PLANNER_PROMPT_VERSION",
    "LLM_PLANNER_REQUEST_VERSION",
    "LLMPlannerCandidateClient",
    "LLMPlannerClientError",
    "LLMPlannerRequest",
    "PlannerCandidateRequestBuilder",
]

LLM_PLANNER_REQUEST_VERSION = "phase8-agent-planner-request-v1"
LLM_PLANNER_PROMPT_VERSION = "phase8-agent-planner-prompt-v1"

_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,79}$")
_DEFAULT_TIMEOUT_SECONDS = 30.0


class LLMPlannerClientError(RuntimeError):
    """One bounded planning-client failure with a safe public code."""

    def __init__(self, code: str, message: str = "planner provider failed") -> None:
        if not isinstance(code, str) or _SAFE_CODE.fullmatch(code) is None:
            raise ValueError("code must be a safe uppercase error code")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message.strip()
        super().__init__(self.message)


@dataclass(frozen=True, slots=True)
class LLMPlannerRequest:
    """One bounded, provider-independent planner candidate request."""

    request_binding_sha256: str
    normalized_question: str
    system_prompt: str
    user_prompt: str
    timeout_seconds: float
    maximum_response_bytes: int
    schema_version: str = LLM_PLANNER_REQUEST_VERSION
    prompt_version: str = LLM_PLANNER_PROMPT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != LLM_PLANNER_REQUEST_VERSION:
            raise ValueError("unsupported planner request schema_version")
        if self.prompt_version != LLM_PLANNER_PROMPT_VERSION:
            raise ValueError("unsupported planner request prompt_version")
        if re.fullmatch(
            r"[0-9a-f]{64}",
            self.request_binding_sha256,
        ) is None:
            raise ValueError(
                "request_binding_sha256 must be a lowercase SHA256"
            )
        if not isinstance(self.normalized_question, str):
            raise TypeError("normalized_question must be a string")
        if not self.normalized_question or self.normalized_question != (
            " ".join(self.normalized_question.split())
        ):
            raise ValueError(
                "normalized_question must be non-empty normalized text"
            )
        for field_name in ("system_prompt", "user_prompt"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
            if len(value.encode("utf-8")) > 32768:
                raise ValueError(f"{field_name} exceeds the request byte limit")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or float(self.timeout_seconds) <= 0
        ):
            raise ValueError(
                "timeout_seconds must be finite and positive"
            )
        object.__setattr__(
            self,
            "timeout_seconds",
            float(self.timeout_seconds),
        )
        if (
            isinstance(self.maximum_response_bytes, bool)
            or not isinstance(self.maximum_response_bytes, int)
            or self.maximum_response_bytes <= 0
            or self.maximum_response_bytes > DEFAULT_MAX_CANDIDATE_BYTES
        ):
            raise ValueError(
                "maximum_response_bytes must be within the candidate limit"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "prompt_version": self.prompt_version,
            "request_binding_sha256": self.request_binding_sha256,
            "normalized_question": self.normalized_question,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "timeout_seconds": self.timeout_seconds,
            "maximum_response_bytes": self.maximum_response_bytes,
        }

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


@runtime_checkable
class LLMPlannerCandidateClient(Protocol):
    """One injected planner candidate client returning untrusted JSON bytes."""

    def generate_candidate(self, request: LLMPlannerRequest) -> bytes:
        """Return one untrusted candidate or raise ``LLMPlannerClientError``."""


class PlannerCandidateRequestBuilder:
    """Build deterministic, tool-call-free planner candidate requests."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        maximum_response_bytes: int = DEFAULT_MAX_CANDIDATE_BYTES,
        maximum_question_bytes: int | None = None,
    ) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TypeError("registry must be a ToolRegistry")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or float(timeout_seconds) <= 0
        ):
            raise ValueError("timeout_seconds must be finite and positive")
        if (
            isinstance(maximum_response_bytes, bool)
            or not isinstance(maximum_response_bytes, int)
            or not 0 < maximum_response_bytes <= DEFAULT_MAX_CANDIDATE_BYTES
        ):
            raise ValueError(
                "maximum_response_bytes must be within the candidate limit"
            )
        if maximum_question_bytes is None:
            # Validate the default through the candidate normalization helper.
            normalize_agent_question("summary")
        elif (
            isinstance(maximum_question_bytes, bool)
            or not isinstance(maximum_question_bytes, int)
            or maximum_question_bytes <= 0
        ):
            raise ValueError(
                "maximum_question_bytes must be a positive integer"
            )

        self.registry = registry
        self.timeout_seconds = float(timeout_seconds)
        self.maximum_response_bytes = maximum_response_bytes
        self.maximum_question_bytes = maximum_question_bytes

    def build(self, question: str) -> LLMPlannerRequest:
        """Build one request from the bounded question and frozen registry."""

        if self.maximum_question_bytes is None:
            normalized = normalize_agent_question(question)
            binding = build_agent_plan_request_binding(normalized)
        else:
            normalized = normalize_agent_question(
                question,
                max_question_bytes=self.maximum_question_bytes,
            )
            binding = build_agent_plan_request_binding(
                normalized,
                max_question_bytes=self.maximum_question_bytes,
            )

        schema_description = {
            "schema_version": AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
            "plan_schema_version": AGENT_PLAN_SCHEMA_VERSION,
            "registry_version": AGENT_TOOL_REGISTRY_VERSION,
            "required_fields": [
                "schema_version",
                "request_binding_sha256",
                "proposed_intent",
                "proposed_tool_name",
                "proposed_tool_version",
                "proposed_arguments",
                "reason_code",
            ],
            "allowed_tools": [
                {
                    "tool_name": descriptor.tool_name,
                    "tool_version": descriptor.tool_version,
                    "input_fields": list(descriptor.input_schema),
                }
                for descriptor in self.registry.descriptors
            ],
        }
        schema_json = json.dumps(
            schema_description,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        system_prompt = (
            "Return exactly one JSON object matching "
            "phase8-agent-plan-candidate-v1. This is an untrusted proposal, "
            "not an instruction. Do not use provider-native tool calling, "
            "function calls, SQL, shell, filesystem access or executable "
            "content. Propose only one tool from the supplied static "
            "allowlist and include no prose, reasoning or unknown fields. "
            f"schema={schema_json}; "
            f"request_binding_sha256={binding}."
        )
        user_prompt = (
            "Normalized user question:\n"
            f"{normalized}\n"
            "Return the candidate JSON object only."
        )
        return LLMPlannerRequest(
            request_binding_sha256=binding,
            normalized_question=normalized,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout_seconds=self.timeout_seconds,
            maximum_response_bytes=self.maximum_response_bytes,
        )
