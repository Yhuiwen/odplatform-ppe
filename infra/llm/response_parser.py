"""Strict parsing of untrusted provider output."""

from __future__ import annotations

import json
import math
import re
from typing import Any

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
from core.schemas.safety import ReportingPeriod
from infra.llm.provider import (
    DEFAULT_RESPONSE_MAX_BYTES,
    MAX_SCHEMA_DIAGNOSTICS,
    ProviderError,
    ProviderErrorCode,
    SchemaDiagnostic,
    SchemaDiagnosticCode,
    SchemaDiagnostics,
)

__all__ = ["ProviderResponseParser"]


_REPORT_FIELDS = frozenset(
    {
        "schema_version",
        "source_context_sha256",
        "reporting_period",
        "generation",
        "executive_summary",
        "key_findings",
        "risk_observations",
        "recommendations",
        "evidence_references",
        "limitations",
        "grounding_status",
    }
)
_PERIOD_FIELDS = frozenset(
    {"start_at", "end_at", "interval_semantics"}
)
_GENERATION_FIELDS = frozenset(
    {"mode", "degraded", "provider_ref", "failure_code"}
)
_CLAIM_FIELDS = frozenset(
    {
        "claim_id",
        "kind",
        "statement",
        "fact_refs",
        "metric_refs",
        "event_refs",
        "track_refs",
        "source_refs",
        "evidence_refs",
        "numeric_claims",
    }
)
_TRACK_FIELDS = frozenset({"track_id", "track_scope"})
_NUMERIC_FIELDS = frozenset({"metric_ref", "value"})
_RECOMMENDATION_FIELDS = frozenset(
    {
        "recommendation_id",
        "action",
        "priority",
        "basis_finding_refs",
        "basis_fact_refs",
        "basis_metric_refs",
    }
)
_EVIDENCE_FIELDS = frozenset(
    {
        "evidence_ref",
        "event_id",
        "track_id",
        "track_scope",
        "snapshot_ref",
        "occurred_at",
    }
)
_LIMITATION_FIELDS = frozenset(
    {"field", "reason_code", "statement"}
)


class _DuplicateKeyError(ValueError):
    pass


