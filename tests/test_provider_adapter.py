from __future__ import annotations

import ast
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus
from core.schemas.safety import (
    SafetyAnalysisContext,
    SafetyAnalyticsQuery,
    SafetyAnalyticsResult,
    SafetyEventFact,
    UnavailableField,
    source_reference,
)
from core.schemas.safety_report import (
    GenerationMode,
    GroundingStatus,
    ReportGeneration,
    TrackReference,
)
from infra.llm.fallback import TemplateFallback
from infra.llm.llm_client import SafetyLLMClient
from infra.llm.provider import (
    DEFAULT_RESPONSE_MAX_BYTES,
    PROVIDER_PROMPT_VERSION,
    PROVIDER_REQUEST_VERSION,
    ProviderError,
    ProviderErrorCode,
    ProviderRequest,
    ProviderTransportError,
    TransportResponse,
)
from infra.llm.request_builder import ProviderRequestBuilder
from infra.llm.response_parser import ProviderResponseParser
from services.report_service import ReportService
from services.safety_context_builder import SafetyContextBuilder

FIXED_CLOCK = lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)


def _fact(
    event_id: str,
    *,
    occurred_at: str,
    event_type: ComplianceEventType,
    track_id: int,
    snapshot_ref: str | None = None,
    source_ref: str | None = None,
) -> SafetyEventFact:
    return SafetyEventFact(
        fact_id=f"EVT:{event_id}",
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        confidence=0.91,
        track_id=track_id,
        source_ref=source_ref,
        status=EventStatus.OPEN,
        snapshot_ref=snapshot_ref,
        evidence_available=snapshot_ref is not None,
    )


def _context() -> SafetyAnalysisContext:
    source_ref = source_reference("mp4:demo.mp4")
    facts = (
        _fact(
            "EVT-A",
            occurred_at="2026-09-23T12:00:00Z",
            event_type=ComplianceEventType.NO_HELMET,
            track_id=7,
            snapshot_ref="20260923/event_EVT-A.jpg",
            source_ref=source_ref,
        ),
        _fact(
            "EVT-B",
            occurred_at="2026-09-23T13:00:00Z",
            event_type=ComplianceEventType.NO_VEST,
            track_id=8,
            source_ref=source_ref,
        ),
    )
    query = SafetyAnalyticsQuery(
        start_at="2026-09-23T00:00:00Z",
        end_at="2026-09-23T23:59:59Z",
    )
    counts_by_type = tuple(
        (
            event_type,
            sum(1 for fact in facts if fact.event_type is event_type),
        )
        for event_type in ComplianceEventType
    )
    counts_by_status = tuple(
        (
            status,
            sum(1 for fact in facts if fact.status is status),
        )
        for status in EventStatus
    )
    counts_by_track = tuple(
        (track_id, sum(1 for fact in facts if fact.track_id == track_id))
        for track_id in sorted({fact.track_id for fact in facts})
    )
    counts_by_day = tuple(
        (
            day,
            sum(1 for fact in facts if fact.occurred_at.startswith(day)),
        )
        for day in sorted({fact.occurred_at[:10] for fact in facts})
    )
    counts_by_source_ref = tuple(
        (source_ref, sum(1 for fact in facts if fact.source_ref == source_ref))
        for source_ref in sorted(
            {
                fact.source_ref
                for fact in facts
                if fact.source_ref is not None
            }
        )
    )
    analytics = SafetyAnalyticsResult(
        query=query,
        facts=facts,
        counts_by_type=counts_by_type,
        counts_by_status=counts_by_status,
        counts_by_track=counts_by_track,
        counts_by_day=counts_by_day,
        counts_by_source_ref=counts_by_source_ref,
        first_occurrence="2026-09-23T12:00:00Z",
        last_occurrence="2026-09-23T13:00:00Z",
        evidence_available_count=1,
        evidence_missing_count=1,
        unavailable_fields=(
            UnavailableField(
                field="metrics.violation_duration",
                reason_code="NO_PERSISTED_DURATION_FIELD",
                reason="No persisted violation-duration field exists.",
            ),
        ),
    )
    return SafetyContextBuilder(clock=FIXED_CLOCK).build(analytics)


