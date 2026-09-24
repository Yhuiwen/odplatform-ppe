from __future__ import annotations

import json
from datetime import datetime, timezone

from core.agent.llm_planner import LLMPlannerClientError
from core.agent.tool_registry import STATIC_TOOL_DESCRIPTORS, ToolRegistry
from core.schemas.agent import (
    AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
    AGENT_RESULT_SCHEMA_VERSION,
    AgentAuditStatus,
    AgentOutcome,
    AgentRequest,
    AgentRole,
    AgentTool,
    ToolError,
    ToolExecutionStatus,
    ToolResult,
)
from infra.storage.agent_audit_store import AgentAuditStoreError
from services.agent_audit_service import AgentAuditService
from services.agent_service import AgentService
from services.llm_planner_adapter import LLMPlannerAdapter, LLMPlannerError

PERIOD = {
    "start_at": "2026-09-01T00:00:00Z",
    "end_at": "2026-09-24T23:59:59Z",
}


def _clock() -> datetime:
    return datetime(2026, 9, 24, 16, 0, tzinfo=timezone.utc)


def _request(
    question: str = "Give me the safety summary",
    *,
    role: AgentRole = AgentRole.SYSTEM,
) -> AgentRequest:
    return AgentRequest(
        request_id="REQ-AGENT-SERVICE-1",
        principal_ref="principal:agent-service-test",
        role=role,
        question=question,
        requested_period=PERIOD,
    )


def _success_data(tool_name: str) -> dict:
    if tool_name == "get_safety_summary":
        return {
            "observed_facts": [
                {
                    "fact_id": "EVT:EVT-1",
                    "event_id": "EVT-1",
                    "snapshot_ref": "20260924/EVT-1.jpg",
                }
            ],
            "calculated_metrics": [
                {
                    "metric_id": "analytics.event_total_count",
                    "value": 1,
                }
            ],
        }
    if tool_name == "get_event_statistics":
        return {
            "total_count": 1,
            "by_type": {"NO_HELMET": 1},
            "by_status": {"OPEN": 1},
            "by_source_ref": {"SRC-0123456789abcdef": 1},
            "by_day": {"2026-09-24": 1},
            "earliest_at": "2026-09-24T12:00:00Z",
            "latest_at": "2026-09-24T12:00:00Z",
        }
    if tool_name == "get_event_details":
        return {
            "events": [
                {
                    "id": "EVT-1",
                    "snapshot_ref": "20260924/EVT-1.jpg",
                }
            ],
            "total_count": 1,
        }
    if tool_name == "generate_safety_report":
        return {
            "status": "TEMPLATE_FALLBACK",
            "generation_path": "TEMPLATE_FALLBACK",
            "degraded": True,
            "report": {"schema_version": "phase8-report-v1"},
        }
    raise AssertionError(f"unexpected tool: {tool_name}")


def _registry(
    *,
    calls: list[tuple[str, dict, object]] | None = None,
    overrides: dict[str, ToolResult] | None = None,
) -> ToolRegistry:
    calls = [] if calls is None else calls
    overrides = {} if overrides is None else overrides

    def handler(tool_name: str):
        def handle(arguments, context):
            calls.append((tool_name, dict(arguments), context))
            if tool_name in overrides:
                return overrides[tool_name]
            return ToolResult(
                tool_name=tool_name,
                tool_version="1.0.0",
                status=ToolExecutionStatus.SUCCESS,
                data=_success_data(tool_name),
                row_count=1,
            )

        return handle

    return ToolRegistry(
        tuple(
            AgentTool(descriptor, handler(descriptor.tool_name))
            for descriptor in STATIC_TOOL_DESCRIPTORS
        )
    )


def _adapter(
    registry: ToolRegistry,
    audit: AgentAuditService,
    client=None,
) -> LLMPlannerAdapter:
    return LLMPlannerAdapter(
        registry,
        candidate_client=client,
        audit_service=audit,
    )


class _Client:
    def __init__(self, handler) -> None:
        self.handler = handler
        self.calls = 0

    def generate_candidate(self, request):
        self.calls += 1
        return self.handler(request)