class ProviderResponseParser:
    """Parse only a bounded, strict JSON ``phase8-report-v1`` response."""

    def __init__(
        self,
        *,
        maximum_response_bytes: int = DEFAULT_RESPONSE_MAX_BYTES,
    ) -> None:
        if (
            isinstance(maximum_response_bytes, bool)
            or not isinstance(maximum_response_bytes, int)
            or maximum_response_bytes <= 0
        ):
            raise ValueError("maximum_response_bytes must be a positive integer")
        self.maximum_response_bytes = maximum_response_bytes

    def parse(
        self,
        raw_response: bytes,
        *,
        expected_context_sha256: str,
        expected_provider_ref: str | None = None,
    ) -> StructuredSafetyReport:
        """Parse and validate schema shape without accepting provider claims."""

        if not isinstance(raw_response, bytes):
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
                message="provider response must be raw bytes",
            )
        if not raw_response:
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_EMPTY_RESPONSE,
                message="provider response was empty",
            )
        if len(raw_response) > self.maximum_response_bytes:
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_RESPONSE_TOO_LARGE,
                message=(
                    "provider response exceeded the configured size limit"
                ),
            )
        try:
            text = raw_response.decode("utf-8")
        except UnicodeDecodeError:
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
                message="provider response was not strict UTF-8",
            ) from None
        if not text.strip():
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_EMPTY_RESPONSE,
                message="provider response was empty",
            )
        if text.startswith("\ufeff"):
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
                message="provider response must not contain a BOM",
            )

        try:
            payload = json.loads(
                text,
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_non_finite_constant,
            )
        except _DuplicateKeyError:
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
                message="provider response contains duplicate JSON keys",
            ) from None
        except (json.JSONDecodeError, ValueError):
            raise ProviderError(
                code=ProviderErrorCode.PROVIDER_MALFORMED_RESPONSE,
                message="provider response is not valid strict JSON",
            ) from None

        try:
            return self._build_report(
                payload,
                expected_context_sha256=expected_context_sha256,
                expected_provider_ref=expected_provider_ref,
            )
        except ProviderError:
            raise
        except (TypeError, ValueError):
            diagnostics = _diagnose_schema(
                payload,
                expected_context_sha256=expected_context_sha256,
                expected_provider_ref=expected_provider_ref,
            )
            if not diagnostics.diagnostics:
                diagnostics = SchemaDiagnostics(
                    diagnostics=(
                        SchemaDiagnostic(
                            path="$",
                            code=SchemaDiagnosticCode.SCHEMA_CONSTRUCTION_FAILED,
                            expected="valid phase8-report-v1",
                            actual_type=_json_type(payload),
                            constraint="construction_failed",
                        ),
                    ),
                )
            raise ProviderError(
                code=ProviderErrorCode.REPORT_SCHEMA_INVALID,
                message="provider response does not satisfy phase8-report-v1",
                schema_diagnostics=diagnostics,
            ) from None

    @staticmethod
    def _build_report(
        payload: Any,
        *,
        expected_context_sha256: str,
        expected_provider_ref: str | None,
    ) -> StructuredSafetyReport:
        report = _object(payload, "report", _REPORT_FIELDS)
        if report["schema_version"] != REPORT_SCHEMA_VERSION:
            raise ValueError("unsupported schema version")
        if (
            not isinstance(expected_context_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_context_sha256) is None
        ):
            raise ValueError("expected context fingerprint is malformed")
        if report["source_context_sha256"] != expected_context_sha256:
            raise ValueError("source context fingerprint mismatch")
        if report["grounding_status"] != GroundingStatus.UNVALIDATED.value:
            raise ValueError(
                "provider candidate must remain unvalidated before P8-2"
            )

        period = _object(
            report["reporting_period"],
            "reporting_period",
            _PERIOD_FIELDS,
        )
        if period["interval_semantics"] != "[start_at,end_at]":
            raise ValueError("unsupported reporting interval semantics")
        reporting_period = ReportingPeriod(
            _string(period["start_at"], "start_at"),
            _string(period["end_at"], "end_at"),
        )

        generation = _object(
            report["generation"],
            "generation",
            _GENERATION_FIELDS,
        )
        if generation["mode"] != GenerationMode.LLM.value:
            raise ValueError("provider candidate generation mode must be LLM")
        if generation["degraded"] is not False:
            raise ValueError("provider candidate cannot be marked degraded")
        if generation["failure_code"] is not None:
            raise ValueError("provider candidate cannot carry a failure code")
        provider_ref = generation["provider_ref"]
        if provider_ref is not None:
            provider_ref = _string(provider_ref, "provider_ref")
            if (
                expected_provider_ref is not None
                and provider_ref != expected_provider_ref
            ):
                raise ValueError("provider_ref does not match the request")

        executive_summary = _claims(
            report["executive_summary"],
            "executive_summary",
            expected_kind=ClaimKind.OBSERVATION,
        )
        key_findings = _claims(
            report["key_findings"],
            "key_findings",
            expected_kind=ClaimKind.OBSERVATION,
        )
        risk_observations = _claims(
            report["risk_observations"],
            "risk_observations",
            expected_kind=ClaimKind.RISK,
        )
        recommendations = _recommendations(report["recommendations"])
        evidence_references = _evidence_references(
            report["evidence_references"]
        )
        limitations = _limitations(report["limitations"])

        return StructuredSafetyReport(
            schema_version=REPORT_SCHEMA_VERSION,
            source_context_sha256=expected_context_sha256,
            reporting_period=reporting_period,
            generation=ReportGeneration(
                mode=GenerationMode.LLM,
                degraded=False,
                provider_ref=provider_ref,
                failure_code=None,
            ),
            executive_summary=executive_summary,
            key_findings=key_findings,
            risk_observations=risk_observations,
            recommendations=recommendations,
            evidence_references=evidence_references,
            limitations=limitations,
            grounding_status=GroundingStatus.UNVALIDATED,
        )


class _SchemaDiagnosticCollector:
    def __init__(
        self,
        maximum_errors: int = MAX_SCHEMA_DIAGNOSTICS,
    ) -> None:
        self.maximum_errors = maximum_errors
        self.truncated = False
        self._diagnostics: list[SchemaDiagnostic] = []

    def add(
        self,
        *,
        path: str,
        code: SchemaDiagnosticCode,
        expected: str,
        actual_value: Any,
        constraint: str | None = None,
    ) -> None:
        if len(self._diagnostics) >= self.maximum_errors:
            self.truncated = True
            return
        self._diagnostics.append(
            SchemaDiagnostic(
                path=path,
                code=code,
                expected=expected,
                actual_type=_json_type(actual_value),
                constraint=constraint,
            )
        )

    def finish(self) -> SchemaDiagnostics:
        ordered = tuple(
            sorted(
                self._diagnostics,
                key=lambda item: (
                    item.path,
                    item.code.value,
                    item.expected,
                    item.actual_type,
                    item.constraint or "",
                ),
            )
        )
        return SchemaDiagnostics(
            diagnostics=ordered,
            truncated=self.truncated,
            maximum_errors=self.maximum_errors,
        )


