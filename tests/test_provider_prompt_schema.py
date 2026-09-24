from __future__ import annotations

import json
from dataclasses import fields
from typing import Any

import pytest

from core.schemas.safety import ReportingPeriod
from core.schemas.safety_report import (
    REPORT_SCHEMA_VERSION,
    ClaimKind,
    GenerationMode,
    GroundingStatus,
    MetricNumericClaim,
    ReportEvidenceReference,
    ReportGeneration,
    ReportLimitation,
    ReportRecommendation,
    SafetyReportClaim,
    StructuredSafetyReport,
    TrackReference,
)
from infra.llm.provider import (
    PROVIDER_PROMPT_VERSION,
    ProviderError,
    ProviderErrorCode,
    TransportResponse,
)
from infra.llm.report_schema_prompt import REPORT_SCHEMA_DESCRIPTION
from infra.llm.request_builder import ProviderRequestBuilder
from services.report_service import ReportService
from services.safety_context_builder import SafetyContextBuilder
from services.safety_report_grounding_validator import (
    SafetyReportGroundingValidator,
)
import tests.test_provider_e2e as e2e


def _request():
    return ProviderRequestBuilder(
        provider_ref="fake-provider",
        model_ref="fake-model",
        timeout_seconds=12.5,
        maximum_response_bytes=262144,
    ).build(e2e._context())


def _prompt_schema(request) -> dict[str, Any]:
    marker = "compact JSON Schema description:\n"
    system_message = request.messages[0].content
    assert marker in system_message
    schema_text = system_message.split(marker, maxsplit=1)[1].split(
        "\nrequest_version=",
        maxsplit=1,
    )[0]
    return json.loads(schema_text)


def _field_names(model: type[Any]) -> set[str]:
    return {field.name for field in fields(model)}


def _assert_object_is_closed(schema: dict[str, Any]) -> None:
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]).issubset(schema["properties"])


def test_prompt_contains_complete_authoritative_top_level_schema() -> None:
    request = _request()
    prompt_schema = _prompt_schema(request)

    assert request.prompt_version == PROVIDER_PROMPT_VERSION
    assert PROVIDER_PROMPT_VERSION == "phase8-provider-prompt-v2"
    assert prompt_schema == REPORT_SCHEMA_DESCRIPTION
    assert set(prompt_schema["required"]) == _field_names(
        StructuredSafetyReport
    )
    assert set(prompt_schema["properties"]) == _field_names(
        StructuredSafetyReport
    )
    assert "$defs" in prompt_schema
    _assert_object_is_closed(prompt_schema)


def test_prompt_generation_fields_and_provider_success_rules_are_exact() -> None:
    schema = _prompt_schema(_request())
    generation = schema["properties"]["generation"]
    generation_properties = generation["properties"]

    assert set(generation["required"]) == _field_names(ReportGeneration)
    assert set(generation_properties) == _field_names(ReportGeneration)
    assert generation_properties["mode"]["enum"] == [
        item.value for item in GenerationMode
    ]
    assert generation_properties["degraded"] == {"type": "boolean"}
    assert {
        "type": "null"
    } in generation_properties["provider_ref"]["anyOf"]
    assert {
        "type": "null"
    } in generation_properties["failure_code"]["anyOf"]

    rules = schema["x-phase8-rules"]
    assert rules["nullableButRequired"] == [
        "$.generation.provider_ref",
        "$.generation.failure_code",
    ]
    assert rules["providerCandidateRequirements"] == {
        "$.schema_version": REPORT_SCHEMA_VERSION,
        "$.generation.mode": GenerationMode.LLM.value,
        "$.generation.degraded": False,
        "$.generation.failure_code": None,
        "$.grounding_status": GroundingStatus.UNVALIDATED.value,
    }


