"""Deterministic read-only analytics over persisted compliance events."""

from __future__ import annotations

from collections import Counter

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import (
    EventPage,
    EventQuery,
    EventStatistics,
    EventStatus,
    PersistedEvent,
)
from core.schemas.safety import (
    SafetyAnalyticsQuery,
    SafetyAnalyticsResult,
    SafetyEventFact,
    UnavailableField,
    source_reference,
)
from services.event_query_service import EventQueryService

__all__ = [
    "SafetyAnalyticsError",
    "SafetyAnalyticsService",
]

_PAGE_SIZE = 1000
_EVENT_TYPE_ORDER = (
    ComplianceEventType.NO_HELMET,
    ComplianceEventType.NO_VEST,
    ComplianceEventType.PPE_UNKNOWN,
)
_STATUS_ORDER = (
    EventStatus.OPEN,
    EventStatus.ACKNOWLEDGED,
    EventStatus.RESOLVED,
    EventStatus.DISMISSED,
)
_UNAVAILABLE_FIELDS = (
    UnavailableField(
        field="metrics.per_event_source_attribution",
        reason_code="SOURCE_NOT_IN_EVENT_PROJECTION",
        reason=(
            "PersistedEvent does not expose source, so source counts are "
            "available only through EventQueryService statistics and are "
            "serialized as opaque source references. Per-event source "
            "attribution is not inferred."
        ),
    ),
    UnavailableField(
        field="metrics.violation_duration",
        reason_code="NO_PERSISTED_DURATION_FIELD",
        reason=(
            "Persisted events contain one occurrence timestamp and no "
            "authoritative start, end or duration field."
        ),
    ),
    UnavailableField(
        field="metrics.unique_person_count",
        reason_code="TRACK_ID_NOT_STABLE_IDENTITY",
        reason=(
            "track_id is tracker-scoped and does not represent a stable "
            "person identity across sessions."
        ),
    ),
    UnavailableField(
        field="metrics.cross_session_identity",
        reason_code="NO_AUTHORITATIVE_IDENTITY_SOURCE",
        reason="The event store has no authoritative cross-session identity.",
    ),
    UnavailableField(
        field="metrics.alert_delivery",
        reason_code="NO_ALERT_TELEMETRY_TABLE",
        reason=(
            "The persisted schema stores no alert delivery, acknowledgement "
            "or latency telemetry."
        ),
    ),
)