def _provider_report(
    context: SafetyAnalysisContext,
) -> object:
    report = TemplateFallback().generate(context)
    return replace(
        report,
        generation=ReportGeneration(
            mode=GenerationMode.LLM,
            degraded=False,
            provider_ref="fake-provider",
            failure_code=None,
        ),
        grounding_status=GroundingStatus.UNVALIDATED,
    )


@dataclass
class FakeTransport:
    response: TransportResponse | None = None
    error: ProviderTransportError | None = None

    def __post_init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    def send(self, request: ProviderRequest) -> TransportResponse:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise AssertionError("fake transport has no response")
        return self.response


def _builder(
    *,
    provider_ref: str = "fake-provider",
    model_ref: str = "fake-model",
    maximum_response_bytes: int = DEFAULT_RESPONSE_MAX_BYTES,
) -> ProviderRequestBuilder:
    return ProviderRequestBuilder(
        provider_ref=provider_ref,
        model_ref=model_ref,
        timeout_seconds=12.5,
        maximum_response_bytes=maximum_response_bytes,
    )


def _client(
    transport: FakeTransport,
    *,
    maximum_response_bytes: int = DEFAULT_RESPONSE_MAX_BYTES,
) -> SafetyLLMClient:
    builder = _builder(maximum_response_bytes=maximum_response_bytes)
    return SafetyLLMClient(
        transport=transport,
        request_builder=builder,
    )


def _response(report: object) -> TransportResponse:
    return TransportResponse(
        status_code=200,
        body=report.to_canonical_json().encode("utf-8"),
    )


def test_request_construction_is_deterministic_safe_and_versioned() -> None:
    context = _context()
    request = _builder().build(context)
    changed_generated_at = replace(
        context,
        metadata=replace(
            context.metadata,
            generated_at="2026-09-25T00:00:00Z",
        ),
    )
    repeated = _builder().build(changed_generated_at)

    assert request.to_canonical_json() == repeated.to_canonical_json()
    assert request.request_version == PROVIDER_REQUEST_VERSION
    assert request.prompt_version == PROVIDER_PROMPT_VERSION
    assert request.expected_report_schema_version == "phase8-report-v1"
    assert request.source_context_sha256 == (
        SafetyContextBuilder.fingerprint(context)
    )
    assert request.timeout_seconds == 12.5
    assert request.maximum_response_bytes == DEFAULT_RESPONSE_MAX_BYTES


def test_request_contains_only_safe_context_sections() -> None:
    request = _builder().build(_context())
    payload = request.safe_context_payload
    encoded = request.to_canonical_json().lower()

    assert set(payload) == {
        "observed_facts",
        "calculated_metrics",
        "metadata",
        "unavailable_fields",
    }
    assert "generated_at" not in payload["metadata"]
    assert "c:\\" not in encoded
    assert "/var/" not in encoded
    assert "api_key" not in encoded
    assert "bearer " not in encoded
    assert '"raw_evidence_bytes":' not in encoded


def test_valid_provider_candidate_passes_unchanged_grounding_validator() -> None:
    context = _context()
    transport = FakeTransport(response=_response(_provider_report(context)))
    client = _client(transport)

    result = ReportService().generate_provider_report(context, client)

    assert result.valid
    assert result.candidate.report.generation.mode is GenerationMode.LLM
    assert result.candidate.report.generation.degraded is False
    assert result.candidate.report.grounding_status is (
        GroundingStatus.UNVALIDATED
    )
    assert result.request.provider_ref == "fake-provider"
    assert result.request.model_ref == "fake-model"
    assert len(transport.requests) == 1


def test_client_returns_unvalidated_candidate_report() -> None:
    context = _context()
    report = _provider_report(context)
    client = _client(FakeTransport(response=_response(report)))

    candidate = client.generate_report(context)

    assert candidate.to_canonical_json() == report.to_canonical_json()
    assert candidate.grounding_status is GroundingStatus.UNVALIDATED


