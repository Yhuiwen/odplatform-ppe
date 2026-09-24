"""Service adapters for the four frozen P8-6 read-only Agent tools."""

from __future__ import annotations

from typing import Any, Mapping

from core.agent.tool_registry import (
    STATIC_TOOL_DESCRIPTORS,
    ToolExecutionError,
    ToolRegistry,
)
from core.schemas.agent import (
    AgentCapability,
    AgentTool,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
)
from core.schemas.events import EventQuery
from core.schemas.safety import (
    SafetyAnalyticsQuery,
    source_reference,
)
from services.event_query_service import EventQueryService
from services.report_service import ReportService
from services.safety_analytics_service import SafetyAnalyticsService
from services.safety_context_builder import SafetyContextBuilder

__all__ = ["AgentToolService"]


class AgentToolService:
    """Wire static tool definitions to existing read-only Phase 8 services."""

    def __init__(
        self,
        *,
        event_query_service: EventQueryService,
        safety_analytics_service: SafetyAnalyticsService,
        context_builder: SafetyContextBuilder,
        report_service: ReportService,
        provider_client: Any | None = None,
    ) -> None:
        if not isinstance(event_query_service, EventQueryService):
            raise TypeError(
                "event_query_service must be an EventQueryService"
            )
        if not isinstance(safety_analytics_service, SafetyAnalyticsService):
            raise TypeError(
                "safety_analytics_service must be a SafetyAnalyticsService"
            )
        if not isinstance(context_builder, SafetyContextBuilder):
            raise TypeError("context_builder must be a SafetyContextBuilder")
        if not isinstance(report_service, ReportService):
            raise TypeError("report_service must be a ReportService")

        self.event_query_service = event_query_service
        self.safety_analytics_service = safety_analytics_service
        self.context_builder = context_builder
        self.report_service = report_service
        self.provider_client = provider_client
        self.registry = ToolRegistry(
            tools=(
                AgentTool(STATIC_TOOL_DESCRIPTORS[0], self._summary),
                AgentTool(STATIC_TOOL_DESCRIPTORS[1], self._statistics),
                AgentTool(STATIC_TOOL_DESCRIPTORS[2], self._event_details),
                AgentTool(STATIC_TOOL_DESCRIPTORS[3], self._report),
            )
        )

    def _summary(
        self,
        arguments: Mapping[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        analytics = self.safety_analytics_service.analyze(
            self._analytics_query(arguments)
        )
        analysis_context = self.context_builder.build(analytics)
        source_refs = tuple(
            sorted(
                {
                    fact.source_ref
                    for fact in analytics.facts
                    if fact.source_ref is not None
                }
            )
        )
        return ToolResult(
            tool_name="get_safety_summary",
            tool_version="1.0.0",
            status=ToolExecutionStatus.SUCCESS,
            data=analysis_context.to_dict(),
            source_refs=source_refs,
            row_count=analytics.total_count,
        )

    def _statistics(
        self,
        arguments: Mapping[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        self._required_text(arguments, "start_at")
        self._required_text(arguments, "end_at")
        query = self._event_query(arguments, default_limit=1000)
        statistics = self.event_query_service.statistics(query)
        payload = statistics.to_dict()
        raw_sources = payload.pop("by_source")
        source_counts = {
            source_reference(source): count
            for source, count in raw_sources.items()
        }
        payload["by_source_ref"] = dict(sorted(source_counts.items()))
        return ToolResult(
            tool_name="get_event_statistics",
            tool_version="1.0.0",
            status=ToolExecutionStatus.SUCCESS,
            data=payload,
            source_refs=tuple(sorted(source_counts)),
            row_count=statistics.total_count,
        )

    def _event_details(
        self,
        arguments: Mapping[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        event_id = self._optional_text(arguments, "event_id")
        if event_id is not None:
            event = self.event_query_service.get_event(event_id)
            events = () if event is None else (event,)
            total_count = len(events)
        else:
            query = self._event_query(arguments, default_limit=20)
            page = self.event_query_service.query_events(query)
            events = page.items
            total_count = page.total_count

        projected = tuple(self._event_projection(event) for event in events)
        source_refs = tuple(
            item["snapshot_ref"]
            for item in projected
            if item["snapshot_ref"] is not None
        )
        return ToolResult(
            tool_name="get_event_details",
            tool_version="1.0.0",
            status=ToolExecutionStatus.SUCCESS,
            data={
                "events": list(projected),
                "total_count": total_count,
            },
            source_refs=source_refs,
            row_count=len(projected),
        )

    def _report(
        self,
        arguments: Mapping[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        analytics = self.safety_analytics_service.analyze(
            self._analytics_query(arguments)
        )
        analysis_context = self.context_builder.build(analytics)
        if (
            self.provider_client is not None
            and AgentCapability.PROVIDER_INVOKE in context.capabilities
        ):
            report_result = self.report_service.generate_provider_or_fallback(
                analysis_context,
                self.provider_client,
            )
            payload = report_result.to_dict()
        else:
            report = self.report_service.generate(analysis_context)
            payload = {
                "status": "TEMPLATE_FALLBACK",
                "generation_path": "TEMPLATE_FALLBACK",
                "degraded": True,
                "report": report.to_dict(),
                "provider_metadata": None,
                "safe_error": None,
                "grounding_status": "valid",
            }
        return ToolResult(
            tool_name="generate_safety_report",
            tool_version="1.0.0",
            status=ToolExecutionStatus.SUCCESS,
            data=payload,
            row_count=analytics.total_count,
        )

    @staticmethod
    def _event_projection(event: Any) -> dict[str, Any]:
        return {
            "id": event.id,
            "timestamp": event.timestamp,
            "track_id": event.track_id,
            "type": event.type.value,
            "confidence": event.confidence,
            "snapshot_ref": event.snapshot,
            "status": event.status.value,
        }

    @staticmethod
    def _analytics_query(arguments: Mapping[str, Any]) -> SafetyAnalyticsQuery:
        start_at = AgentToolService._required_text(arguments, "start_at")
        end_at = AgentToolService._required_text(arguments, "end_at")
        try:
            return SafetyAnalyticsQuery(
                start_at=start_at,
                end_at=end_at,
                event_type=AgentToolService._optional_text(
                    arguments,
                    "event_type",
                ),
                status=AgentToolService._optional_text(
                    arguments,
                    "status",
                ),
                track_id=AgentToolService._optional_int(
                    arguments,
                    "track_id",
                ),
            )
        except (TypeError, ValueError) as exc:
            raise ToolExecutionError(
                "INVALID_ARGUMENTS",
                "tool arguments do not satisfy the frozen query contract",
            ) from exc

    @staticmethod
    def _event_query(
        arguments: Mapping[str, Any],
        *,
        default_limit: int,
    ) -> EventQuery:
        try:
            return EventQuery(
                start_at=AgentToolService._optional_text(
                    arguments,
                    "start_at",
                ),
                end_at=AgentToolService._optional_text(
                    arguments,
                    "end_at",
                ),
                event_type=AgentToolService._optional_text(
                    arguments,
                    "event_type",
                ),
                status=AgentToolService._optional_text(
                    arguments,
                    "status",
                ),
                track_id=AgentToolService._optional_int(
                    arguments,
                    "track_id",
                ),
                limit=AgentToolService._optional_int(
                    arguments,
                    "limit",
                    default=default_limit,
                ),
                offset=AgentToolService._optional_int(
                    arguments,
                    "offset",
                    default=0,
                ),
            )
        except (TypeError, ValueError) as exc:
            raise ToolExecutionError(
                "INVALID_ARGUMENTS",
                "tool arguments do not satisfy the frozen event query contract",
            ) from exc

    @staticmethod
    def _required_text(
        arguments: Mapping[str, Any],
        key: str,
    ) -> str:
        value = arguments.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ToolExecutionError(
                "INVALID_ARGUMENTS",
                f"{key} must be a non-empty string",
            )
        return value.strip()

    @staticmethod
    def _optional_text(
        arguments: Mapping[str, Any],
        key: str,
    ) -> str | None:
        value = arguments.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ToolExecutionError(
                "INVALID_ARGUMENTS",
                f"{key} must be a non-empty string or omitted",
            )
        return value.strip()

    @staticmethod
    def _optional_int(
        arguments: Mapping[str, Any],
        key: str,
        *,
        default: int | None = None,
    ) -> int | None:
        value = arguments.get(key)
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int):
            raise ToolExecutionError(
                "INVALID_ARGUMENTS",
                f"{key} must be an integer or omitted",
            )
        return value
