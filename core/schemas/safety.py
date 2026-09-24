"""Phase 8 deterministic safety analytics and context contracts.

These schemas contain no provider, prompt, model or network dependency.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import (
    EventStatus,
    normalize_utc_timestamp,
)

__all__ = [
    "ANALYTICS_VERSION",
    "CONTEXT_SCHEMA_VERSION",
    "MetricValue",
    "ReportingPeriod",
    "SafetyAnalysisContext",
    "SafetyAnalyticsQuery",
    "SafetyAnalyticsResult",
    "SafetyContextMetadata",
    "SafetyEventFact",
    "TemporalBucket",
    "UnavailableField",
    "source_reference",
]

CONTEXT_SCHEMA_VERSION = "phase8-context-v1"
ANALYTICS_VERSION = "phase8-analytics-v1"

_SOURCE_REF_PATTERN = re.compile(r"^SRC-[0-9a-f]{16}$")
_DAY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TemporalBucket(str, Enum):
    """Frozen temporal bucket vocabulary for P8-1."""

    DAY = "day"


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_non_negative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return value


def _validate_confidence(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("confidence must be numeric")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError("confidence must be finite and between 0 and 1")
    return normalized


def _normalize_snapshot_ref(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("snapshot_ref must be a relative POSIX path or None")
    candidate = value.strip()
    path = PurePosixPath(candidate)
    if (
        path.is_absolute()
        or "\\" in candidate
        or re.match(r"^[A-Za-z]:/", candidate) is not None
    ):
        raise ValueError("snapshot_ref must be a relative POSIX path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(
            "snapshot_ref cannot contain empty, current or parent segments"
        )
    return path.as_posix()


def _normalize_day(value: str) -> str:
    if not isinstance(value, str) or _DAY_PATTERN.fullmatch(value) is None:
        raise ValueError("day buckets must use YYYY-MM-DD")
    return value


def source_reference(source: str) -> str:
    """Return a stable opaque reference for one authoritative source value."""

    normalized = _validate_text(source, "source")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"SRC-{digest}"


@dataclass(frozen=True, slots=True)
class ReportingPeriod:
    """A canonical UTC interval using inclusive start and end bounds."""

    start_at: str
    end_at: str

    def __post_init__(self) -> None:
        start_at = normalize_utc_timestamp(self.start_at)
        end_at = normalize_utc_timestamp(self.end_at)
        if start_at > end_at:
            raise ValueError("start_at cannot be after end_at")
        object.__setattr__(self, "start_at", start_at)
        object.__setattr__(self, "end_at", end_at)

    def to_dict(self) -> dict[str, str]:
        return {
            "start_at": self.start_at,
            "end_at": self.end_at,
            "interval_semantics": "[start_at,end_at]",
        }


@dataclass(frozen=True, slots=True)
class SafetyAnalyticsQuery:
    """Validated deterministic analytics query over persisted events."""

    start_at: str
    end_at: str
    track_id: int | None = None
    event_type: ComplianceEventType | str | None = None
    status: EventStatus | str | None = None
    source: str | None = None
    bucket: TemporalBucket | str = TemporalBucket.DAY

    def __post_init__(self) -> None:
        period = ReportingPeriod(self.start_at, self.end_at)
        object.__setattr__(self, "start_at", period.start_at)
        object.__setattr__(self, "end_at", period.end_at)

        if self.track_id is not None:
            object.__setattr__(
                self,
                "track_id",
                _validate_non_negative_int(self.track_id, "track_id"),
            )
        if self.event_type is not None:
            try:
                event_type = ComplianceEventType(self.event_type)
            except ValueError as exc:
                raise ValueError(
                    "event_type must be a supported compliance event type"
                ) from exc
            object.__setattr__(self, "event_type", event_type)
        if self.status is not None:
            try:
                status = EventStatus(self.status)
            except ValueError as exc:
                raise ValueError("status must be a supported event status") from exc
            object.__setattr__(self, "status", status)
        if self.source is not None:
            object.__setattr__(
                self,
                "source",
                _validate_text(self.source, "source"),
            )
        try:
            bucket = TemporalBucket(self.bucket)
        except ValueError as exc:
            raise ValueError("bucket must be a supported temporal bucket") from exc
        object.__setattr__(self, "bucket", bucket)

    @property
    def reporting_period(self) -> ReportingPeriod:
        return ReportingPeriod(self.start_at, self.end_at)


@dataclass(frozen=True, slots=True)
class SafetyEventFact:
    """One sanitized event fact used by the Phase 8 context."""

    fact_id: str
    event_id: str
    occurred_at: str
    event_type: ComplianceEventType
    confidence: float
    track_id: int
    source_ref: str | None
    status: EventStatus
    snapshot_ref: str | None
    evidence_available: bool

    def __post_init__(self) -> None:
        fact_id = _validate_text(self.fact_id, "fact_id")
        event_id = _validate_text(self.event_id, "event_id")
        if fact_id != f"EVT:{event_id}":
            raise ValueError("fact_id must use the EVT:<event_id> convention")
        object.__setattr__(self, "fact_id", fact_id)
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_timestamp(self.occurred_at),
        )
        try:
            event_type = ComplianceEventType(self.event_type)
        except ValueError as exc:
            raise ValueError("event_type must be a supported compliance event type") from exc
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(
            self,
            "confidence",
            _validate_confidence(self.confidence),
        )
        object.__setattr__(
            self,
            "track_id",
            _validate_non_negative_int(self.track_id, "track_id"),
        )
        source_ref = self.source_ref
        if source_ref is not None:
            source_ref = _validate_text(source_ref, "source_ref")
            if _SOURCE_REF_PATTERN.fullmatch(source_ref) is None:
                raise ValueError(
                    "source_ref must use the SRC-<16 hex> convention or be None"
                )
        object.__setattr__(self, "source_ref", source_ref)
        try:
            status = EventStatus(self.status)
        except ValueError as exc:
            raise ValueError("status must be a supported event status") from exc
        object.__setattr__(self, "status", status)
        snapshot_ref = _normalize_snapshot_ref(self.snapshot_ref)
        object.__setattr__(self, "snapshot_ref", snapshot_ref)
        if not isinstance(self.evidence_available, bool):
            raise TypeError("evidence_available must be a boolean")
        if self.evidence_available != (snapshot_ref is not None):
            raise ValueError(
                "evidence_available must match snapshot_ref presence"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "type": self.event_type.value,
            "confidence": self.confidence,
            "track_id": self.track_id,
            "track_scope": "tracker_scoped",
            "source_ref": self.source_ref,
            "status": self.status.value,
            "snapshot_ref": self.snapshot_ref,
            "evidence_available": self.evidence_available,
        }


@dataclass(frozen=True, slots=True)
class MetricValue:
    """One deterministic, named metric in the Phase 8 context."""

    metric_id: str
    name: str
    value: str | int | float | None
    unit: str
    definition: str
    sample_size: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metric_id",
            _validate_text(self.metric_id, "metric_id"),
        )
        object.__setattr__(self, "name", _validate_text(self.name, "name"))
        object.__setattr__(self, "unit", _validate_text(self.unit, "unit"))
        object.__setattr__(
            self,
            "definition",
            _validate_text(self.definition, "definition"),
        )
        object.__setattr__(
            self,
            "sample_size",
            _validate_non_negative_int(self.sample_size, "sample_size"),
        )
        if isinstance(self.value, bool) or not isinstance(
            self.value,
            (str, int, float, type(None)),
        ):
            raise TypeError("metric value must be a string, number or None")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("numeric metric values must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "definition": self.definition,
            "sample_size": self.sample_size,
        }


@dataclass(frozen=True, slots=True)
class UnavailableField:
    """One unsupported or unavailable Phase 8 field."""

    field: str
    reason_code: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "field", _validate_text(self.field, "field"))
        object.__setattr__(
            self,
            "reason_code",
            _validate_text(self.reason_code, "reason_code"),
        )
        object.__setattr__(self, "reason", _validate_text(self.reason, "reason"))

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field,
            "reason_code": self.reason_code,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class SafetyAnalyticsResult:
    """Deterministic aggregate result before context construction."""

    query: SafetyAnalyticsQuery
    facts: tuple[SafetyEventFact, ...]
    counts_by_type: tuple[tuple[ComplianceEventType, int], ...]
    counts_by_status: tuple[tuple[EventStatus, int], ...]
    counts_by_track: tuple[tuple[int, int], ...]
    counts_by_day: tuple[tuple[str, int], ...]
    counts_by_source_ref: tuple[tuple[str, int], ...]
    first_occurrence: str | None
    last_occurrence: str | None
    evidence_available_count: int
    evidence_missing_count: int
    unavailable_fields: tuple[UnavailableField, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.query, SafetyAnalyticsQuery):
            raise TypeError("query must be a SafetyAnalyticsQuery")

        facts = tuple(self.facts)
        event_ids: set[str] = set()
        for fact in facts:
            if not isinstance(fact, SafetyEventFact):
                raise TypeError("facts must contain SafetyEventFact objects")
            if fact.event_id in event_ids:
                raise ValueError("facts cannot contain duplicate event_id values")
            event_ids.add(fact.event_id)
        object.__setattr__(self, "facts", facts)

        object.__setattr__(
            self,
            "counts_by_type",
            _normalize_grouped_counts(
                self.counts_by_type,
                "counts_by_type",
                ComplianceEventType,
            ),
        )
        object.__setattr__(
            self,
            "counts_by_status",
            _normalize_grouped_counts(
                self.counts_by_status,
                "counts_by_status",
                EventStatus,
            ),
        )
        object.__setattr__(
            self,
            "counts_by_track",
            tuple(
                (
                    _validate_non_negative_int(track_id, "track_id"),
                    _validate_non_negative_int(count, "track count"),
                )
                for track_id, count in self.counts_by_track
            ),
        )
        object.__setattr__(
            self,
            "counts_by_day",
            tuple(
                (
                    _normalize_day(day),
                    _validate_non_negative_int(count, "day count"),
                )
                for day, count in self.counts_by_day
            ),
        )
        object.__setattr__(
            self,
            "counts_by_source_ref",
            tuple(
                (
                    _validate_text(source_ref, "source_ref"),
                    _validate_non_negative_int(count, "source count"),
                )
                for source_ref, count in self.counts_by_source_ref
            ),
        )
        if self.first_occurrence is not None:
            object.__setattr__(
                self,
                "first_occurrence",
                normalize_utc_timestamp(self.first_occurrence),
            )
        if self.last_occurrence is not None:
            object.__setattr__(
                self,
                "last_occurrence",
                normalize_utc_timestamp(self.last_occurrence),
            )
        object.__setattr__(
            self,
            "evidence_available_count",
            _validate_non_negative_int(
                self.evidence_available_count,
                "evidence_available_count",
            ),
        )
        object.__setattr__(
            self,
            "evidence_missing_count",
            _validate_non_negative_int(
                self.evidence_missing_count,
                "evidence_missing_count",
            ),
        )
        if (
            self.evidence_available_count + self.evidence_missing_count
            != len(facts)
        ):
            raise ValueError("evidence counts must sum to total fact count")
        unavailable_fields = tuple(self.unavailable_fields)
        if any(
            not isinstance(field, UnavailableField)
            for field in unavailable_fields
        ):
            raise TypeError(
                "unavailable_fields must contain UnavailableField objects"
            )
        object.__setattr__(self, "unavailable_fields", unavailable_fields)

    @property
    def total_count(self) -> int:
        return len(self.facts)


def _normalize_grouped_counts(
    values: tuple[tuple[Any, int], ...],
    field_name: str,
    key_type: type[Enum],
) -> tuple[tuple[Enum, int], ...]:
    normalized: list[tuple[Enum, int]] = []
    seen: set[Enum] = set()
    for key, count in values:
        try:
            normalized_key = key_type(key)
        except ValueError as exc:
            raise ValueError(f"{field_name} contains an unsupported key") from exc
        if normalized_key in seen:
            raise ValueError(f"{field_name} contains a duplicate key")
        seen.add(normalized_key)
        normalized.append(
            (
                normalized_key,
                _validate_non_negative_int(count, f"{field_name} count"),
            )
        )
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class SafetyContextMetadata:
    """Metadata for one phase8-context-v1 payload."""

    context_version: str
    analytics_version: str
    generated_at: str
    reporting_period: ReportingPeriod
    query_filters: tuple[tuple[str, str | int | bool | None], ...]
    event_schema_version: str
    source_of_truth: str
    detail_selection_policy: str
    provider_data_policy: str

    def __post_init__(self) -> None:
        if self.context_version != CONTEXT_SCHEMA_VERSION:
            raise ValueError("unsupported context_version")
        object.__setattr__(
            self,
            "analytics_version",
            _validate_text(self.analytics_version, "analytics_version"),
        )
        object.__setattr__(
            self,
            "generated_at",
            normalize_utc_timestamp(self.generated_at),
        )
        if not isinstance(self.reporting_period, ReportingPeriod):
            raise TypeError("reporting_period must be a ReportingPeriod")
        object.__setattr__(
            self,
            "query_filters",
            tuple(
                (
                    _validate_text(key, "query filter key"),
                    value,
                )
                for key, value in self.query_filters
            ),
        )
        object.__setattr__(
            self,
            "event_schema_version",
            _validate_text(
                self.event_schema_version,
                "event_schema_version",
            ),
        )
        object.__setattr__(
            self,
            "source_of_truth",
            _validate_text(self.source_of_truth, "source_of_truth"),
        )
        object.__setattr__(
            self,
            "detail_selection_policy",
            _validate_text(
                self.detail_selection_policy,
                "detail_selection_policy",
            ),
        )
        object.__setattr__(
            self,
            "provider_data_policy",
            _validate_text(
                self.provider_data_policy,
                "provider_data_policy",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CONTEXT_SCHEMA_VERSION,
            "context_version": self.context_version,
            "analytics_version": self.analytics_version,
            "generated_at": self.generated_at,
            "reporting_period": self.reporting_period.to_dict(),
            "query_filters": dict(self.query_filters),
            "event_schema_version": self.event_schema_version,
            "source_of_truth": self.source_of_truth,
            "detail_selection_policy": self.detail_selection_policy,
            "provider_data_policy": self.provider_data_policy,
        }


@dataclass(frozen=True, slots=True)
class SafetyAnalysisContext:
    """Immutable phase8-context-v1 payload with four separate sections."""

    metadata: SafetyContextMetadata
    observed_facts: tuple[SafetyEventFact, ...]
    calculated_metrics: tuple[MetricValue, ...]
    unavailable_fields: tuple[UnavailableField, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, SafetyContextMetadata):
            raise TypeError("metadata must be a SafetyContextMetadata")
        observed_facts = tuple(self.observed_facts)
        calculated_metrics = tuple(self.calculated_metrics)
        unavailable_fields = tuple(self.unavailable_fields)
        if any(not isinstance(item, SafetyEventFact) for item in observed_facts):
            raise TypeError("observed_facts contain an unsupported value")
        if any(not isinstance(item, MetricValue) for item in calculated_metrics):
            raise TypeError("calculated_metrics contain an unsupported value")
        if any(
            not isinstance(item, UnavailableField)
            for item in unavailable_fields
        ):
            raise TypeError("unavailable_fields contain an unsupported value")
        if len({item.fact_id for item in observed_facts}) != len(observed_facts):
            raise ValueError("observed_facts contain duplicate fact_id values")
        if (
            len({item.metric_id for item in calculated_metrics})
            != len(calculated_metrics)
        ):
            raise ValueError(
                "calculated_metrics contain duplicate metric_id values"
            )
        if (
            len({item.field for item in unavailable_fields})
            != len(unavailable_fields)
        ):
            raise ValueError("unavailable_fields contain duplicate field values")
        object.__setattr__(self, "observed_facts", observed_facts)
        object.__setattr__(self, "calculated_metrics", calculated_metrics)
        object.__setattr__(self, "unavailable_fields", unavailable_fields)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_facts": [item.to_dict() for item in self.observed_facts],
            "calculated_metrics": [
                item.to_dict() for item in self.calculated_metrics
            ],
            "metadata": self.metadata.to_dict(),
            "unavailable_fields": [
                item.to_dict() for item in self.unavailable_fields
            ],
        }

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
