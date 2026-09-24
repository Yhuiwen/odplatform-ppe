from __future__ import annotations

import json

import pytest

from core.schemas.safety_report import REPORT_SCHEMA_VERSION, GenerationMode
from infra.llm.provider import (
    ProviderError,
    ProviderErrorCode,
    SchemaDiagnosticCode,
    TransportResponse,
)
from infra.llm.config import LLMProviderConfig
import scripts.run_p8_5_provider_smoke as smoke
from scripts.run_p8_5_provider_smoke import SmokeReport
from services.report_service import (
    ReportGenerationPath,
    ReportGenerationStatus,
    ReportService,
)
import tests.test_provider_e2e as e2e


def _payload() -> dict[str, object]:
    context = e2e._context()
    return e2e._provider_report(context).to_dict()


def _parse_error(payload: dict[str, object]) -> ProviderError:
    context = e2e._context()
    client = e2e._client(
        e2e.FakeTransport(
            response=TransportResponse(
                200,
                json.dumps(payload).encode("utf-8"),
            )
        )
    )
    with pytest.raises(ProviderError) as error:
        client.generate_report(context)
    assert error.value.code is ProviderErrorCode.REPORT_SCHEMA_INVALID
    assert error.value.schema_diagnostics is not None
    return error.value


def _diagnostic_tuples(error: ProviderError) -> list[tuple[str, str]]:
    assert error.schema_diagnostics is not None
    return [
        (item.path, item.code.value)
        for item in error.schema_diagnostics.diagnostics
    ]


def test_missing_required_field_diagnostic() -> None:
    payload = _payload()
    payload.pop("schema_version")

    error = _parse_error(payload)

    assert (
        "$.schema_version",
        SchemaDiagnosticCode.MISSING_FIELD.value,
    ) in _diagnostic_tuples(error)


def test_wrong_primitive_type_diagnostic() -> None:
    payload = _payload()
    payload["schema_version"] = 7

    error = _parse_error(payload)

    assert (
        "$.schema_version",
        SchemaDiagnosticCode.INVALID_TYPE.value,
    ) in _diagnostic_tuples(error)
    assert error.schema_diagnostics is not None
    diagnostic = next(
        item
        for item in error.schema_diagnostics.diagnostics
        if item.path == "$.schema_version"
    )
    assert diagnostic.expected == "string"
    assert diagnostic.actual_type == "integer"


def test_invalid_enum_diagnostic() -> None:
    payload = _payload()
    generation = payload["generation"]
    assert isinstance(generation, dict)
    generation["mode"] = "NOT_LLM"

    error = _parse_error(payload)

    assert (
        "$.generation.mode",
        SchemaDiagnosticCode.INVALID_ENUM.value,
    ) in _diagnostic_tuples(error)


def test_nested_array_json_path_diagnostic() -> None:
    payload = _payload()
    findings = payload["key_findings"]
    assert isinstance(findings, list)
    assert isinstance(findings[0], dict)
    findings[0]["claim_id"] = 9

    error = _parse_error(payload)

    assert (
        "$.key_findings[0].claim_id",
        SchemaDiagnosticCode.INVALID_TYPE.value,
    ) in _diagnostic_tuples(error)


def test_multiple_diagnostics_are_deterministic_and_ordered() -> None:
    first = _payload()
    first.pop("schema_version")
    generation = first["generation"]
    findings = first["key_findings"]
    assert isinstance(generation, dict)
    assert isinstance(findings, list)
    assert isinstance(findings[0], dict)
    generation["mode"] = "NOT_LLM"
    findings[0]["claim_id"] = 9

    second = dict(reversed(list(first.items())))
    first_error = _parse_error(first)
    second_error = _parse_error(second)

    assert _diagnostic_tuples(first_error) == _diagnostic_tuples(second_error)
    assert _diagnostic_tuples(first_error) == sorted(_diagnostic_tuples(first_error))


def test_diagnostic_count_limit_and_truncated_flag() -> None:
    payload = _payload()
    payload["key_findings"] = [{} for _ in range(25)]

    error = _parse_error(payload)

    assert error.schema_diagnostics is not None
    assert len(error.schema_diagnostics.diagnostics) == 20
    assert error.schema_diagnostics.truncated is True


def test_no_invalid_field_value_is_exposed() -> None:
    secret_value = "sk-" + "A" * 24
    payload = _payload()
    generation = payload["generation"]
    assert isinstance(generation, dict)
    generation["mode"] = secret_value

    error = _parse_error(payload)
    rendered = json.dumps(error.to_dict(), ensure_ascii=False)

    assert secret_value not in rendered
    assert "NOT_LLM" not in rendered
    assert error.schema_diagnostics is not None
    assert all(
        item.actual_type == "string"
        for item in error.schema_diagnostics.diagnostics
        if item.path == "$.generation.mode"
    )


