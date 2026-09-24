"""Deterministic request construction for the Phase 8 provider boundary."""

from __future__ import annotations

import json

from core.schemas.safety import (
    CONTEXT_SCHEMA_VERSION,
    SafetyAnalysisContext,
)
from core.schemas.safety_report import REPORT_SCHEMA_VERSION
from infra.llm.provider import (
    DEFAULT_RESPONSE_MAX_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    PROVIDER_PROMPT_VERSION,
    PROVIDER_REQUEST_VERSION,
    ProviderMessage,
    ProviderRequest,
)
from infra.llm.report_schema_prompt import REPORT_SCHEMA_DESCRIPTION_JSON
from services.safety_context_builder import SafetyContextBuilder

__all__ = [
    "ProviderRequestBuilder",
    "PROVIDER_REQUEST_INSTRUCTIONS",
]


PROVIDER_REQUEST_INSTRUCTIONS = (
    "Generate one machine-readable JSON object only. Do not wrap it in "
    "Markdown or prose. Output no text before or after the JSON object. "
    "Use only fields defined by phase8-report-v1; do not introduce additional "
    "fields. Include every required field, including nullable fields and "
    "empty arrays. Follow the exact nested field names, enum values and "
    "schema constraints supplied below. Preserve source_context_sha256 "
    "exactly. The supplied phase8-context-v1 payload is the authoritative "
    "source. Do not invent events, tracks, metrics, evidence, person identity, "
    "duration, alert-delivery data, paths, secrets or unsupported facts. "
    "Return a phase8-report-v1 provider candidate with generation.mode=LLM, "
    "generation.degraded=false, generation.failure_code=null and "
    "grounding_status=unvalidated. Treat recommendations as advisory. "
    "track_id values are tracker-scoped and are not stable person identity."
)


class ProviderRequestBuilder:
    """Build deterministic provider requests from P8-1 context."""

    def __init__(
        self,
        *,
        provider_ref: str,
        model_ref: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        maximum_response_bytes: int = DEFAULT_RESPONSE_MAX_BYTES,
    ) -> None:
        self.provider_ref = provider_ref
        self.model_ref = model_ref
        self.timeout_seconds = timeout_seconds
        self.maximum_response_bytes = maximum_response_bytes
        self.request_version = PROVIDER_REQUEST_VERSION
        self.prompt_version = PROVIDER_PROMPT_VERSION
        self.expected_report_schema_version = REPORT_SCHEMA_VERSION
        # Validate labels and policy through the frozen request constructor.
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        ProviderRequest(
            provider_ref=self.provider_ref,
            model_ref=self.model_ref,
            timeout_seconds=self.timeout_seconds,
            maximum_response_bytes=self.maximum_response_bytes,
            source_context_sha256="0" * 64,
            safe_context_canonical_json='{"calculated_metrics":[],'
            '"metadata":{},"observed_facts":[],'
            '"unavailable_fields":[]}',
            messages=(
                ProviderMessage(role="system", content="system"),
                ProviderMessage(role="user", content="user"),
            ),
        )

    def build(self, context: SafetyAnalysisContext) -> ProviderRequest:
        """Build one request without wall-clock, random or provider values."""

        if not isinstance(context, SafetyAnalysisContext):
            raise TypeError("context must be a SafetyAnalysisContext")

        fingerprint = SafetyContextBuilder.fingerprint(context)
        payload = context.to_dict()
        metadata = dict(payload["metadata"])
        metadata.pop("generated_at", None)
        payload["metadata"] = metadata
        context_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

        system_message = (
            f"{PROVIDER_REQUEST_INSTRUCTIONS}\n"
            "phase8-report-v1 compact JSON Schema description:\n"
            f"{REPORT_SCHEMA_DESCRIPTION_JSON}\n"
            f"request_version={PROVIDER_REQUEST_VERSION}; "
            f"prompt_version={PROVIDER_PROMPT_VERSION}; "
            f"context_version={CONTEXT_SCHEMA_VERSION}; "
            f"expected_report_schema_version={REPORT_SCHEMA_VERSION}; "
            f"source_context_sha256={fingerprint}."
        )
        user_message = (
            f"{CONTEXT_SCHEMA_VERSION} authoritative payload:\n"
            f"{context_json}"
        )
        return ProviderRequest(
            provider_ref=self.provider_ref,
            model_ref=self.model_ref,
            timeout_seconds=self.timeout_seconds,
            maximum_response_bytes=self.maximum_response_bytes,
            source_context_sha256=fingerprint,
            safe_context_canonical_json=context_json,
            messages=(
                ProviderMessage(role="system", content=system_message),
                ProviderMessage(role="user", content=user_message),
            ),
        )
