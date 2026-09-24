"""Build reproducible phase8-context-v1 payloads from analytics results."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Callable

from core.schemas.events import (
    PERSISTED_EVENT_SCHEMA_VERSION,
    format_utc_timestamp,
)
from core.schemas.safety import (
    ANALYTICS_VERSION,
    CONTEXT_SCHEMA_VERSION,
    MetricValue,
    SafetyAnalysisContext,
    SafetyAnalyticsResult,
    SafetyContextMetadata,
    source_reference,
)

__all__ = ["SafetyContextBuilder"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SafetyContextBuilder:
    """Convert deterministic analytics into a canonical Phase 8 context."""

    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        if not callable(clock):
            raise TypeError("clock must be callable")
        self.clock = clock

    def build(
        self,
        analytics: SafetyAnalyticsResult,
    ) -> SafetyAnalysisContext:
        if not isinstance(analytics, SafetyAnalyticsResult):
            raise TypeError("analytics must be a SafetyAnalyticsResult")

        generated_at = format_utc_timestamp(self.clock())
        metadata = SafetyContextMetadata(
            context_version=CONTEXT_SCHEMA_VERSION,
            analytics_version=ANALYTICS_VERSION,
            generated_at=generated_at,
            reporting_period=analytics.query.reporting_period,
            query_filters=self._query_filters(analytics),
            event_schema_version=PERSISTED_EVENT_SCHEMA_VERSION,
            source_of_truth=(
                "SQLite events and snapshot metadata through EventQueryService"
            ),
            detail_selection_policy=(
                "all_matching_events_no_silent_truncation"
            ),
            provider_data_policy=(
                "structured_event_metadata_only;raw_evidence_bytes_excluded"
            ),
        )
        facts = sorted(analytics.facts, key=lambda item: item.event_id)
        facts = sorted(
            facts,
            key=lambda item: item.occurred_at,
            reverse=True,
        )
        metrics = tuple(
            sorted(
                self._metric_values(analytics),
                key=lambda item: item.metric_id,
            )
        )
        unavailable_fields = tuple(
            sorted(
                analytics.unavailable_fields,
                key=lambda item: item.field,
            )
        )
        return SafetyAnalysisContext(
            metadata=metadata,
            observed_facts=tuple(facts),
            calculated_metrics=metrics,
            unavailable_fields=unavailable_fields,
        )

    @staticmethod
    def fingerprint(context: SafetyAnalysisContext) -> str:
        """Return a SHA256 over deterministic context content.

        ``metadata.generated_at`` is excluded because it records construction
        time rather than event content. The frozen context schema itself is
        not changed and no ``context_sha256`` field is added.
        """

        if not isinstance(context, SafetyAnalysisContext):
            raise TypeError("context must be a SafetyAnalysisContext")
        payload = json.loads(context.to_canonical_json())
        payload["metadata"].pop("generated_at", None)
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _query_filters(
        analytics: SafetyAnalyticsResult,
    ) -> tuple[tuple[str, str | int | bool | None], ...]:
        query = analytics.query
        values: list[tuple[str, str | int | bool | None]] = [
            ("start_at", query.start_at),
            ("end_at", query.end_at),
            ("bucket", query.bucket.value),
        ]
        if query.track_id is not None:
            values.append(("track_id", query.track_id))
        if query.event_type is not None:
            values.append(("event_type", query.event_type.value))
        if query.status is not None:
            values.append(("status", query.status.value))
        if query.source is not None:
            values.append(
                ("source_filter_ref", source_reference(query.source))
            )
        return tuple(sorted(values, key=lambda item: item[0]))

    @staticmethod
    def _metric_values(
        analytics: SafetyAnalyticsResult,
    ) -> tuple[MetricValue, ...]:
        total = analytics.total_count
        metrics: list[MetricValue] = [
            MetricValue(
                metric_id="analytics.event_total_count",
                name="Total event count",
                value=total,
                unit="events",
                definition="Count of persisted events in the reporting period.",
                sample_size=total,
            ),
            MetricValue(
                metric_id="analytics.evidence.available_count",
                name="Evidence available count",
                value=analytics.evidence_available_count,
                unit="events",
                definition="Events with a persisted relative snapshot reference.",
                sample_size=total,
            ),
            MetricValue(
                metric_id="analytics.evidence.missing_count",
                name="Evidence missing count",
                value=analytics.evidence_missing_count,
                unit="events",
                definition="Events without a persisted relative snapshot reference.",
                sample_size=total,
            ),
            MetricValue(
                metric_id="analytics.first_occurrence",
                name="First occurrence",
                value=analytics.first_occurrence,
                unit="utc_timestamp",
                definition=(
                    "Earliest persisted event timestamp; null for an empty set."
                ),
                sample_size=total,
            ),
            MetricValue(
                metric_id="analytics.last_occurrence",
                name="Last occurrence",
                value=analytics.last_occurrence,
                unit="utc_timestamp",
                definition=(
                    "Latest persisted event timestamp; null for an empty set."
                ),
                sample_size=total,
            ),
        ]
        metrics.extend(
            MetricValue(
                metric_id=(
                    f"analytics.event_count.by_type.{event_type.value}"
                ),
                name=f"Event count for {event_type.value}",
                value=count,
                unit="events",
                definition=(
                    f"Count of events with type {event_type.value} in the "
                    "reporting period."
                ),
                sample_size=total,
            )
            for event_type, count in analytics.counts_by_type
        )
        metrics.extend(
            MetricValue(
                metric_id=f"analytics.event_count.by_status.{status.value}",
                name=f"Event count for status {status.value}",
                value=count,
                unit="events",
                definition=(
                    f"Count of events with status {status.value} in the "
                    "reporting period."
                ),
                sample_size=total,
            )
            for status, count in analytics.counts_by_status
        )
        metrics.extend(
            MetricValue(
                metric_id=f"analytics.event_count.by_track.{track_id}",
                name=f"Tracker-scoped event count for track_id {track_id}",
                value=count,
                unit="events",
                definition=(
                    "Count grouped by tracker-scoped track_id; this is not "
                    "a stable person identity count."
                ),
                sample_size=total,
            )
            for track_id, count in analytics.counts_by_track
        )
        metrics.extend(
            MetricValue(
                metric_id=f"analytics.event_count.by_day.{day}",
                name=f"Event count for UTC day {day}",
                value=count,
                unit="events",
                definition=(
                    "Count grouped by the UTC date prefix of occurred_at."
                ),
                sample_size=total,
            )
            for day, count in analytics.counts_by_day
        )
        metrics.extend(
            MetricValue(
                metric_id=f"analytics.event_count.by_source_ref.{source_ref}",
                name=f"Event count for source reference {source_ref}",
                value=count,
                unit="events",
                definition="Count grouped by an opaque source reference.",
                sample_size=total,
            )
            for source_ref, count in analytics.counts_by_source_ref
        )
        return tuple(metrics)
