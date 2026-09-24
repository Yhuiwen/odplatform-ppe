from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable

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
from infra.llm.fallback import TemplateFallback, TemplateFallbackError
from infra.llm.llm_client import SafetyLLMClient
from infra.llm.provider import (
    DEFAULT_RESPONSE_MAX_BYTES,
    PROVIDER_PROMPT_VERSION,
    ProviderErrorCode,
    ProviderRequest,
    ProviderTransportError,
    TransportResponse,
)
from infra.llm.request_builder import ProviderRequestBuilder
from services.report_service import (
    ReportGenerationPath,
    ReportGenerationStatus,
    ReportService,
)
from services.safety_context_builder import SafetyContextBuilder

FIXED_CLOCK = lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)


def _fact(
    event_id: str,
    *,
    occurred_at: str,
    event_type: ComplianceEventType,
    track_id: int,
    snapshot_ref: str | None = None,
) -> SafetyEventFact:
    return SafetyEventFact(
        fact_id=f"EVT:{event_id}",
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        confidence=0.91,
        track_id=track_id,
        source_ref=source_reference("mp4:demo.mp4"),
        status=EventStatus.OPEN,
        snapshot_ref=snapshot_ref,
        evidence_available=snapshot_ref is not None,
    )


def _context(*, empty: bool = False) -> SafetyAnalysisContext:
    facts = (
        ()
        if empty
        else (
            _fact(
                "EVT-A",
                occurred_at="2026-09-23T12:00:00Z",
                event_type=ComplianceEventType.NO_HELMET,
                track_id=7,
                snapshot_ref="20260923/event_EVT-A.jpg",
            ),
            _fact(
                "EVT-B",
                occurred_at="2026-09-23T13:00:00Z",
                event_type=ComplianceEventType.NO_VEST,
                track_id=8,
            ),
        )
    )
    query = SafetyAnalyticsQuery(
        start_at="2026-09-23T00:00:00Z",
        end_at="2026-09-23T23:59:59Z",
    )
    analytics = SafetyAnalyticsResult(
        query=query,
        facts=facts,
        counts_by_type=tuple(
            (
                event_type,
                sum(1 for fact in facts if fact.event_type is event_type),
            )
            for event_type in ComplianceEventType
        ),
        counts_by_status=tuple(
            (
                status,
                sum(1 for fact in facts if fact.status is status),
            )
            for status in EventStatus
        ),
        counts_by_track=tuple(
            (
                track_id,
                sum(1 for fact in facts if fact.track_id == track_id),
            )
            for track_id in sorted({fact.track_id for fact in facts})
        ),
        counts_by_day=tuple(
            (
                day,
                sum(1 for fact in facts if fact.occurred_at.startswith(day)),
            )
            for day in sorted({fact.occurred_at[:10] for fact in facts})
        ),
        counts_by_source_ref=tuple(
            (
                reference,
                sum(1 for fact in facts if fact.source_ref == reference),
            )
            for reference in sorted(
                {
                    fact.source_ref
                    for fact in facts
                    if fact.source_ref is not None
                }
            )
        ),
        first_occurrence=(
            None
            if not facts
            else min(fact.occurred_at for fact in facts)
        ),
        last_occurrence=(
            None
            if not facts
            else max(fact.occurred_at for fact in facts)
        ),
        evidence_available_count=sum(
            1 for fact in facts if fact.evidence_available
        ),
        evidence_missing_count=sum(
            1 for fact in facts if not fact.evidence_available
        ),
        unavailable_fields=(
            UnavailableField(
                field="metrics.violation_duration",
                reason_code="NO_PERSISTED_DURATION_FIELD",
                reason="No persisted violation-duration field exists.",
            ),
        ),
    )
    return SafetyContextBuilder(clock=FIXED_CLOCK).build(analytics)


def _provider_report(context: SafetyAnalysisContext):
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