def _diagnose_schema(
    payload: Any,
    *,
    expected_context_sha256: str,
    expected_provider_ref: str | None,
) -> SchemaDiagnostics:
    collector = _SchemaDiagnosticCollector()
    report = _diagnose_object(
        collector,
        payload,
        "$",
        _REPORT_FIELDS,
    )
    if report is None:
        return collector.finish()

    if "schema_version" in report:
        schema_version = _diagnose_string(
            collector,
            report["schema_version"],
            "$.schema_version",
        )
        if (
            schema_version is not None
            and schema_version != REPORT_SCHEMA_VERSION
        ):
            collector.add(
                path="$.schema_version",
                code=SchemaDiagnosticCode.INVALID_ENUM,
                expected=REPORT_SCHEMA_VERSION,
                actual_value=schema_version,
                constraint="exact",
            )

    if "source_context_sha256" in report:
        fingerprint = _diagnose_string(
            collector,
            report["source_context_sha256"],
            "$.source_context_sha256",
        )
        if fingerprint is not None:
            if re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
                collector.add(
                    path="$.source_context_sha256",
                    code=SchemaDiagnosticCode.INVALID_FORMAT,
                    expected="lowercase SHA256",
                    actual_value=fingerprint,
                    constraint="64_hex",
                )
            elif fingerprint != expected_context_sha256:
                collector.add(
                    path="$.source_context_sha256",
                    code=SchemaDiagnosticCode.INVALID_VALUE,
                    expected="request context fingerprint",
                    actual_value=fingerprint,
                    constraint="context_binding",
                )

    if "grounding_status" in report:
        grounding_status = _diagnose_string(
            collector,
            report["grounding_status"],
            "$.grounding_status",
        )
        if (
            grounding_status is not None
            and grounding_status != GroundingStatus.UNVALIDATED.value
        ):
            collector.add(
                path="$.grounding_status",
                code=SchemaDiagnosticCode.INVALID_ENUM,
                expected=GroundingStatus.UNVALIDATED.value,
                actual_value=grounding_status,
                constraint="provider_candidate_only",
            )

    if "reporting_period" in report:
        _diagnose_reporting_period(
            collector,
            report["reporting_period"],
        )
    if "generation" in report:
        _diagnose_generation(
            collector,
            report["generation"],
            expected_provider_ref=expected_provider_ref,
        )

    claim_specs = (
        ("executive_summary", ClaimKind.OBSERVATION),
        ("key_findings", ClaimKind.OBSERVATION),
        ("risk_observations", ClaimKind.RISK),
    )
    for field_name, expected_kind in claim_specs:
        if field_name in report:
            _diagnose_claims(
                collector,
                report[field_name],
                f"$.{field_name}",
                expected_kind=expected_kind,
            )
    if "recommendations" in report:
        _diagnose_recommendations(
            collector,
            report["recommendations"],
        )
    if "evidence_references" in report:
        _diagnose_evidence_references(
            collector,
            report["evidence_references"],
        )
    if "limitations" in report:
        _diagnose_limitations(
            collector,
            report["limitations"],
        )
    return collector.finish()


def _diagnose_reporting_period(
    collector: _SchemaDiagnosticCollector,
    value: Any,
) -> None:
    period = _diagnose_object(
        collector,
        value,
        "$.reporting_period",
        _PERIOD_FIELDS,
    )
    if period is None:
        return
    if "start_at" in period:
        _diagnose_string(
            collector,
            period["start_at"],
            "$.reporting_period.start_at",
        )
    if "end_at" in period:
        _diagnose_string(
            collector,
            period["end_at"],
            "$.reporting_period.end_at",
        )
    if "interval_semantics" in period:
        semantics = _diagnose_string(
            collector,
            period["interval_semantics"],
            "$.reporting_period.interval_semantics",
        )
        if semantics is not None and semantics != "[start_at,end_at]":
            collector.add(
                path="$.reporting_period.interval_semantics",
                code=SchemaDiagnosticCode.INVALID_ENUM,
                expected="[start_at,end_at]",
                actual_value=semantics,
                constraint="exact",
            )