@pytest.mark.parametrize(
    ("body", "code"),
    [
        (b"", ProviderErrorCode.PROVIDER_EMPTY_RESPONSE),
        (b"   ", ProviderErrorCode.PROVIDER_EMPTY_RESPONSE),
        (b"{not-json", ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE),
        (b'{"value": NaN}', ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE),
        (
            b'{"schema_version":"phase8-report-v1",'
            b'"schema_version":"phase8-report-v1"}',
            ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
        ),
    ],
)
def test_empty_malformed_and_duplicate_output_fail_closed(
    body: bytes,
    code: ProviderErrorCode,
) -> None:
    context = _context()
    client = _client(FakeTransport(response=TransportResponse(200, body)))

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is code


def test_oversized_output_fails_before_parsing() -> None:
    context = _context()
    body = b"x" * (DEFAULT_RESPONSE_MAX_BYTES + 1)
    client = _client(FakeTransport(response=TransportResponse(200, body)))

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is ProviderErrorCode.PROVIDER_RESPONSE_TOO_LARGE


def test_schema_invalid_unknown_field_is_rejected() -> None:
    context = _context()
    payload = _provider_report(context).to_dict()
    payload["unexpected"] = True
    body = json.dumps(payload).encode("utf-8")
    client = _client(FakeTransport(response=TransportResponse(200, body)))

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is ProviderErrorCode.REPORT_SCHEMA_INVALID


def test_fingerprint_mismatch_is_rejected_before_grounding() -> None:
    context = _context()
    payload = _provider_report(context).to_dict()
    payload["source_context_sha256"] = "0" * 64
    body = json.dumps(payload).encode("utf-8")
    client = _client(FakeTransport(response=TransportResponse(200, body)))

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is ProviderErrorCode.REPORT_SCHEMA_INVALID


def test_fabricated_event_reaches_grounding_and_is_rejected() -> None:
    context = _context()
    report = _provider_report(context)
    changed = replace(
        report,
        key_findings=(
            replace(
                report.key_findings[0],
                event_refs=("EVT-MISSING",),
            ),
            *report.key_findings[1:],
        ),
    )
    result = ReportService().generate_provider_report(
        context,
        _client(FakeTransport(response=_response(changed))),
    )

    assert not result.valid
    assert {
        issue.code for issue in result.validation.errors
    } >= {"UNKNOWN_EVENT_REFERENCE"}


def test_fabricated_track_reaches_grounding_and_is_rejected() -> None:
    context = _context()
    report = _provider_report(context)
    changed = replace(
        report,
        key_findings=(
            replace(
                report.key_findings[0],
                track_refs=(TrackReference(track_id=999),),
            ),
            *report.key_findings[1:],
        ),
    )
    result = ReportService().generate_provider_report(
        context,
        _client(FakeTransport(response=_response(changed))),
    )

    assert not result.valid
    assert {
        issue.code for issue in result.validation.errors
    } >= {"UNKNOWN_TRACK_REFERENCE"}


def test_numeric_contradiction_reaches_grounding_and_is_rejected() -> None:
    context = _context()
    report = _provider_report(context)
    first_claim = report.key_findings[0]
    original = first_claim.numeric_claims[0]
    changed = replace(
        report,
        key_findings=(
            replace(
                first_claim,
                numeric_claims=(
                    replace(original, value=original.value + 1),
                ),
            ),
            *report.key_findings[1:],
        ),
    )
    result = ReportService().generate_provider_report(
        context,
        _client(FakeTransport(response=_response(changed))),
    )

    assert not result.valid
    assert {
        issue.code for issue in result.validation.errors
    } >= {"NUMERIC_VALUE_MISMATCH"}


def test_path_leaking_output_reaches_grounding_and_is_rejected() -> None:
    context = _context()
    report = _provider_report(context)
    changed = replace(
        report,
        key_findings=(
            replace(
                report.key_findings[0],
                statement=r"Evidence was read from C:\private\event.jpg",
            ),
            *report.key_findings[1:],
        ),
    )
    result = ReportService().generate_provider_report(
        context,
        _client(FakeTransport(response=_response(changed))),
    )

    assert not result.valid
    assert {
        issue.code for issue in result.validation.errors
    } >= {"PATH_LEAK_DETECTED"}


