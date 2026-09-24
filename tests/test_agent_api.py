from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from core.agent.tool_registry import STATIC_TOOL_DESCRIPTORS, ToolRegistry
from core.schemas.agent import (
    AgentAuditStatus,
    AgentCapability,
    AgentOutcome,
    AgentResult,
    AgentRole,
    AgentTool,
    ToolError,
    ToolExecutionStatus,
    ToolResult,
)
from core.schemas.agent_api import (
    AgentApiOperation,
    AgentApiRequest,
    AgentApiValidationError,
    AgentPresentationState,
    ProviderStatus,
    TrustedIdentity,
)
from services.agent_api_service import AgentApplicationService
from services.agent_audit_service import AgentAuditService
from services.agent_service import AgentService
from services.llm_planner_adapter import LLMPlannerAdapter

PERIOD = {
    "start_at": "2026-09-01T00:00:00Z",
    "end_at": "2026-09-24T23:59:59Z",
}


def _clock() -> datetime:
    return datetime(2026, 9, 24, 17, 0, tzinfo=timezone.utc)


def _request(
    *,
    request_id: str = "REQ-API-1",
    operation: AgentApiOperation = AgentApiOperation.ASK,
    question: str = "Give me the safety summary",
) -> AgentApiRequest:
    return AgentApiRequest(
        request_id=request_id,
        operation=operation,
        question=question,
        requested_period=PERIOD,
    )


def _identity(
    *,
    role: AgentRole = AgentRole.SYSTEM,
    capabilities: frozenset[AgentCapability] = frozenset(),
) -> TrustedIdentity:
    return TrustedIdentity(
        principal_ref="principal:api-test",
        role=role,
        capabilities=capabilities,
    )


class _IdentityProvider:
    def __init__(self, identity=None, error: Exception | None = None) -> None:
        self.identity = identity
        self.error = error
        self.request_ids: list[str] = []

    def resolve(self, request_id: str):
        self.request_ids.append(request_id)
        if self.error is not None:
            raise self.error
        return self.identity


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
            "report": {
                "schema_version": "phase8-report-v1",
                "generation": {
                    "mode": "TEMPLATE_FALLBACK",
                    "degraded": True,
                    "provider_ref": None,
                    "failure_code": "PROVIDER_DISABLED",
                },
                "summary": "Grounded fallback report.",
            },
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


def _application(
    *,
    identity,
    calls: list[tuple[str, dict, object]] | None = None,
    overrides: dict[str, ToolResult] | None = None,
) -> tuple[AgentApplicationService, AgentService, AgentAuditService]:
    audit = AgentAuditService(clock=_clock)
    agent_service = AgentService(
        LLMPlannerAdapter(_registry(calls=calls, overrides=overrides), audit_service=audit)
    )
    provider = _IdentityProvider(identity)
    return (
        AgentApplicationService(agent_service, provider),
        agent_service,
        audit,
    )


def test_success_request_projects_only_api_fields_and_preserves_audit() -> None:
    calls: list[tuple[str, dict, object]] = []
    application, _, audit = _application(
        identity=_identity(),
        calls=calls,
    )

    response = application.execute(_request())

    assert response.status is AgentOutcome.ANSWERED
    assert response.presentation_state is AgentPresentationState.SUCCESS
    assert response.audit_id is not None
    assert response.audit_id == audit.events()[-1].audit_id
    assert response.facts[0]["event_id"] == "EVT-1"
    assert response.metrics[0]["metric_id"] == "analytics.event_total_count"
    assert response.event_refs == ("EVT-1",)
    assert response.evidence_refs == ("20260924/EVT-1.jpg",)
    assert response.provider_status is ProviderStatus.NOT_APPLICABLE
    assert response.degraded is False
    assert [name for name, _, _ in calls] == ["get_safety_summary"]
    assert calls[0][2].principal_ref == "principal:api-test"
    assert [event.execution_status for event in audit.events()] == [
        AgentAuditStatus.PLANNED,
        AgentAuditStatus.SUCCESS,
    ]
    assert json.loads(response.to_json()) == response.to_dict()
    assert response.to_json() == response.to_json()