def _response(report: object) -> TransportResponse:
    return TransportResponse(
        status_code=200,
        body=report.to_canonical_json().encode("utf-8"),
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


def _client(
    transport: FakeTransport,
    *,
    maximum_response_bytes: int = DEFAULT_RESPONSE_MAX_BYTES,
) -> SafetyLLMClient:
    return SafetyLLMClient(
        transport=transport,
        request_builder=ProviderRequestBuilder(
            provider_ref="fake-provider",
            model_ref="fake-model",
            timeout_seconds=12.5,
            maximum_response_bytes=maximum_response_bytes,
        ),
    )


def _assert_fallback(
    result,
    *,
    expected_code: str,
) -> None:
    assert result.status is ReportGenerationStatus.TEMPLATE_FALLBACK
    assert result.generation_path is ReportGenerationPath.TEMPLATE_FALLBACK
    assert result.degraded is True
    assert result.report is not None
    assert result.report.generation.mode is GenerationMode.TEMPLATE_FALLBACK
    assert result.report.generation.degraded is True
    assert result.report.grounding_status is GroundingStatus.VALID
    assert result.grounding_status is GroundingStatus.VALID
    assert result.safe_error is not None
    assert result.safe_error.code == expected_code


def test_provider_valid_report_returns_provider_path_not_degraded() -> None:
    context = _context()
    transport = FakeTransport(response=_response(_provider_report(context)))

    result = ReportService().generate_provider_or_fallback(
        context,
        _client(transport),
    )

    assert result.status is ReportGenerationStatus.PROVIDER_VALIDATED
    assert result.generation_path is ReportGenerationPath.PROVIDER
    assert result.degraded is False
    assert result.report is not None
    assert result.report.generation.mode is GenerationMode.LLM
    assert result.report.grounding_status is GroundingStatus.VALID
    assert result.grounding_status is GroundingStatus.VALID
    assert result.safe_error is None
    assert result.provider_metadata is not None
    assert result.provider_metadata.provider_ref == "fake-provider"
    assert result.provider_metadata.model_ref == "fake-model"
    assert len(transport.requests) == 1


def _changed_report(
    context: SafetyAnalysisContext,
    case: str,
):
    report = _provider_report(context)
    if case == "fabricated_event":
        first = report.key_findings[0]
        return replace(
            report,
            key_findings=(
                replace(first, event_refs=("EVT-MISSING",)),
                *report.key_findings[1:],
            ),
        )
    if case == "fabricated_track":
        first = report.key_findings[0]
        return replace(
            report,
            key_findings=(
                replace(first, track_refs=(TrackReference(track_id=999),)),
                *report.key_findings[1:],
            ),
        )
    if case == "numeric_mismatch":
        first = report.key_findings[0]
        numeric = first.numeric_claims[0]
        return replace(
            report,
            key_findings=(
                replace(
                    first,
                    numeric_claims=(
                        replace(numeric, value=numeric.value + 1),
                    ),
                ),
                *report.key_findings[1:],
            ),
        )
    if case == "path_leak":
        first = report.key_findings[0]
        return replace(
            report,
            key_findings=(
                replace(
                    first,
                    statement=r"Evidence was read from C:\private\event.jpg",
                ),
                *report.key_findings[1:],
            ),
        )
    raise AssertionError(f"unknown case: {case}")


@pytest.mark.parametrize(
    ("case", "expected_code"),
    [
        ("fabricated_event", "GROUNDING_REJECTED"),
        ("fabricated_track", "GROUNDING_REJECTED"),
        ("numeric_mismatch", "GROUNDING_REJECTED"),
        ("path_leak", "GROUNDING_REJECTED"),
    ],
)
def test_semantic_provider_failures_route_to_template_fallback(
    case: str,
    expected_code: str,
) -> None:
    context = _context()
    report = _changed_report(context, case)

    result = ReportService().generate_provider_or_fallback(
        context,
        _client(FakeTransport(response=_response(report))),
    )

    _assert_fallback(result, expected_code=expected_code)
    assert result.report is not None
    assert result.report.generation.mode is not GenerationMode.LLM


def test_parser_rejections_route_to_template_fallback() -> None:
    context = _context()
    valid_payload = _provider_report(context).to_dict()

    cases = (
        (
            b"{not-json",
            "PROVIDER_MALFORMED_RESPONSE",
        ),
        (
            json.dumps({**valid_payload, "unexpected": True}).encode("utf-8"),
            "REPORT_SCHEMA_INVALID",
        ),
        (
            json.dumps(
                {**valid_payload, "source_context_sha256": "0" * 64}
            ).encode("utf-8"),
            "REPORT_SCHEMA_INVALID",
        ),
    )
    for body, expected_code in cases:
        result = ReportService().generate_provider_or_fallback(
            context,
            _client(FakeTransport(response=TransportResponse(200, body))),
        )
        _assert_fallback(result, expected_code=expected_code)


@pytest.mark.parametrize(
    ("response", "error", "expected_code"),
    [
        (
            None,
            ProviderTransportError(
                ProviderErrorCode.PROVIDER_TIMEOUT,
                "timeout detail",
            ),
            "PROVIDER_TIMEOUT",
        ),
        (
            None,
            ProviderTransportError(
                ProviderErrorCode.PROVIDER_AUTH_ERROR,
                "auth detail",
            ),
            "PROVIDER_AUTH_ERROR",
        ),
        (
            None,
            ProviderTransportError(
                ProviderErrorCode.PROVIDER_RATE_LIMITED,
                "rate detail",
            ),
            "PROVIDER_RATE_LIMITED",
        ),
        (
            None,
            ProviderTransportError(
                ProviderErrorCode.PROVIDER_HTTP_ERROR,
                "http detail",
            ),
            "PROVIDER_HTTP_ERROR",
        ),
        (
            None,
            ProviderTransportError(
                ProviderErrorCode.PROVIDER_UNAVAILABLE,
                "unavailable detail",
            ),
            "PROVIDER_UNAVAILABLE",
        ),
        (
            TransportResponse(200, b""),
            None,
            "PROVIDER_EMPTY_RESPONSE",
        ),
        (
            TransportResponse(
                200,
                b"x" * (DEFAULT_RESPONSE_MAX_BYTES + 1),
            ),
            None,
            "PROVIDER_RESPONSE_TOO_LARGE",
        ),
    ],
)
def test_operational_provider_failures_route_to_template_fallback(
    response: TransportResponse | None,
    error: ProviderTransportError | None,
    expected_code: str,
) -> None:
    result = ReportService().generate_provider_or_fallback(
        _context(),
        _client(FakeTransport(response=response, error=error)),
    )

    _assert_fallback(result, expected_code=expected_code)


class _FailingFallback(TemplateFallback):
    def generate(self, context: SafetyAnalysisContext):
        raise TemplateFallbackError(
            code="FALLBACK_FAILED",
            message="fallback fixture failed",
        )


def test_fallback_failure_returns_report_unavailable_without_report() -> None:
    context = _context()
    transport = FakeTransport(
        error=ProviderTransportError(
            ProviderErrorCode.PROVIDER_UNAVAILABLE,
            "unavailable detail",
        )
    )

    result = ReportService(fallback=_FailingFallback()).generate_provider_or_fallback(
        context,
        _client(transport),
    )

    assert result.status is ReportGenerationStatus.REPORT_UNAVAILABLE
    assert result.generation_path is ReportGenerationPath.UNAVAILABLE
    assert result.degraded is True
    assert result.report is None
    assert result.grounding_status is None
    assert result.safe_error is not None
    assert result.safe_error.code == "FALLBACK_FAILED"


def test_zero_event_context_works_for_provider_and_fallback_paths() -> None:
    context = _context(empty=True)
    provider_result = ReportService().generate_provider_or_fallback(
        context,
        _client(FakeTransport(response=_response(_provider_report(context)))),
    )
    fallback_result = ReportService().generate_provider_or_fallback(
        context,
        _client(
            FakeTransport(
                error=ProviderTransportError(
                    ProviderErrorCode.PROVIDER_UNAVAILABLE,
                    "unavailable detail",
                )
            )
        ),
    )

    assert provider_result.status is ReportGenerationStatus.PROVIDER_VALIDATED
    assert provider_result.report is not None
    assert provider_result.report.key_findings[0].metric_refs
    _assert_fallback(fallback_result, expected_code="PROVIDER_UNAVAILABLE")
    assert fallback_result.report is not None
    assert fallback_result.report.executive_summary


def test_safe_error_does_not_contain_transport_secret() -> None:
    secret = "api_key=not-a-real-secret"
    result = ReportService().generate_provider_or_fallback(
        _context(),
        _client(
            FakeTransport(
                error=ProviderTransportError(
                    ProviderErrorCode.PROVIDER_AUTH_ERROR,
                    secret,
                )
            )
        ),
    )

    rendered = json.dumps(result.to_dict(), ensure_ascii=False)
    assert secret not in rendered
    assert "Authorization" not in rendered


def test_orchestration_result_serialization_contains_only_safe_metadata() -> None:
    context = _context()
    result = ReportService().generate_provider_or_fallback(
        context,
        _client(FakeTransport(response=_response(_provider_report(context)))),
    )
    payload = result.to_dict()

    assert payload["status"] == "PROVIDER_VALIDATED"
    assert payload["generation_path"] == "PROVIDER"
    assert payload["grounding_status"] == "valid"
    assert payload["safe_error"] is None
    assert payload["provider_metadata"] == {
        "provider_ref": "fake-provider",
        "model_ref": "fake-model",
        "request_version": "phase8-provider-request-v1",
        "prompt_version": PROVIDER_PROMPT_VERSION,
        "report_schema_version": "phase8-report-v1",
    }
    assert "api_key" not in json.dumps(payload).lower()
    assert "authorization" not in json.dumps(payload).lower()


def test_invalid_provider_candidate_never_escapes_report_service() -> None:
    context = _context()
    invalid = _changed_report(context, "fabricated_event")

    result = ReportService().generate_provider_or_fallback(
        context,
        _client(FakeTransport(response=_response(invalid))),
    )

    assert result.report is not None
    assert result.report.generation.mode is GenerationMode.TEMPLATE_FALLBACK
    assert result.report.source_context_sha256 == (
        SafetyContextBuilder.fingerprint(context)
    )