def _candidate_bytes(
    request,
    *,
    intent: str = "SAFETY_SUMMARY",
    tool_name: str = "get_safety_summary",
    arguments=None,
    reason_code: str = "SUMMARY_REQUEST",
) -> bytes:
    return json.dumps(
        {
            "schema_version": AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
            "request_binding_sha256": request.request_binding_sha256,
            "proposed_intent": intent,
            "proposed_tool_name": tool_name,
            "proposed_tool_version": "1.0.0",
            "proposed_arguments": (
                dict(PERIOD) if arguments is None else arguments
            ),
            "reason_code": reason_code,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def test_full_successful_flow_executes_registry_and_records_audit() -> None:
    calls: list[tuple[str, dict, object]] = []
    audit = AgentAuditService(clock=_clock)
    service = AgentService(
        _adapter(_registry(calls=calls), audit),
    )

    result = service.execute(_request())

    assert result.status is AgentOutcome.ANSWERED
    assert result.audit_id is not None
    assert result.facts[0]["event_id"] == "EVT-1"
    assert result.metrics[0]["metric_id"] == "analytics.event_total_count"
    assert result.event_refs == ("EVT-1",)
    assert result.evidence_refs == ("20260924/EVT-1.jpg",)
    assert result.report is None
    assert [name for name, _, _ in calls] == ["get_safety_summary"]
    assert [event.execution_status for event in audit.events()] == [
        AgentAuditStatus.PLANNED,
        AgentAuditStatus.SUCCESS,
    ]
    payload = result.to_dict()
    assert payload["schema_version"] == AGENT_RESULT_SCHEMA_VERSION
    assert json.loads(result.to_json()) == payload


def test_llm_planner_success_still_executes_only_the_validated_plan() -> None:
    calls: list[tuple[str, dict, object]] = []
    audit = AgentAuditService(clock=_clock)
    client = _Client(_candidate_bytes)
    service = AgentService(
        _adapter(_registry(calls=calls), audit, client),
    )

    result = service.execute(_request())

    assert client.calls == 1
    assert result.status is AgentOutcome.ANSWERED
    assert len(calls) == 1
    tool_name, arguments, context = calls[0]
    assert tool_name == "get_safety_summary"
    assert arguments == PERIOD
    assert context.request_id == "REQ-AGENT-SERVICE-1"
    assert [event.execution_status for event in audit.events()] == [
        AgentAuditStatus.PLANNED,
        AgentAuditStatus.SUCCESS,
    ]


def test_llm_planner_failure_uses_deterministic_fallback() -> None:
    calls: list[tuple[str, dict, object]] = []
    audit = AgentAuditService(clock=_clock)

    def fail(request):
        raise LLMPlannerClientError(
            "PROVIDER_TIMEOUT",
            "provider request timed out",
        )

    service = AgentService(
        _adapter(_registry(calls=calls), audit, _Client(fail)),
    )

    result = service.execute(_request())

    assert result.status is AgentOutcome.ANSWERED
    assert [name for name, _, _ in calls] == ["get_safety_summary"]
    assert [event.execution_status for event in audit.events()] == [
        AgentAuditStatus.FAILURE,
        AgentAuditStatus.PLANNED,
        AgentAuditStatus.SUCCESS,
    ]
    assert audit.events()[0].failure_status == "PROVIDER_TIMEOUT"


def test_forbidden_request_is_refused_without_tool_execution() -> None:
    calls: list[tuple[str, dict, object]] = []
    audit = AgentAuditService(clock=_clock)
    service = AgentService(_adapter(_registry(calls=calls), audit))

    result = service.execute(_request("Delete all events"))

    assert result.status is AgentOutcome.REFUSED
    assert result.safe_error is not None
    assert result.safe_error.code == "FORBIDDEN_REQUEST"
    assert not calls
    assert audit.events()[0].execution_status is AgentAuditStatus.REFUSED


def test_tool_failure_is_structured_and_audited() -> None:
    calls: list[tuple[str, dict, object]] = []
    registry = _registry(
        calls=calls,
        overrides={
            "get_safety_summary": ToolResult(
                tool_name="get_safety_summary",
                tool_version="1.0.0",
                status=ToolExecutionStatus.ERROR,
                data={},
                safe_error=ToolError(
                    code="TOOL_TIMEOUT",
                    message="tool execution timed out safely",
                ),
            )
        },
    )
    audit = AgentAuditService(clock=_clock)
    service = AgentService(_adapter(registry, audit))

    result = service.execute(_request())

    assert result.status is AgentOutcome.TOOL_ERROR
    assert result.safe_error is not None
    assert result.safe_error.code == "TOOL_TIMEOUT"
    assert len(calls) == 1
    assert [event.execution_status for event in audit.events()] == [
        AgentAuditStatus.PLANNED,
        AgentAuditStatus.FAILURE,
    ]


def test_planner_failure_without_its_own_event_is_still_audited(
    monkeypatch,
) -> None:
    calls: list[tuple[str, dict, object]] = []
    audit = AgentAuditService(clock=_clock)
    adapter = _adapter(_registry(calls=calls), audit)

    def fail_plan(*args, **kwargs):
        raise LLMPlannerError(
            "INVALID_REQUEST",
            "question is invalid",
        )

    monkeypatch.setattr(adapter, "plan", fail_plan)
    result = AgentService(adapter).execute(_request())

    assert result.status is AgentOutcome.REFUSED
    assert not calls
    assert len(audit.events()) == 1
    assert audit.events()[0].execution_status is AgentAuditStatus.REFUSED
    assert audit.events()[0].failure_status == "INVALID_REQUEST"


class _FailSecondAuditStore:
    def __init__(self) -> None:
        self._events = []

    def append(self, event) -> None:
        if self._events:
            raise AgentAuditStoreError("second append unavailable")
        self._events.append(event)

    def events(self):
        return tuple(self._events)


def test_tool_result_audit_failure_fails_closed() -> None:
    calls: list[tuple[str, dict, object]] = []
    audit = AgentAuditService(
        store=_FailSecondAuditStore(),
        clock=_clock,
    )
    service = AgentService(_adapter(_registry(calls=calls), audit))

    result = service.execute(_request())

    assert result.status is AgentOutcome.AUDIT_UNAVAILABLE
    assert result.safe_error is not None
    assert result.safe_error.code == "AUDIT_UNAVAILABLE"
    assert len(calls) == 1
    assert len(audit.events()) == 1
    assert audit.events()[0].execution_status is AgentAuditStatus.PLANNED


def test_empty_success_is_reported_as_insufficient_data() -> None:
    calls: list[tuple[str, dict, object]] = []
    registry = _registry(
        calls=calls,
        overrides={
            "get_safety_summary": ToolResult(
                tool_name="get_safety_summary",
                tool_version="1.0.0",
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "observed_facts": [],
                    "calculated_metrics": [],
                },
            )
        },
    )
    audit = AgentAuditService(clock=_clock)

    result = AgentService(_adapter(registry, audit)).execute(_request())

    assert result.status is AgentOutcome.INSUFFICIENT_DATA
    assert result.audit_id is not None
    assert result.facts == ()
    assert result.metrics == ()