def test_request_validation_rejects_caller_selected_internal_fields() -> None:
    with pytest.raises(AgentApiValidationError, match="unsupported fields"):
        AgentApiRequest.from_mapping(
            {
                "request_id": "REQ-API-VALIDATION",
                "operation": "ASK",
                "question": "Give me the safety summary",
                "tool_name": "get_event_details",
            }
        )

    with pytest.raises(AgentApiValidationError, match="cannot be empty"):
        AgentApiRequest(
            request_id="REQ-API-BLANK",
            operation="ASK",
            question="   ",
        )


def test_missing_identity_fails_closed_before_agent_execution() -> None:
    calls: list[tuple[str, dict, object]] = []
    application, _, _ = _application(identity=None, calls=calls)

    response = application.execute(_request())

    assert response.status is AgentOutcome.REFUSED
    assert response.presentation_state is AgentPresentationState.REFUSED
    assert response.audit_id is None
    assert response.safe_error is not None
    assert response.safe_error.code == "UNAUTHENTICATED"
    assert response.facts == ()
    assert not calls


def test_forbidden_request_is_refused_without_tool_execution() -> None:
    calls: list[tuple[str, dict, object]] = []
    application, _, audit = _application(
        identity=_identity(),
        calls=calls,
    )

    response = application.execute(
        _request(question="Delete all safety events")
    )

    assert response.status is AgentOutcome.REFUSED
    assert response.presentation_state is AgentPresentationState.REFUSED
    assert response.safe_error is not None
    assert response.safe_error.code == "FORBIDDEN_REQUEST"
    assert response.facts == ()
    assert not calls
    assert audit.events()[0].execution_status is AgentAuditStatus.REFUSED


