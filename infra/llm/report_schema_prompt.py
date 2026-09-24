"""Machine-derived prompt projection of the frozen Phase 8 report schema.

This module does not define validation behavior. It introspects the
authoritative report dataclasses and enums and emits a compact JSON Schema-like
description for inclusion in the provider prompt. The strict parser remains
the authoritative runtime boundary.
"""

from __future__ import annotations

import json
from dataclasses import fields
from typing import Any, Iterable

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

__all__ = [
    "REPORT_SCHEMA_DESCRIPTION",
    "REPORT_SCHEMA_DESCRIPTION_JSON",
]

_IDENTIFIER_PATTERN = r"^[A-Za-z][A-Za-z0-9._:-]{0,159}$"
_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_EVIDENCE_REF_PATTERN = r"^EVID:.+$"

_IDENTIFIER = {
    "type": "string",
    "pattern": _IDENTIFIER_PATTERN,
}
_NON_EMPTY_STRING = {
    "type": "string",
    "minLength": 1,
}
_IDENTIFIER_ARRAY = {
    "type": "array",
    "items": _IDENTIFIER,
}


def _required_fields(model: type[Any]) -> tuple[str, ...]:
    return tuple(sorted(field.name for field in fields(model)))


def _object_schema(
    model: type[Any],
    properties: dict[str, Any],
    *,
    extra_required: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": sorted(set(_required_fields(model)) | set(extra_required)),
        "properties": properties,
    }


def _nullable_identifier() -> dict[str, Any]:
    return {
        "anyOf": [
            _IDENTIFIER,
            {"type": "null"},
        ]
    }


def _claim_schema(kind: ClaimKind) -> dict[str, Any]:
    return _object_schema(
        SafetyReportClaim,
        {
            "claim_id": _IDENTIFIER,
            "kind": {"const": kind.value},
            "statement": _NON_EMPTY_STRING,
            "fact_refs": _IDENTIFIER_ARRAY,
            "metric_refs": _IDENTIFIER_ARRAY,
            "event_refs": _IDENTIFIER_ARRAY,
            "track_refs": {
                "type": "array",
                "items": {"$ref": "#/$defs/trackReference"},
            },
            "source_refs": _IDENTIFIER_ARRAY,
            "evidence_refs": _IDENTIFIER_ARRAY,
            "numeric_claims": {
                "type": "array",
                "items": {"$ref": "#/$defs/numericClaim"},
            },
        },
    )


def _build_report_schema_description() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": REPORT_SCHEMA_VERSION,
        **_object_schema(
            StructuredSafetyReport,
            {
                "schema_version": {"const": REPORT_SCHEMA_VERSION},
                "source_context_sha256": {
                    "type": "string",
                    "pattern": _SHA256_PATTERN,
                },
                "reporting_period": _object_schema(
                    ReportingPeriod,
                    {
                        "start_at": _NON_EMPTY_STRING,
                        "end_at": _NON_EMPTY_STRING,
                        "interval_semantics": {"const": "[start_at,end_at]"},
                    },
                    extra_required=("interval_semantics",),
                ),
                "generation": _object_schema(
                    ReportGeneration,
                    {
                        "mode": {
                            "type": "string",
                            "enum": [
                                item.value for item in GenerationMode
                            ],
                        },
                        "degraded": {"type": "boolean"},
                        "provider_ref": _nullable_identifier(),
                        "failure_code": _nullable_identifier(),
                    },
                ),
                "executive_summary": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/observationClaim"},
                },
                "key_findings": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/observationClaim"},
                },
                "risk_observations": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/riskClaim"},
                },
                "recommendations": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/recommendation"},
                },
                "evidence_references": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/evidenceReference"},
                },
                "limitations": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/limitation"},
                },
                "grounding_status": {
                    "type": "string",
                    "enum": [
                        item.value for item in GroundingStatus
                    ],
                },
            },
        ),
        "$defs": {
            "observationClaim": _claim_schema(ClaimKind.OBSERVATION),
            "riskClaim": _claim_schema(ClaimKind.RISK),
            "trackReference": _object_schema(
                TrackReference,
                {
                    "track_id": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "track_scope": {"const": "tracker_scoped"},
                },
            ),
            "numericClaim": _object_schema(
                MetricNumericClaim,
                {
                    "metric_ref": _IDENTIFIER,
                    "value": {"type": "number"},
                },
            ),
            "recommendation": _object_schema(
                ReportRecommendation,
                {
                    "recommendation_id": _IDENTIFIER,
                    "action": _NON_EMPTY_STRING,
                    "priority": _IDENTIFIER,
                    "basis_finding_refs": _IDENTIFIER_ARRAY,
                    "basis_fact_refs": _IDENTIFIER_ARRAY,
                    "basis_metric_refs": _IDENTIFIER_ARRAY,
                },
            ),
            "evidenceReference": _object_schema(
                ReportEvidenceReference,
                {
                    "evidence_ref": {
                        "type": "string",
                        "pattern": _EVIDENCE_REF_PATTERN,
                    },
                    "event_id": _IDENTIFIER,
                    "track_id": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "track_scope": {"const": "tracker_scoped"},
                    "snapshot_ref": _NON_EMPTY_STRING,
                    "occurred_at": {
                        "type": "string",
                        "format": "date-time",
                    },
                },
                extra_required=("track_scope",),
            ),
            "limitation": _object_schema(
                ReportLimitation,
                {
                    "field": _IDENTIFIER,
                    "reason_code": _IDENTIFIER,
                    "statement": _NON_EMPTY_STRING,
                },
            ),
        },
        "x-phase8-rules": {
            "requiredFieldPolicy": (
                "Every field in required must be present at every object, "
                "even when its value is null or an empty array."
            ),
            "additionalFields": "forbidden at every object",
            "emptyArraysAllowed": [
                "executive_summary",
                "key_findings",
                "risk_observations",
                "recommendations",
                "evidence_references",
                "limitations",
                "fact_refs",
                "metric_refs",
                "event_refs",
                "track_refs",
                "source_refs",
                "evidence_refs",
                "numeric_claims",
                "basis_finding_refs",
                "basis_fact_refs",
                "basis_metric_refs",
            ],
            "nullableButRequired": [
                "$.generation.provider_ref",
                "$.generation.failure_code",
            ],
            "providerCandidateRequirements": {
                "$.schema_version": REPORT_SCHEMA_VERSION,
                "$.generation.mode": GenerationMode.LLM.value,
                "$.generation.degraded": False,
                "$.generation.failure_code": None,
                "$.grounding_status": GroundingStatus.UNVALIDATED.value,
            },
            "providerRefPolicy": (
                "null or one non-secret provider label; never include a "
                "credential, request header or secret."
            ),
            "referencePolicy": (
                "Use only references present in the supplied "
                "phase8-context-v1 payload."
            ),
        },
    }


REPORT_SCHEMA_DESCRIPTION = _build_report_schema_description()
REPORT_SCHEMA_DESCRIPTION_JSON = json.dumps(
    REPORT_SCHEMA_DESCRIPTION,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
)