@pytest.mark.parametrize(
    ("status_code", "code"),
    [
        (401, ProviderErrorCode.PROVIDER_AUTH_ERROR),
        (403, ProviderErrorCode.PROVIDER_AUTH_ERROR),
        (429, ProviderErrorCode.PROVIDER_RATE_LIMITED),
        (500, ProviderErrorCode.PROVIDER_HTTP_ERROR),
    ],
)
def test_http_status_errors_are_mapped_deterministically(
    status_code: int,
    code: ProviderErrorCode,
) -> None:
    context = _context()
    client = _client(
        FakeTransport(
            response=TransportResponse(status_code=status_code, body=b"ignored")
        )
    )

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is code
    assert error.value.provider_ref == "fake-provider"


def test_transport_timeout_is_mapped_without_network_access() -> None:
    context = _context()
    client = _client(
        FakeTransport(
            error=ProviderTransportError(
                ProviderErrorCode.PROVIDER_TIMEOUT,
                "upstream transport detail",
            )
        )
    )

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is ProviderErrorCode.PROVIDER_TIMEOUT
    assert "upstream transport detail" not in str(error.value)


def test_transport_error_does_not_leak_secret_or_raw_output() -> None:
    context = _context()
    secret = "api_key=not-a-real-secret"
    client = _client(
        FakeTransport(
            error=ProviderTransportError(
                ProviderErrorCode.PROVIDER_AUTH_ERROR,
                secret,
            )
        )
    )

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    rendered = f"{error.value!r} {error.value!s} {error.value.to_dict()}"
    assert secret not in rendered
    assert error.value.__cause__ is None


def test_mock_transport_performs_zero_network_access(monkeypatch) -> None:
    import socket

    def fail_socket(*args, **kwargs):
        raise AssertionError("network access is forbidden in P8-4")

    monkeypatch.setattr(socket, "socket", fail_socket)
    context = _context()
    transport = FakeTransport(response=_response(_provider_report(context)))

    result = ReportService().generate_provider_report(
        context,
        _client(transport),
    )

    assert result.valid
    assert len(transport.requests) == 1


def test_provider_modules_have_no_vendor_or_network_coupling() -> None:
    project_root = Path(__file__).resolve().parents[1]
    paths = (
        project_root / "infra" / "llm" / "provider.py",
        project_root / "infra" / "llm" / "request_builder.py",
        project_root / "infra" / "llm" / "response_parser.py",
        project_root / "infra" / "llm" / "llm_client.py",
    )
    forbidden = {
        "openai",
        "anthropic",
        "ollama",
        "langchain",
        "llama_index",
        "autogen",
        "crewai",
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert not {
            item
            for item in imports
            if any(
                item == name or item.startswith(f"{name}.")
                for name in forbidden
            )
        }


def test_provider_client_and_parser_do_not_fallback_or_mutate_contracts() -> None:
    context = _context()
    report = _provider_report(context)
    client = _client(FakeTransport(response=_response(report)))

    candidate = client.generate_report(context)
    result = ReportService().generate_provider_report(context, client)

    assert candidate.generation.mode is GenerationMode.LLM
    assert candidate.generation.degraded is False
    assert result.candidate.report.grounding_status is (
        GroundingStatus.UNVALIDATED
    )
    assert TemplateFallback().generate(context).generation.mode is (
        GenerationMode.TEMPLATE_FALLBACK
    )


def test_parser_rejects_provider_claim_of_prevalidated_grounding() -> None:
    from core.schemas.safety_report import StructuredSafetyReport

    context = _context()
    report = _provider_report(context)
    assert isinstance(report, StructuredSafetyReport)
    payload = report.to_dict()
    payload["grounding_status"] = "valid"
    client = _client(
        FakeTransport(
            response=TransportResponse(
                200,
                json.dumps(payload).encode("utf-8"),
            )
        )
    )

    with pytest.raises(ProviderError) as error:
        client.generate_report(context)

    assert error.value.code is ProviderErrorCode.REPORT_SCHEMA_INVALID