def _diagnose_generation(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    *,
    expected_provider_ref: str | None,
) -> None:
    generation = _diagnose_object(
        collector,
        value,
        "$.generation",
        _GENERATION_FIELDS,
    )
    if generation is None:
        return
    if "mode" in generation:
        mode = _diagnose_string(
            collector,
            generation["mode"],
            "$.generation.mode",
        )
        if mode is not None and mode != GenerationMode.LLM.value:
            collector.add(
                path="$.generation.mode",
                code=SchemaDiagnosticCode.INVALID_ENUM,
                expected=GenerationMode.LLM.value,
                actual_value=mode,
                constraint="provider_candidate_only",
            )
    if "degraded" in generation:
        degraded = generation["degraded"]
        if not isinstance(degraded, bool):
            collector.add(
                path="$.generation.degraded",
                code=SchemaDiagnosticCode.INVALID_TYPE,
                expected="boolean",
                actual_value=degraded,
            )
        elif degraded is not False:
            collector.add(
                path="$.generation.degraded",
                code=SchemaDiagnosticCode.INVALID_VALUE,
                expected="false",
                actual_value=degraded,
                constraint="provider_candidate_only",
            )
    if "failure_code" in generation:
        failure_code = generation["failure_code"]
        if failure_code is not None:
            collector.add(
                path="$.generation.failure_code",
                code=SchemaDiagnosticCode.INVALID_VALUE,
                expected="null",
                actual_value=failure_code,
                constraint="provider_candidate_only",
            )
    if "provider_ref" in generation:
        provider_ref = generation["provider_ref"]
        if provider_ref is not None:
            provider_text = _diagnose_string(
                collector,
                provider_ref,
                "$.generation.provider_ref",
            )
            if (
                provider_text is not None
                and expected_provider_ref is not None
                and provider_text != expected_provider_ref
            ):
                collector.add(
                    path="$.generation.provider_ref",
                    code=SchemaDiagnosticCode.INVALID_VALUE,
                    expected="request provider_ref",
                    actual_value=provider_text,
                    constraint="provider_binding",
                )


def _diagnose_claims(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    path: str,
    *,
    expected_kind: ClaimKind,
) -> None:
    claims = _diagnose_array(collector, value, path)
    if claims is None:
        return
    seen_claim_ids: set[str] = set()
    for index, raw_claim in enumerate(claims):
        item_path = f"{path}[{index}]"
        claim = _diagnose_object(
            collector,
            raw_claim,
            item_path,
            _CLAIM_FIELDS,
        )
        if claim is None:
            continue
        if "kind" in claim:
            kind = _diagnose_string(
                collector,
                claim["kind"],
                f"{item_path}.kind",
            )
            if kind is not None and kind != expected_kind.value:
                collector.add(
                    path=f"{item_path}.kind",
                    code=SchemaDiagnosticCode.INVALID_ENUM,
                    expected=expected_kind.value,
                    actual_value=kind,
                    constraint="claim_role",
                )
        if "claim_id" in claim:
            claim_id = _diagnose_string(
                collector,
                claim["claim_id"],
                f"{item_path}.claim_id",
            )
            if claim_id is not None:
                if claim_id in seen_claim_ids:
                    collector.add(
                        path=f"{item_path}.claim_id",
                        code=SchemaDiagnosticCode.INVALID_COLLECTION,
                        expected="unique claim_id",
                        actual_value=claim_id,
                        constraint="unique",
                    )
                seen_claim_ids.add(claim_id)
        if "statement" in claim:
            _diagnose_string(
                collector,
                claim["statement"],
                f"{item_path}.statement",
            )
        for field_name in (
            "fact_refs",
            "metric_refs",
            "event_refs",
            "source_refs",
            "evidence_refs",
        ):
            if field_name in claim:
                _diagnose_string_list(
                    collector,
                    claim[field_name],
                    f"{item_path}.{field_name}",
                )
        if "track_refs" in claim:
            _diagnose_track_references(
                collector,
                claim["track_refs"],
                f"{item_path}.track_refs",
            )
        if "numeric_claims" in claim:
            _diagnose_numeric_claims(
                collector,
                claim["numeric_claims"],
                f"{item_path}.numeric_claims",
            )