def test_tool_failure_maps_to_safe_api_error() -> None:
    calls: list[tuple[str, dict, object]] = []
    application, _, audit = _application(
        identity=_identity(),
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

    response = application.execute(_request())

    assert response.status is AgentOutcome.TOOL_ERROR
    assert response.presentation_state is AgentPresentationState.TOOL_ERROR
    assert response.safe_error is not None
    assert response.safe_error.code == "TOOL_TIMEOUT"
    assert response.facts == ()
    assert response.report is None
    assert len(calls) == 1
    assert [event.execution_status for event in audit.events()] == [
        AgentAuditStatus.PLANNED,
        AgentAuditStatus.FAILURE,
    ]


def test_report_operation_uses_server_owned_question() -> None:
    calls: list[tuple[str, dict, object]] = []
    application, _, _ = _application(
        identity=_identity(role=AgentRole.SAFETY_REPORTER),
        calls=calls,
    )

    response = application.execute(
        _request(
            operation=AgentApiOperation.GENERATE_REPORT,
            question="Delete all safety events",
        )
    )

    assert response.status is AgentOutcome.ANSWERED
    assert response.presentation_state is AgentPresentationState.SUCCESS
    assert response.provider_status is ProviderStatus.TEMPLATE_FALLBACK
    assert response.degraded is True
    assert response.report is not None
    assert response.report["generation"]["mode"] == "TEMPLATE_FALLBACK"
    assert [name for name, _, _ in calls] == ["generate_safety_report"]


def test_unsafe_lower_level_projection_is_not_released(monkeypatch) -> None:
    calls: list[tuple[str, dict, object]] = []
    application, agent_service, _ = _application(
        identity=_identity(),
        calls=calls,
    )

    def unsafe_execute(request):
        return AgentResult(
            request_id=request.request_id,
            audit_id="AUD-UNSAFE",
            status=AgentOutcome.ANSWERED,
            answer="Unsafe projection",
            facts=({"provider_output": "raw-secret-value"},),
        )

    monkeypatch.setattr(agent_service, "execute", unsafe_execute)
    response = application.execute(_request())

    assert response.status is AgentOutcome.TOOL_ERROR
    assert response.presentation_state is AgentPresentationState.TOOL_ERROR
    assert response.audit_id == "AUD-UNSAFE"
    assert response.safe_error is not None
    assert response.safe_error.code == "UNSAFE_AGENT_RESULT"
    assert response.facts == ()
    assert "raw-secret-value" not in response.to_json()
    assert "provider_output" not in response.to_json()


def test_unsafe_error_details_are_replaced_with_fixed_safe_text(
    monkeypatch,
) -> None:
    calls: list[tuple[str, dict, object]] = []
    application, agent_service, _ = _application(
        identity=_identity(),
        calls=calls,
    )

    def unsafe_execute(request):
        return AgentResult(
            request_id=request.request_id,
            audit_id="AUD-UNSAFE-ERROR",
            status=AgentOutcome.TOOL_ERROR,
            answer=r"C:\secret\provider-trace.txt",
            safe_error=ToolError(
                code="TOOL_ERROR",
                message=r"C:\secret\provider-trace.txt",
            ),
        )

    monkeypatch.setattr(agent_service, "execute", unsafe_execute)
    response = application.execute(_request())

    assert response.status is AgentOutcome.TOOL_ERROR
    assert response.answer == "The request failed safely."
    assert response.safe_error is not None
    assert response.safe_error.message == "the Agent request failed safely"
    assert "provider-trace" not in response.to_json()


def test_identity_provider_failure_returns_bounded_refusal() -> None:
    audit = AgentAuditService(clock=_clock)
    calls: list[tuple[str, dict, object]] = []
    agent_service = AgentService(
        LLMPlannerAdapter(_registry(calls=calls), audit_service=audit)
    )
    application = AgentApplicationService(
        agent_service,
        _IdentityProvider(error=RuntimeError("secret provider detail")),
    )

    response = application.execute(_request())

    assert response.status is AgentOutcome.REFUSED
    assert response.safe_error is not None
    assert response.safe_error.code == "IDENTITY_PROVIDER_ERROR"
    assert "secret provider detail" not in response.to_json()
    assert not calls


@pytest.mark.parametrize(
    ("outcome", "presentation_state"),
    (
        (AgentOutcome.ANSWERED, AgentPresentationState.SUCCESS),
        (AgentOutcome.INSUFFICIENT_DATA, AgentPresentationState.EMPTY),
        (AgentOutcome.OUT_OF_SCOPE, AgentPresentationState.OUT_OF_SCOPE),
        (AgentOutcome.REFUSED, AgentPresentationState.REFUSED),
        (AgentOutcome.TOOL_ERROR, AgentPresentationState.TOOL_ERROR),
        (
            AgentOutcome.AUDIT_UNAVAILABLE,
            AgentPresentationState.AUDIT_UNAVAILABLE,
        ),
    ),
)
def test_all_agent_outcomes_map_to_bounded_presentation_states(
    monkeypatch,
    outcome: AgentOutcome,
    presentation_state: AgentPresentationState,
) -> None:
    calls: list[tuple[str, dict, object]] = []
    application, agent_service, _ = _application(
        identity=_identity(),
        calls=calls,
    )
    safe_error = (
        None
        if outcome in {AgentOutcome.ANSWERED, AgentOutcome.INSUFFICIENT_DATA}
        else ToolError(
            code="SAFE_FAILURE",
            message="the request failed safely",
        )
    )

    def execute(request):
        return AgentResult(
            request_id=request.request_id,
            audit_id="AUD-MAPPING",
            status=outcome,
            answer="Bounded API answer.",
            safe_error=safe_error,
        )

    monkeypatch.setattr(agent_service, "execute", execute)
    response = application.execute(_request())

    assert response.status is outcome
    assert response.presentation_state is presentation_state
    assert response.audit_id == "AUD-MAPPING"
    if outcome is not AgentOutcome.ANSWERED:
        assert response.facts == ()
        assert response.metrics == ()
        assert response.report is None