def test_prompt_requires_all_nested_fields_and_candidate_enums() -> None:
    schema = _prompt_schema(_request())
    definitions = schema["$defs"]

    assert set(schema["properties"]["reporting_period"]["required"]) == (
        _field_names(ReportingPeriod) | {"interval_semantics"}
    )
    assert set(definitions["observationClaim"]["required"]) == (
        _field_names(SafetyReportClaim)
    )
    assert definitions["observationClaim"]["properties"]["kind"] == {
        "const": ClaimKind.OBSERVATION.value
    }
    assert definitions["riskClaim"]["properties"]["kind"] == {
        "const": ClaimKind.RISK.value
    }
    assert set(definitions["trackReference"]["required"]) == (
        _field_names(TrackReference)
    )
    assert definitions["trackReference"]["properties"]["track_scope"] == {
        "const": "tracker_scoped"
    }
    assert set(definitions["numericClaim"]["required"]) == (
        _field_names(MetricNumericClaim)
    )
    assert set(definitions["recommendation"]["required"]) == (
        _field_names(ReportRecommendation)
    )
    assert set(definitions["evidenceReference"]["required"]) == (
        _field_names(ReportEvidenceReference) | {"track_scope"}
    )
    assert definitions["evidenceReference"]["properties"]["track_scope"] == {
        "const": "tracker_scoped"
    }
    assert set(definitions["limitation"]["required"]) == (
        _field_names(ReportLimitation)
    )
    assert schema["properties"]["grounding_status"]["enum"] == [
        item.value for item in GroundingStatus
    ]


def test_prompt_prohibits_additional_fields_and_allows_empty_arrays() -> None:
    schema = _prompt_schema(_request())

    object_schemas = [
        schema,
        schema["properties"]["reporting_period"],
        schema["properties"]["generation"],
        *schema["$defs"].values(),
    ]
    for object_schema in object_schemas:
        _assert_object_is_closed(object_schema)

    rules = schema["x-phase8-rules"]
    assert rules["additionalFields"] == "forbidden at every object"
    assert "executive_summary" in rules["emptyArraysAllowed"]
    assert "evidence_references" in rules["emptyArraysAllowed"]
    assert "requiredFieldPolicy" in rules
    assert "referencePolicy" in rules


def test_request_construction_with_schema_is_deterministic() -> None:
    first = _request()
    second = _request()

    assert first.to_canonical_json() == second.to_canonical_json()
    assert first.source_context_sha256 == SafetyContextBuilder.fingerprint(
        e2e._context()
    )
    assert "phase8-provider-prompt-v1" not in first.messages[0].content


def _deepseek_like_malformed_payload(context) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "source_context_sha256": SafetyContextBuilder.fingerprint(context),
        "reporting_period": {
            "start_at": "2026-09-23T00:00:00Z",
            "end_at": "2026-09-23T23:59:59Z",
            "interval_semantics": "[start_at,end_at]",
        },
        "generation": {
            "mode": GenerationMode.LLM.value,
            "degraded": False,
            "model": "deepseek-flash",
            "temperature": 0,
            "stream": False,
            "provider": "openai-compatible",
            "request_id": "fixture-request",
            "prompt_version": "phase8-provider-prompt-v1",
            "request_version": "phase8-provider-request-v1",
            "schema_version": REPORT_SCHEMA_VERSION,
            "generated_at": "2026-09-24T00:00:00Z",
            "finish_reason": "stop",
        },
        "summary": "Provider-style summary",
        "findings": [],
        "incidents": [],
        "suggestions": [],
        "evidence": [],
        "metadata": {},
        "analysis": {},
        "risk_level": "unknown",
    }


def test_known_deepseek_like_malformed_fixture_still_fails_closed() -> None:
    context = e2e._context()
    body = json.dumps(
        _deepseek_like_malformed_payload(context)
    ).encode("utf-8")
    client = e2e._client(
        e2e.FakeTransport(response=TransportResponse(200, body))
    )

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is ProviderErrorCode.REPORT_SCHEMA_INVALID
    assert error.value.schema_diagnostics is not None
    diagnostics = {
        item.path: item.code.value
        for item in error.value.schema_diagnostics.diagnostics
    }
    assert diagnostics["$.evidence_references"] == "MISSING_FIELD"
    assert diagnostics["$.executive_summary"] == "MISSING_FIELD"
    assert diagnostics["$.generation.failure_code"] == "MISSING_FIELD"
    assert diagnostics["$.generation.provider_ref"] == "MISSING_FIELD"


def test_schema_conforming_fixture_parses_and_reaches_grounding() -> None:
    context = e2e._context()
    report = e2e._provider_report(context)
    client = e2e._client(
        e2e.FakeTransport(response=e2e._response(report))
    )

    candidate = client.generate_report(context)

    assert candidate.to_dict() == report.to_dict()

    class RecordingValidator(SafetyReportGroundingValidator):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def validate(self, report, context):
            self.calls += 1
            return super().validate(report, context)

    validator = RecordingValidator()
    result = ReportService(validator=validator).generate_provider_report(
        context,
        client,
    )

    assert validator.calls == 1
    assert result.valid
    assert result.candidate.report.generation.mode is GenerationMode.LLM