def _diagnose_track_references(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    path: str,
) -> None:
    references = _diagnose_array(collector, value, path)
    if references is None:
        return
    seen_track_ids: set[int] = set()
    for index, raw_reference in enumerate(references):
        item_path = f"{path}[{index}]"
        reference = _diagnose_object(
            collector,
            raw_reference,
            item_path,
            _TRACK_FIELDS,
        )
        if reference is None:
            continue
        if "track_scope" in reference:
            scope = _diagnose_string(
                collector,
                reference["track_scope"],
                f"{item_path}.track_scope",
            )
            if scope is not None and scope != "tracker_scoped":
                collector.add(
                    path=f"{item_path}.track_scope",
                    code=SchemaDiagnosticCode.INVALID_ENUM,
                    expected="tracker_scoped",
                    actual_value=scope,
                    constraint="exact",
                )
        if "track_id" in reference:
            track_id = reference["track_id"]
            if isinstance(track_id, bool) or not isinstance(track_id, int):
                collector.add(
                    path=f"{item_path}.track_id",
                    code=SchemaDiagnosticCode.INVALID_TYPE,
                    expected="integer",
                    actual_value=track_id,
                )
            elif track_id < 0:
                collector.add(
                    path=f"{item_path}.track_id",
                    code=SchemaDiagnosticCode.INVALID_VALUE,
                    expected="non-negative integer",
                    actual_value=track_id,
                    constraint="minimum_0",
                )
            elif track_id in seen_track_ids:
                collector.add(
                    path=f"{item_path}.track_id",
                    code=SchemaDiagnosticCode.INVALID_COLLECTION,
                    expected="unique track_id",
                    actual_value=track_id,
                    constraint="unique",
                )
            if isinstance(track_id, int) and not isinstance(track_id, bool):
                seen_track_ids.add(track_id)


def _diagnose_numeric_claims(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    path: str,
) -> None:
    claims = _diagnose_array(collector, value, path)
    if claims is None:
        return
    seen_metric_refs: set[str] = set()
    for index, raw_claim in enumerate(claims):
        item_path = f"{path}[{index}]"
        claim = _diagnose_object(
            collector,
            raw_claim,
            item_path,
            _NUMERIC_FIELDS,
        )
        if claim is None:
            continue
        if "metric_ref" in claim:
            metric_ref = _diagnose_string(
                collector,
                claim["metric_ref"],
                f"{item_path}.metric_ref",
            )
            if metric_ref is not None:
                if metric_ref in seen_metric_refs:
                    collector.add(
                        path=f"{item_path}.metric_ref",
                        code=SchemaDiagnosticCode.INVALID_COLLECTION,
                        expected="unique metric_ref",
                        actual_value=metric_ref,
                        constraint="unique",
                    )
                seen_metric_refs.add(metric_ref)
        if "value" in claim:
            numeric_value = claim["value"]
            if isinstance(numeric_value, bool) or not isinstance(
                numeric_value,
                (int, float),
            ):
                collector.add(
                    path=f"{item_path}.value",
                    code=SchemaDiagnosticCode.INVALID_TYPE,
                    expected="number",
                    actual_value=numeric_value,
                )
            elif not math.isfinite(float(numeric_value)):
                collector.add(
                    path=f"{item_path}.value",
                    code=SchemaDiagnosticCode.INVALID_VALUE,
                    expected="finite number",
                    actual_value=numeric_value,
                    constraint="finite",
                )


def _diagnose_recommendations(
    collector: _SchemaDiagnosticCollector,
    value: Any,
) -> None:
    recommendations = _diagnose_array(
        collector,
        value,
        "$.recommendations",
    )
    if recommendations is None:
        return
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(recommendations):
        path = f"$.recommendations[{index}]"
        item = _diagnose_object(
            collector,
            raw_item,
            path,
            _RECOMMENDATION_FIELDS,
        )
        if item is None:
            continue
        if "recommendation_id" in item:
            recommendation_id = _diagnose_string(
                collector,
                item["recommendation_id"],
                f"{path}.recommendation_id",
            )
            if recommendation_id is not None:
                if recommendation_id in seen_ids:
                    collector.add(
                        path=f"{path}.recommendation_id",
                        code=SchemaDiagnosticCode.INVALID_COLLECTION,
                        expected="unique recommendation_id",
                        actual_value=recommendation_id,
                        constraint="unique",
                    )
                seen_ids.add(recommendation_id)
        for field_name in ("action", "priority"):
            if field_name in item:
                _diagnose_string(
                    collector,
                    item[field_name],
                    f"{path}.{field_name}",
                )
        for field_name in (
            "basis_finding_refs",
            "basis_fact_refs",
            "basis_metric_refs",
        ):
            if field_name in item:
                _diagnose_string_list(
                    collector,
                    item[field_name],
                    f"{path}.{field_name}",
                )


