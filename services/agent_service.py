"""AgentService orchestration over validated plans and the static registry."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from core.agent.tool_registry import ToolRegistry, ToolRegistryError
from core.schemas.agent import (
    AGENT_PLAN_SCHEMA_VERSION,
    AgentAuditStatus,
    AgentIntent,
    AgentOutcome,
    AgentPlan,
    AgentRequest,
    AgentResult,
    ToolError,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
)
from services.agent_audit_service import AgentAuditError, AgentAuditService
from services.llm_planner_adapter import (
    LLMPlannerAdapter,
    LLMPlannerError,
    LLMPlannerOutcome,
)

__all__ = ["AgentService"]

_REFUSAL_CODES = frozenset(
    {
        "FORBIDDEN_REQUEST",
        "FORBIDDEN_CAPABILITY",
        "UNAUTHORIZED",
        "INVALID_REQUEST",
        "INVALID_ARGUMENTS",
        "INVALID_REQUEST_BINDING",
        "INVALID_CANDIDATE",
        "INTENT_CONFLICT",
        "TOOL_DISABLED",
    }
)
_TOOL_ERROR_CODES = frozenset(
    {
        "TOOL_NOT_FOUND",
        "TOOL_UNAVAILABLE",
        "TOOL_VERSION_MISMATCH",
        "TOOL_ERROR",
    }
)
_SAFE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,79}$")
_STATISTICS_METRIC_FIELDS = (
    "total_count",
    "by_type",
    "by_status",
    "by_source_ref",
    "by_day",
    "earliest_at",
    "latest_at",
)


class AgentService:
    """Plan one request, execute at most one validated read-only tool, audit."""

    def __init__(self, planner_adapter: LLMPlannerAdapter) -> None:
        if not isinstance(planner_adapter, LLMPlannerAdapter):
            raise TypeError("planner_adapter must be an LLMPlannerAdapter")
        self.planner_adapter = planner_adapter
        self.registry: ToolRegistry = planner_adapter.registry
        self.audit_service: AgentAuditService = planner_adapter.audit_service

    def execute(self, request: AgentRequest) -> AgentResult:
        """Execute one typed request without accepting provider candidate data."""

        if not isinstance(request, AgentRequest):
            raise TypeError("request must be an AgentRequest")
        context = request.to_context()

        try:
            outcome = self.planner_adapter.plan(
                request.question,
                context=context,
                requested_period=request.requested_period,
                filters=request.filters,
            )
        except LLMPlannerError as exc:
            return self._planner_failure(request, context, exc)
        except Exception:
            failure = LLMPlannerError(
                "PLANNER_ERROR",
                "the planner failed safely before tool execution",
            )
            return self._planner_failure(request, context, failure)

        plan = outcome.plan
        if (
            not isinstance(plan, AgentPlan)
            or plan.schema_version != AGENT_PLAN_SCHEMA_VERSION
        ):
            failure = LLMPlannerError(
                "INVALID_PLAN",
                "only a validated phase8-agent-plan-v1 may execute",
            )
            return self._planner_failure(request, context, failure)

        try:
            tool_result = self.registry.execute(
                plan.tool_name,
                plan.arguments,
                context,
            )
        except ToolRegistryError as exc:
            return self._registry_failure(request, context, plan, exc)

        if tool_result.status is not ToolExecutionStatus.SUCCESS:
            return self._non_success_tool_result(
                request,
                outcome,
                context,
                tool_result,
            )

        try:
            projection = self._project_success(plan, tool_result)
        except (TypeError, ValueError):
            tool_error = ToolError(
                code="TOOL_RESULT_INVALID",
                message="tool returned an invalid structured result",
            )
            audit_id = self._record_projection_failure(
                request=request,
                plan=plan,
            )
            if audit_id is None:
                return self._audit_unavailable(
                    request,
                    tool_error,
                    last_audit_id=self._last_audit_id(outcome),
                )
            return AgentResult(
                request_id=request.request_id,
                audit_id=audit_id,
                status=AgentOutcome.TOOL_ERROR,
                answer="The tool returned an invalid structured result.",
                safe_error=tool_error,
            )

        try:
            audit_event = self.audit_service.record_tool_result(
                tool_result,
                context,
                intent=plan.intent,
                plan_id=self._plan_id(plan),
                metadata={
                    "fallback_used": outcome.fallback_used,
                },
            )
        except AgentAuditError:
            return self._audit_unavailable(
                request,
                ToolError(
                    code="AUDIT_UNAVAILABLE",
                    message=(
                        "append-only audit storage did not confirm the "
                        "tool result"
                    ),
                ),
                last_audit_id=self._last_audit_id(outcome),
            )

        facts, metrics, event_refs, evidence_refs, report = projection
        status = (
            AgentOutcome.INSUFFICIENT_DATA
            if self._is_empty_success(plan.intent, tool_result.data)
            else AgentOutcome.ANSWERED
        )
        return AgentResult(
            request_id=request.request_id,
            audit_id=audit_event.audit_id,
            status=status,
            answer=self._answer(plan.intent, tool_result.data),
            facts=facts,
            metrics=metrics,
            event_refs=event_refs,
            evidence_refs=evidence_refs,
            report=report,
        )

    def _planner_failure(
        self,
        request: AgentRequest,
        context: ToolExecutionContext,
        error: LLMPlannerError,
    ) -> AgentResult:
        code = self._safe_code(error.code, "PLANNER_ERROR")
        status = self._planner_outcome(code)
        tool_error = ToolError(
            code=code,
            message=self._safe_message(
                error.message,
                "the planner failed safely",
            ),
        )

        audit_id = self._last_audit_id_from_tuple(error.audit_events)
        if audit_id is None:
            audit_id = self._record_planner_failure(
                request=request,
                context=context,
                code=code,
                status=status,
            )
        if audit_id is None:
            return self._audit_unavailable(request, tool_error, None)
        return AgentResult(
            request_id=request.request_id,
            audit_id=audit_id,
            status=status,
            answer=self._failure_answer(status),
            safe_error=tool_error,
        )

    def _non_success_tool_result(
        self,
        request: AgentRequest,
        outcome: LLMPlannerOutcome,
        context: ToolExecutionContext,
        tool_result: ToolResult,
    ) -> AgentResult:
        try:
            audit_event = self.audit_service.record_tool_result(
                tool_result,
                context,
                intent=outcome.plan.intent,
                plan_id=self._plan_id(outcome.plan),
                metadata={
                    "fallback_used": outcome.fallback_used,
                },
            )
        except AgentAuditError:
            return self._audit_unavailable(
                request,
                ToolError(
                    code="AUDIT_UNAVAILABLE",
                    message=(
                        "append-only audit storage did not confirm the "
                        "tool result"
                    ),
                ),
                last_audit_id=self._last_audit_id(outcome),
            )

        safe_error = tool_result.safe_error or ToolError(
            code="TOOL_ERROR",
            message="tool execution failed safely",
        )
        status = (
            AgentOutcome.REFUSED
            if tool_result.status is ToolExecutionStatus.REFUSED
            else AgentOutcome.TOOL_ERROR
        )
        return AgentResult(
            request_id=request.request_id,
            audit_id=audit_event.audit_id,
            status=status,
            answer=self._failure_answer(status),
            safe_error=safe_error,
        )

    def _registry_failure(
        self,
        request: AgentRequest,
        context: ToolExecutionContext,
        plan: AgentPlan,
        error: ToolRegistryError,
    ) -> AgentResult:
        code = self._safe_code(error.code, "TOOL_ERROR")
        status = (
            AgentAuditStatus.UNKNOWN_TOOL
            if code == "TOOL_NOT_FOUND"
            else AgentAuditStatus.FAILURE
        )
        try:
            audit_event = self.audit_service.record_event(
                request_id=request.request_id,
                principal_ref=request.principal_ref,
                role_ref=request.role,
                intent=plan.intent,
                plan_id=self._plan_id(plan),
                tools_requested=(plan.tool_name,),
                execution_status=status,
                failure_status=code,
                question_sha256=plan.question_sha256,
            )
        except AgentAuditError:
            return self._audit_unavailable(
                request,
                ToolError(
                    code="AUDIT_UNAVAILABLE",
                    message="the registry failure could not be audited",
                ),
                None,
            )
        return AgentResult(
            request_id=request.request_id,
            audit_id=audit_event.audit_id,
            status=AgentOutcome.TOOL_ERROR,
            answer=self._failure_answer(AgentOutcome.TOOL_ERROR),
            safe_error=ToolError(
                code=code,
                message=self._safe_message(
                    error.message,
                    "tool execution failed safely",
                ),
            ),
        )

    def _record_planner_failure(
        self,
        *,
        request: AgentRequest,
        context: ToolExecutionContext,
        code: str,
        status: AgentOutcome,
    ) -> str | None:
        if status is AgentOutcome.AUDIT_UNAVAILABLE:
            return None
        audit_status = (
            AgentAuditStatus.REFUSED
            if status in {AgentOutcome.REFUSED, AgentOutcome.OUT_OF_SCOPE}
            else AgentAuditStatus.FAILURE
        )
        intent = (
            AgentIntent.FORBIDDEN_REQUEST
            if code in {"FORBIDDEN_REQUEST", "FORBIDDEN_CAPABILITY"}
            else AgentIntent.UNKNOWN
        )
        try:
            event = self.audit_service.record_event(
                request_id=request.request_id,
                principal_ref=request.principal_ref,
                role_ref=request.role,
                intent=intent,
                plan_id=self._failure_plan_id(context, code),
                tools_requested=(),
                execution_status=audit_status,
                failure_status=code,
            )
        except AgentAuditError:
            return None
        return event.audit_id

    def _record_projection_failure(
        self,
        *,
        request: AgentRequest,
        plan: AgentPlan,
    ) -> str | None:
        try:
            event = self.audit_service.record_event(
                request_id=request.request_id,
                principal_ref=request.principal_ref,
                role_ref=request.role,
                intent=plan.intent,
                plan_id=self._plan_id(plan),
                tools_requested=(plan.tool_name,),
                execution_status=AgentAuditStatus.FAILURE,
                failure_status="TOOL_RESULT_INVALID",
                question_sha256=plan.question_sha256,
                metadata={"tool_version": plan.tool_version},
            )
        except AgentAuditError:
            return None
        return event.audit_id

    @staticmethod
    def _planner_outcome(code: str) -> AgentOutcome:
        if code == "AUDIT_UNAVAILABLE":
            return AgentOutcome.AUDIT_UNAVAILABLE
        if code == "OUT_OF_SCOPE":
            return AgentOutcome.OUT_OF_SCOPE
        if code in _REFUSAL_CODES:
            return AgentOutcome.REFUSED
        if code in _TOOL_ERROR_CODES:
            return AgentOutcome.TOOL_ERROR
        return AgentOutcome.TOOL_ERROR

    @staticmethod
    def _project_success(
        plan: AgentPlan,
        result: ToolResult,
    ) -> tuple[
        tuple[Mapping[str, Any], ...],
        tuple[Mapping[str, Any], ...],
        tuple[str, ...],
        tuple[str, ...],
        Mapping[str, Any] | None,
    ]:
        if plan.intent is AgentIntent.SAFETY_SUMMARY:
            facts = AgentService._mapping_list(
                result.data.get("observed_facts", ()),
                "observed_facts",
            )
            metrics = AgentService._mapping_list(
                result.data.get("calculated_metrics", ()),
                "calculated_metrics",
            )
            event_refs, evidence_refs = AgentService._fact_references(facts)
            return facts, metrics, event_refs, evidence_refs, None

        if plan.intent is AgentIntent.EVENT_STATISTICS:
            metrics = tuple(
                {
                    "metric_id": f"event_statistics.{field_name}",
                    "value": result.data[field_name],
                }
                for field_name in _STATISTICS_METRIC_FIELDS
                if field_name in result.data
            )
            return (), metrics, (), (), None

        if plan.intent is AgentIntent.EVENT_DETAIL:
            facts = AgentService._mapping_list(
                result.data.get("events", ()),
                "events",
            )
            total_count = result.data.get("total_count", len(facts))
            if isinstance(total_count, bool) or not isinstance(total_count, int):
                raise ValueError("total_count must be an integer")
            metrics = (
                {
                    "metric_id": "event_details.total_count",
                    "value": total_count,
                },
            )
            event_refs = tuple(
                AgentService._safe_output_reference(item["id"], "event_ref")
                for item in facts
                if item.get("id") is not None
            )
            evidence_refs = tuple(
                AgentService._safe_output_reference(
                    item["snapshot_ref"],
                    "evidence_ref",
                )
                for item in facts
                if item.get("snapshot_ref") is not None
            )
            return facts, metrics, event_refs, evidence_refs, None

        if plan.intent is AgentIntent.SAFETY_REPORT:
            report = result.data.get("report")
            if not isinstance(report, Mapping):
                raise ValueError("report result must contain a report mapping")
            return (), (), (), (), report

        raise ValueError("plan intent does not have a result projection")

    @staticmethod
    def _mapping_list(
        value: Any,
        field_name: str,
    ) -> tuple[Mapping[str, Any], ...]:
        if not isinstance(value, (list, tuple)):
            raise TypeError(f"{field_name} must be a list or tuple")
        if any(not isinstance(item, Mapping) for item in value):
            raise TypeError(f"{field_name} must contain mappings")
        return tuple(item for item in value)

    @staticmethod
    def _fact_references(
        facts: tuple[Mapping[str, Any], ...],
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        event_refs = tuple(
            AgentService._safe_output_reference(
                fact["event_id"],
                "event_ref",
            )
            for fact in facts
            if fact.get("event_id") is not None
        )
        evidence_refs = tuple(
            AgentService._safe_output_reference(
                fact["snapshot_ref"],
                "evidence_ref",
            )
            for fact in facts
            if fact.get("snapshot_ref") is not None
        )
        return event_refs, evidence_refs

    @staticmethod
    def _safe_output_reference(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        normalized = value.strip()
        if (
            len(normalized) > 300
            or normalized.startswith("/")
            or "\\" in normalized
            or re.match(r"^[A-Za-z]:/", normalized) is not None
        ):
            raise ValueError(f"{field_name} must be a relative reference")
        if any(
            part in {"", ".", ".."}
            for part in normalized.split("/")
        ):
            raise ValueError(f"{field_name} contains an unsafe segment")
        return normalized

    @staticmethod
    def _is_empty_success(
        intent: AgentIntent,
        data: Mapping[str, Any],
    ) -> bool:
        if intent is AgentIntent.SAFETY_SUMMARY:
            facts = data.get("observed_facts", ())
            return isinstance(facts, (list, tuple)) and not facts
        if intent is AgentIntent.EVENT_STATISTICS:
            return data.get("total_count") == 0
        if intent is AgentIntent.EVENT_DETAIL:
            return data.get("total_count") == 0
        return False

    @staticmethod
    def _answer(intent: AgentIntent, data: Mapping[str, Any]) -> str:
        if intent is AgentIntent.SAFETY_SUMMARY:
            facts = data.get("observed_facts", ())
            count = len(facts) if isinstance(facts, (list, tuple)) else 0
            return f"Safety summary returned {count} event(s)."
        if intent is AgentIntent.EVENT_STATISTICS:
            return (
                "Event statistics returned total_count="
                f"{data.get('total_count', 0)}."
            )
        if intent is AgentIntent.EVENT_DETAIL:
            count = data.get("total_count", 0)
            return f"Retrieved {count} event detail record(s)."
        if intent is AgentIntent.SAFETY_REPORT:
            generation_path = data.get("generation_path", "UNKNOWN")
            return f"Safety report generated via {generation_path}."
        return "The validated tool completed successfully."

    @staticmethod
    def _failure_answer(status: AgentOutcome) -> str:
        if status is AgentOutcome.OUT_OF_SCOPE:
            return "The request is outside the supported read-only scope."
        if status is AgentOutcome.REFUSED:
            return "The request was refused by the Agent policy."
        if status is AgentOutcome.AUDIT_UNAVAILABLE:
            return "Audit storage is unavailable; no successful result released."
        return "The read-only tool failed safely."

    @staticmethod
    def _plan_id(plan: AgentPlan) -> str:
        digest = hashlib.sha256(
            (
                f"{plan.tool_name}:{plan.tool_version}:"
                f"{plan.question_sha256}:{plan.intent.value}"
            ).encode("utf-8")
        ).hexdigest()[:16]
        return f"PLAN-{digest}"

    @staticmethod
    def _failure_plan_id(
        context: ToolExecutionContext,
        code: str,
    ) -> str:
        digest = hashlib.sha256(
            f"{context.request_id}:{context.principal_ref}:{code}".encode(
                "utf-8"
            )
        ).hexdigest()[:16]
        return f"PLAN-{digest}"

    @staticmethod
    def _last_audit_id(outcome: LLMPlannerOutcome) -> str | None:
        return AgentService._last_audit_id_from_tuple(outcome.audit_events)

    @staticmethod
    def _last_audit_id_from_tuple(events: tuple[Any, ...]) -> str | None:
        if not events:
            return None
        return events[-1].audit_id

    @staticmethod
    def _audit_unavailable(
        request: AgentRequest,
        error: ToolError,
        last_audit_id: str | None,
    ) -> AgentResult:
        return AgentResult(
            request_id=request.request_id,
            audit_id=last_audit_id,
            status=AgentOutcome.AUDIT_UNAVAILABLE,
            answer=AgentService._failure_answer(
                AgentOutcome.AUDIT_UNAVAILABLE
            ),
            safe_error=error,
        )

    @staticmethod
    def _safe_message(message: str, fallback: str) -> str:
        if not isinstance(message, str) or not message.strip():
            return fallback
        normalized = message.strip()
        if len(normalized) <= 300:
            return normalized
        return normalized[:297] + "..."

    @staticmethod
    def _safe_code(code: str, fallback: str) -> str:
        if not isinstance(code, str):
            return fallback
        normalized = code.strip().upper().replace("-", "_")
        if _SAFE_CODE_PATTERN.fullmatch(normalized) is None:
            return fallback
        return normalized