def test_no_raw_response_or_unexpected_field_name_is_exposed() -> None:
    raw_marker = "provider-raw-response-marker"
    unexpected_field_name = "unexpected_provider_field_name"
    payload = _payload()
    payload[unexpected_field_name] = raw_marker

    error = _parse_error(payload)
    rendered = json.dumps(error.to_dict(), ensure_ascii=False)

    assert raw_marker not in rendered
    assert unexpected_field_name not in rendered
    assert (
        "$.<unexpected>",
        SchemaDiagnosticCode.UNEXPECTED_FIELD.value,
    ) in _diagnostic_tuples(error)


def test_no_api_key_value_is_exposed() -> None:
    api_key = "sk-" + "B" * 24
    payload = _payload()
    payload["api_key"] = api_key

    error = _parse_error(payload)
    rendered = f"{error!r} {error!s} {json.dumps(error.to_dict())}"

    assert api_key not in rendered
    assert "Authorization" not in rendered


def test_invalid_provider_report_still_routes_to_valid_fallback() -> None:
    context = e2e._context()
    payload = _payload()
    payload["schema_version"] = 7
    result = ReportService().generate_provider_or_fallback(
        context,
        e2e._client(
            e2e.FakeTransport(
                response=TransportResponse(
                    200,
                    json.dumps(payload).encode("utf-8"),
                )
            )
        ),
    )

    assert result.status is ReportGenerationStatus.TEMPLATE_FALLBACK
    assert result.generation_path is ReportGenerationPath.TEMPLATE_FALLBACK
    assert result.degraded is True
    assert result.report is not None
    assert result.report.generation.mode is GenerationMode.TEMPLATE_FALLBACK
    assert result.safe_error is not None
    assert result.safe_error.code == "REPORT_SCHEMA_INVALID"
    assert result.safe_error.schema_diagnostics is not None
    assert result.grounding_status is not None
    assert result.grounding_status.value == "valid"


def test_smoke_report_serializes_only_sanitized_diagnostics() -> None:
    error = _parse_error({"schema_version": 7})
    assert error.schema_diagnostics is not None
    report = SmokeReport(
        status="TEMPLATE_FALLBACK",
        reason="provider path used safe fallback",
        provider_ref="fake-provider",
        model_ref="fake-model",
        generation_path="TEMPLATE_FALLBACK",
        degraded=True,
        grounding_status="valid",
        safe_error_code="REPORT_SCHEMA_INVALID",
        schema_diagnostics=[
            item.to_dict()
            for item in error.schema_diagnostics.diagnostics
        ],
        schema_diagnostics_truncated=False,
    )

    rendered = json.dumps(report.to_dict(), ensure_ascii=False)

    assert "schema_diagnostics" in rendered
    assert "$.schema_version" in rendered
    assert "schema_version\":7" not in rendered
    assert REPORT_SCHEMA_VERSION == "phase8-report-v1"


def test_smoke_cli_prints_sanitized_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _payload()
    payload["schema_version"] = 7
    body = json.dumps(payload).encode("utf-8")
    config = LLMProviderConfig(
        schema_version="phase8-llm-config-v1",
        provider_ref="fake-provider",
        endpoint="http://127.0.0.1:9999/v1/chat/completions",
        model_ref="fake-model",
        api_key_env="PPE_LLM_API_KEY",
        api_key="test-secret",
        timeout_seconds=12.5,
        maximum_response_bytes=262144,
        response_format_json_object=True,
    )
    monkeypatch.setattr(
        smoke.LLMProviderConfig,
        "from_file",
        classmethod(lambda cls, path: config),
    )
    monkeypatch.setattr(
        smoke,
        "OpenAICompatibleChatTransport",
        lambda config: e2e.FakeTransport(
            response=TransportResponse(200, body)
        ),
    )

    exit_code = smoke.main(["--execute"])
    rendered = capsys.readouterr().out
    output = json.loads(rendered)

    assert exit_code == 0
    assert output["safe_error_code"] == "REPORT_SCHEMA_INVALID"
    assert output["schema_diagnostics"][0]["path"] == "$.schema_version"
    assert output["schema_diagnostics"][0]["actual_type"] == "integer"
    assert "schema_version\":7" not in rendered
    assert "test-secret" not in rendered