def _diagnose_evidence_references(
    collector: _SchemaDiagnosticCollector,
    value: Any,
) -> None:
    references = _diagnose_array(
        collector,
        value,
        "$.evidence_references",
    )
    if references is None:
        return
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(references):
        path = f"$.evidence_references[{index}]"
        item = _diagnose_object(
            collector,
            raw_item,
            path,
            _EVIDENCE_FIELDS,
        )
        if item is None:
            continue
        if "track_scope" in item:
            scope = _diagnose_string(
                collector,
                item["track_scope"],
                f"{path}.track_scope",
            )
            if scope is not None and scope != "tracker_scoped":
                collector.add(
                    path=f"{path}.track_scope",
                    code=SchemaDiagnosticCode.INVALID_ENUM,
                    expected="tracker_scoped",
                    actual_value=scope,
                    constraint="exact",
                )
        if "evidence_ref" in item:
            evidence_ref = _diagnose_string(
                collector,
                item["evidence_ref"],
                f"{path}.evidence_ref",
            )
            if evidence_ref is not None:
                if evidence_ref in seen_ids:
                    collector.add(
                        path=f"{path}.evidence_ref",
                        code=SchemaDiagnosticCode.INVALID_COLLECTION,
                        expected="unique evidence_ref",
                        actual_value=evidence_ref,
                        constraint="unique",
                    )
                seen_ids.add(evidence_ref)
        for field_name in ("event_id", "snapshot_ref", "occurred_at"):
            if field_name in item:
                _diagnose_string(
                    collector,
                    item[field_name],
                    f"{path}.{field_name}",
                )
        if "track_id" in item:
            track_id = item["track_id"]
            if isinstance(track_id, bool) or not isinstance(track_id, int):
                collector.add(
                    path=f"{path}.track_id",
                    code=SchemaDiagnosticCode.INVALID_TYPE,
                    expected="integer",
                    actual_value=track_id,
                )
            elif track_id < 0:
                collector.add(
                    path=f"{path}.track_id",
                    code=SchemaDiagnosticCode.INVALID_VALUE,
                    expected="non-negative integer",
                    actual_value=track_id,
                    constraint="minimum_0",
                )


def _diagnose_limitations(
    collector: _SchemaDiagnosticCollector,
    value: Any,
) -> None:
    limitations = _diagnose_array(
        collector,
        value,
        "$.limitations",
    )
    if limitations is None:
        return
    seen_fields: set[str] = set()
    for index, raw_item in enumerate(limitations):
        path = f"$.limitations[{index}]"
        item = _diagnose_object(
            collector,
            raw_item,
            path,
            _LIMITATION_FIELDS,
        )
        if item is None:
            continue
        for field_name in ("field", "reason_code", "statement"):
            if field_name in item:
                _diagnose_string(
                    collector,
                    item[field_name],
                    f"{path}.{field_name}",
                )
        if "field" in item:
            field = item["field"]
            if isinstance(field, str) and field.strip():
                normalized = field.strip()
                if normalized in seen_fields:
                    collector.add(
                        path=f"{path}.field",
                        code=SchemaDiagnosticCode.INVALID_COLLECTION,
                        expected="unique limitation field",
                        actual_value=normalized,
                        constraint="unique",
                    )
                seen_fields.add(normalized)