class SafetyAnalyticsError(RuntimeError):
    """Deterministic analytics failure with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        self.code = code
        super().__init__(message)


def _fact_from_event(
    event: PersistedEvent,
    *,
    source_ref: str | None,
) -> SafetyEventFact:
    return SafetyEventFact(
        fact_id=f"EVT:{event.id}",
        event_id=event.id,
        occurred_at=event.timestamp,
        event_type=event.type,
        confidence=event.confidence,
        track_id=event.track_id,
        source_ref=source_ref,
        status=event.status,
        snapshot_ref=event.snapshot,
        evidence_available=event.snapshot is not None,
    )


class SafetyAnalyticsService:
    """Calculate only deterministic metrics supported by persisted events."""

    def __init__(self, event_query_service: EventQueryService) -> None:
        if not isinstance(event_query_service, EventQueryService):
            raise TypeError(
                "event_query_service must be an EventQueryService"
            )
        self.event_query_service = event_query_service

    def analyze(self, query: SafetyAnalyticsQuery) -> SafetyAnalyticsResult:
        if not isinstance(query, SafetyAnalyticsQuery):
            raise TypeError("query must be a SafetyAnalyticsQuery")

        events = self._load_events(query)
        events = tuple(sorted(events, key=lambda item: item.id))
        events = tuple(
            sorted(events, key=lambda item: item.timestamp, reverse=True)
        )
        source_ref = (
            None
            if query.source is None
            else source_reference(query.source)
        )
        facts = tuple(
            _fact_from_event(event, source_ref=source_ref)
            for event in events
        )
        counts_by_source_ref = self._load_source_counts(
            query,
            expected_total=len(events),
        )

        type_counter = Counter(fact.event_type for fact in facts)
        status_counter = Counter(fact.status for fact in facts)
        track_counter = Counter(fact.track_id for fact in facts)
        day_counter = Counter(fact.occurred_at[:10] for fact in facts)
        occurrences = [fact.occurred_at for fact in facts]

        return SafetyAnalyticsResult(
            query=query,
            facts=facts,
            counts_by_type=tuple(
                (event_type, type_counter[event_type])
                for event_type in _EVENT_TYPE_ORDER
            ),
            counts_by_status=tuple(
                (status, status_counter[status])
                for status in _STATUS_ORDER
            ),
            counts_by_track=tuple(sorted(track_counter.items())),
            counts_by_day=tuple(sorted(day_counter.items())),
            counts_by_source_ref=counts_by_source_ref,
            first_occurrence=min(occurrences) if occurrences else None,
            last_occurrence=max(occurrences) if occurrences else None,
            evidence_available_count=sum(
                1 for fact in facts if fact.evidence_available
            ),
            evidence_missing_count=sum(
                1 for fact in facts if not fact.evidence_available
            ),
            unavailable_fields=_UNAVAILABLE_FIELDS,
        )

    def _load_source_counts(
        self,
        query: SafetyAnalyticsQuery,
        *,
        expected_total: int,
    ) -> tuple[tuple[str, int], ...]:
        statistics = self.event_query_service.statistics(
            EventQuery(
                start_at=query.start_at,
                end_at=query.end_at,
                track_id=query.track_id,
                event_type=query.event_type,
                status=query.status,
                source=query.source,
                limit=_PAGE_SIZE,
            )
        )
        if not isinstance(statistics, EventStatistics):
            raise SafetyAnalyticsError(
                "UNSUPPORTED_QUERY_RESULT",
                "event statistics did not return an EventStatistics",
            )
        if statistics.total_count != expected_total:
            raise SafetyAnalyticsError(
                "PARTIAL_DATABASE_DATA",
                "event statistics did not match the detailed event total",
            )

        counts: list[tuple[str, int]] = []
        seen_refs: set[str] = set()
        for source, count in statistics.by_source:
            reference = source_reference(source)
            if reference in seen_refs:
                raise SafetyAnalyticsError(
                    "SOURCE_REFERENCE_COLLISION",
                    "two authoritative sources produced the same source reference",
                )
            seen_refs.add(reference)
            counts.append((reference, count))
        if sum(count for _, count in counts) != expected_total:
            raise SafetyAnalyticsError(
                "PARTIAL_DATABASE_DATA",
                "source counts did not sum to the detailed event total",
            )
        return tuple(sorted(counts))

    def _load_events(
        self,
        query: SafetyAnalyticsQuery,
    ) -> tuple[PersistedEvent, ...]:
        events: list[PersistedEvent] = []
        event_ids: set[str] = set()
        offset = 0
        expected_total: int | None = None

        while True:
            page = self.event_query_service.query_events(
                EventQuery(
                    start_at=query.start_at,
                    end_at=query.end_at,
                    track_id=query.track_id,
                    event_type=query.event_type,
                    status=query.status,
                    source=query.source,
                    limit=_PAGE_SIZE,
                    offset=offset,
                )
            )
            self._validate_page(page)
            if expected_total is None:
                expected_total = page.total_count
            elif page.total_count != expected_total:
                raise SafetyAnalyticsError(
                    "PARTIAL_DATABASE_DATA",
                    "event total changed while deterministic pages were read",
                )

            if not page.items and offset < page.total_count:
                raise SafetyAnalyticsError(
                    "PARTIAL_DATABASE_DATA",
                    "event query returned an incomplete page",
                )

            for item in page.items:
                if not isinstance(item, PersistedEvent):
                    raise SafetyAnalyticsError(
                        "UNSUPPORTED_EVENT_RECORD",
                        "event query returned an unsupported record",
                    )
                if item.id in event_ids:
                    raise SafetyAnalyticsError(
                        "DUPLICATE_EVENT_ID",
                        f"event query returned duplicate event_id: {item.id}",
                    )
                event_ids.add(item.id)
                events.append(item)

            offset += len(page.items)
            if expected_total == 0 or offset >= expected_total:
                break
            if not page.items:
                break

        if expected_total is not None and len(events) != expected_total:
            raise SafetyAnalyticsError(
                "PARTIAL_DATABASE_DATA",
                "event query did not return the declared total",
            )
        if len(event_ids) != len(events):
            raise SafetyAnalyticsError(
                "DUPLICATE_EVENT_ID",
                "event query returned non-unique event identities",
            )
        return tuple(events)

    @staticmethod
    def _validate_page(page: EventPage) -> None:
        if not isinstance(page, EventPage):
            raise SafetyAnalyticsError(
                "UNSUPPORTED_QUERY_RESULT",
                "event query did not return an EventPage",
            )
        if page.limit != _PAGE_SIZE:
            raise SafetyAnalyticsError(
                "UNSUPPORTED_QUERY_RESULT",
                "event query returned an unexpected page size",
            )