def _diagnose_object(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    path: str,
    expected_fields: frozenset[str],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        collector.add(
            path=path,
            code=SchemaDiagnosticCode.INVALID_TYPE,
            expected="object",
            actual_value=value,
        )
        return None
    actual_fields = set(value)
    missing = sorted(expected_fields - actual_fields)
    unknown = sorted(actual_fields - expected_fields)
    for field_name in missing:
        collector.add(
            path=f"{path}.{field_name}",
            code=SchemaDiagnosticCode.MISSING_FIELD,
            expected="required field",
            actual_value=None,
            constraint="required",
        )
    if unknown:
        collector.add(
            path=f"{path}.<unexpected>",
            code=SchemaDiagnosticCode.UNEXPECTED_FIELD,
            expected="no additional fields",
            actual_value=value,
            constraint=f"count={len(unknown)}",
        )
    return value


def _diagnose_array(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    path: str,
) -> list[Any] | None:
    if not isinstance(value, list):
        collector.add(
            path=path,
            code=SchemaDiagnosticCode.INVALID_TYPE,
            expected="array",
            actual_value=value,
        )
        return None
    return value


def _diagnose_string(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    path: str,
) -> str | None:
    if not isinstance(value, str):
        collector.add(
            path=path,
            code=SchemaDiagnosticCode.INVALID_TYPE,
            expected="string",
            actual_value=value,
        )
        return None
    if not value.strip():
        collector.add(
            path=path,
            code=SchemaDiagnosticCode.INVALID_VALUE,
            expected="non-empty string",
            actual_value=value,
            constraint="minimum_length_1",
        )
        return None
    return value.strip()


def _diagnose_string_list(
    collector: _SchemaDiagnosticCollector,
    value: Any,
    path: str,
) -> None:
    items = _diagnose_array(collector, value, path)
    if items is None:
        return
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        text = _diagnose_string(collector, item, item_path)
        if text is None:
            continue
        if text in seen:
            collector.add(
                path=item_path,
                code=SchemaDiagnosticCode.INVALID_COLLECTION,
                expected="unique reference",
                actual_value=text,
                constraint="unique",
            )
        seen.add(text)


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number" if math.isfinite(value) else "non_finite"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


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


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{path} must be a non-empty string")
    return value.strip()


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{path} must be a boolean")
    return value


def _int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{path} must be an integer")
    return value


def _finite_number(value: Any, path: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{path} must be numeric")
    if not math.isfinite(float(value)):
        raise ValueError(f"{path} must be finite")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{path} must be an array")
    return value


def _string_list(value: Any, path: str) -> tuple[str, ...]:
    values = tuple(
        _string(item, f"{path}[]")
        for item in _list(value, path)
    )
    if len(set(values)) != len(values):
        raise ValueError(f"{path} contains duplicate references")
    return values


def _claims(
    value: Any,
    path: str,
    *,
    expected_kind: ClaimKind,
) -> tuple[SafetyReportClaim, ...]:
    claims: list[SafetyReportClaim] = []
    seen_ids: set[str] = set()
    for index, raw_claim in enumerate(_list(value, path)):
        item_path = f"{path}[{index}]"
        claim = _object(raw_claim, item_path, _CLAIM_FIELDS)
        if claim["kind"] != expected_kind.value:
            raise ValueError(f"{item_path}.kind is invalid")
        claim_id = _string(claim["claim_id"], f"{item_path}.claim_id")
        if claim_id in seen_ids:
            raise ValueError(f"{path} contains duplicate claim_id values")
        seen_ids.add(claim_id)
        claims.append(
            SafetyReportClaim(
                claim_id=claim_id,
                kind=expected_kind,
                statement=_string(
                    claim["statement"],
                    f"{item_path}.statement",
                ),
                fact_refs=_string_list(
                    claim["fact_refs"],
                    f"{item_path}.fact_refs",
                ),
                metric_refs=_string_list(
                    claim["metric_refs"],
                    f"{item_path}.metric_refs",
                ),
                event_refs=_string_list(
                    claim["event_refs"],
                    f"{item_path}.event_refs",
                ),
                track_refs=_track_references(
                    claim["track_refs"],
                    f"{item_path}.track_refs",
                ),
                source_refs=_string_list(
                    claim["source_refs"],
                    f"{item_path}.source_refs",
                ),
                evidence_refs=_string_list(
                    claim["evidence_refs"],
                    f"{item_path}.evidence_refs",
                ),
                numeric_claims=_numeric_claims(
                    claim["numeric_claims"],
                    f"{item_path}.numeric_claims",
                ),
            )
        )
    return tuple(claims)


def _track_references(
    value: Any,
    path: str,
) -> tuple[TrackReference, ...]:
    references: list[TrackReference] = []
    seen_ids: set[int] = set()
    for index, raw_reference in enumerate(_list(value, path)):
        item_path = f"{path}[{index}]"
        reference = _object(raw_reference, item_path, _TRACK_FIELDS)
        if reference["track_scope"] != "tracker_scoped":
            raise ValueError(f"{item_path}.track_scope must be tracker_scoped")
        track_id = _int(reference["track_id"], f"{item_path}.track_id")
        if track_id in seen_ids:
            raise ValueError(f"{path} contains duplicate track_id values")
        seen_ids.add(track_id)
        references.append(
            TrackReference(
                track_id=track_id,
                track_scope="tracker_scoped",
            )
        )
    return tuple(references)


def _numeric_claims(
    value: Any,
    path: str,
) -> tuple[MetricNumericClaim, ...]:
    claims: list[MetricNumericClaim] = []
    seen_refs: set[str] = set()
    for index, raw_claim in enumerate(_list(value, path)):
        item_path = f"{path}[{index}]"
        claim = _object(raw_claim, item_path, _NUMERIC_FIELDS)
        metric_ref = _string(claim["metric_ref"], f"{item_path}.metric_ref")
        if metric_ref in seen_refs:
            raise ValueError(f"{path} contains duplicate metric_ref values")
        seen_refs.add(metric_ref)
        claims.append(
            MetricNumericClaim(
                metric_ref=metric_ref,
                value=_finite_number(
                    claim["value"],
                    f"{item_path}.value",
                ),
            )
        )
    return tuple(claims)


def _recommendations(value: Any) -> tuple[ReportRecommendation, ...]:
    recommendations: list[ReportRecommendation] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(_list(value, "recommendations")):
        path = f"recommendations[{index}]"
        item = _object(raw_item, path, _RECOMMENDATION_FIELDS)
        recommendation_id = _string(
            item["recommendation_id"],
            f"{path}.recommendation_id",
        )
        if recommendation_id in seen_ids:
            raise ValueError(
                "recommendations contains duplicate recommendation_id values"
            )
        seen_ids.add(recommendation_id)
        recommendations.append(
            ReportRecommendation(
                recommendation_id=recommendation_id,
                action=_string(item["action"], f"{path}.action"),
                priority=_string(item["priority"], f"{path}.priority"),
                basis_finding_refs=_string_list(
                    item["basis_finding_refs"],
                    f"{path}.basis_finding_refs",
                ),
                basis_fact_refs=_string_list(
                    item["basis_fact_refs"],
                    f"{path}.basis_fact_refs",
                ),
                basis_metric_refs=_string_list(
                    item["basis_metric_refs"],
                    f"{path}.basis_metric_refs",
                ),
            )
        )
    return tuple(recommendations)


def _evidence_references(value: Any) -> tuple[ReportEvidenceReference, ...]:
    references: list[ReportEvidenceReference] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(_list(value, "evidence_references")):
        path = f"evidence_references[{index}]"
        item = _object(raw_item, path, _EVIDENCE_FIELDS)
        if item["track_scope"] != "tracker_scoped":
            raise ValueError(f"{path}.track_scope must be tracker_scoped")
        evidence_ref = _string(
            item["evidence_ref"],
            f"{path}.evidence_ref",
        )
        if evidence_ref in seen_ids:
            raise ValueError(
                "evidence_references contains duplicate evidence_ref values"
            )
        seen_ids.add(evidence_ref)
        references.append(
            ReportEvidenceReference(
                evidence_ref=evidence_ref,
                event_id=_string(item["event_id"], f"{path}.event_id"),
                track_id=_int(item["track_id"], f"{path}.track_id"),
                snapshot_ref=_string(
                    item["snapshot_ref"],
                    f"{path}.snapshot_ref",
                ),
                occurred_at=_string(
                    item["occurred_at"],
                    f"{path}.occurred_at",
                ),
            )
        )
    return tuple(references)


def _limitations(value: Any) -> tuple[ReportLimitation, ...]:
    limitations: list[ReportLimitation] = []
    seen_fields: set[str] = set()
    for index, raw_item in enumerate(_list(value, "limitations")):
        path = f"limitations[{index}]"
        item = _object(raw_item, path, _LIMITATION_FIELDS)
        field = _string(item["field"], f"{path}.field")
        if field in seen_fields:
            raise ValueError("limitations contains duplicate field values")
        seen_fields.add(field)
        limitations.append(
            ReportLimitation(
                field=field,
                reason_code=_string(
                    item["reason_code"],
                    f"{path}.reason_code",
                ),
                statement=_string(
                    item["statement"],
                    f"{path}.statement",
                ),
            )
        )
    return tuple(limitations)
