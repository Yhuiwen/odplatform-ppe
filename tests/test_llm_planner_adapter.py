from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.agent.candidate import build_agent_plan_request_binding
from core.agent.llm_planner import (
    LLMPlannerClientError,
    PlannerCandidateRequestBuilder,
)
from core.agent.tool_registry import STATIC_TOOL_DESCRIPTORS, ToolRegistry
from core.schemas.agent import (
    AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
    AgentAuditStatus,
    AgentIntent,
    AgentRole,
    AgentTool,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
)
from services.agent_audit_service import AgentAuditService
from services.llm_planner_adapter import (
    LLMPlannerAdapter,
    LLMPlannerError,
)

PERIOD = {
    "start_at": "2026-09-01T00:00:00Z",
    "end_at": "2026-09-24T23:59:59Z",
}
FIXED_TIMESTAMP = "2026-09-24T15:00:00Z"


def _clock() -> datetime:
    return datetime(2026, 9, 24, 15, 0, tzinfo=timezone.utc)


def _handler(tool_name: str):
    def handle(arguments, context):
        return ToolResult(
            tool_name=tool_name,
            tool_version="1.0.0",
            status=ToolExecutionStatus.SUCCESS,
            data={},
        )

    return handle


def _registry() -> ToolRegistry:
    return ToolRegistry(
        tuple(
            AgentTool(descriptor, _handler(descriptor.tool_name))
            for descriptor in STATIC_TOOL_DESCRIPTORS
        )
    )


def _context(
    role: AgentRole = AgentRole.SYSTEM,
) -> ToolExecutionContext:
    return ToolExecutionContext(
        request_id="REQ-LLM-PLANNER-1",
        principal_ref="principal:llm-planner-test",
        role=role,
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


def _adapter(client, *, audit=None, registry=None) -> LLMPlannerAdapter:
    return LLMPlannerAdapter(
        registry or _registry(),
        candidate_client=client,
        audit_service=audit or AgentAuditService(clock=_clock),
    )


def test_request_builder_is_deterministic_and_tool_call_free() -> None:
    builder = PlannerCandidateRequestBuilder(_registry())

    first = builder.build("  Give   me the safety summary  ")
    second = builder.build("Give me the safety summary")

    assert first.to_canonical_json() == second.to_canonical_json()
    assert first.normalized_question == "Give me the safety summary"
    assert first.request_binding_sha256 == build_agent_plan_request_binding(
        first.normalized_question
    )
    assert "provider-native tool calling" in first.system_prompt
    assert "get_safety_summary" in first.system_prompt


def test_valid_llm_candidate_is_validated_and_audited() -> None:
    client = _Client(_candidate_bytes)
    audit = AgentAuditService(clock=_clock)
    adapter = _adapter(client, audit=audit)

    outcome = adapter.plan(
        "Give me the safety summary",
        context=_context(),
        requested_period=PERIOD,
    )

    assert client.calls == 1
    assert outcome.planning_path == "LLM_VALIDATED"
    assert outcome.candidate_attempted is True
    assert outcome.fallback_used is False
    assert outcome.plan.intent is AgentIntent.SAFETY_SUMMARY
    assert outcome.plan.tool_name == "get_safety_summary"
    assert len(outcome.audit_events) == 1
    assert outcome.audit_events[0].execution_status is AgentAuditStatus.PLANNED
    assert outcome.audit_events[0].safe_metadata["fallback_used"] is False


def test_malformed_candidate_uses_deterministic_fallback() -> None:
    client = _Client(lambda request: b"{")
    audit = AgentAuditService(clock=_clock)
    adapter = _adapter(client, audit=audit)

    outcome = adapter.plan(
        "Give me the safety summary",
        context=_context(),
        requested_period=PERIOD,
    )

    assert outcome.planning_path == "DETERMINISTIC_FALLBACK"
    assert outcome.candidate_attempted is True
    assert outcome.fallback_used is True
    assert [event.execution_status for event in outcome.audit_events] == [
        AgentAuditStatus.FAILURE,
        AgentAuditStatus.PLANNED,
    ]
    assert outcome.audit_events[0].failure_status == "INVALID_PLANNER_OUTPUT"
    assert outcome.audit_events[1].safe_metadata["fallback_used"] is True


def test_forbidden_candidate_is_refused_without_fallback() -> None:
    client = _Client(
        lambda request: _candidate_bytes(
            request,
            tool_name="run_sql",
        )
    )
    audit = AgentAuditService(clock=_clock)
    adapter = _adapter(client, audit=audit)

    with pytest.raises(LLMPlannerError) as error:
        adapter.plan(
            "Give me the safety summary",
            context=_context(),
            requested_period=PERIOD,
        )

    assert error.value.code == "FORBIDDEN_CAPABILITY"
    assert len(error.value.audit_events) == 1
    assert (
        error.value.audit_events[0].execution_status
        is AgentAuditStatus.REFUSED
    )
    assert len(audit.events()) == 1


def test_provider_failure_uses_deterministic_fallback() -> None:
    def fail(request):
        raise LLMPlannerClientError(
            "PROVIDER_TIMEOUT",
            "provider request timed out",
        )

    client = _Client(fail)
    adapter = _adapter(client)

    outcome = adapter.plan(
        "Give me the safety summary",
        context=_context(),
        requested_period=PERIOD,
    )

    assert outcome.planning_path == "DETERMINISTIC_FALLBACK"
    assert outcome.fallback_used is True
    assert outcome.audit_events[0].execution_status is AgentAuditStatus.FAILURE
    assert outcome.audit_events[0].failure_status == "PROVIDER_TIMEOUT"
    assert outcome.plan.tool_name == "get_safety_summary"


def test_provider_access_requires_capability_and_defers_to_planner() -> None:
    client = _Client(_candidate_bytes)
    adapter = _adapter(client)

    outcome = adapter.plan(
        "Give me the safety summary",
        context=_context(AgentRole.SAFETY_VIEWER),
        requested_period=PERIOD,
    )

    assert client.calls == 0
    assert outcome.planning_path == "DETERMINISTIC"
    assert outcome.candidate_attempted is False
    assert outcome.fallback_used is False


def test_fallback_and_llm_paths_never_execute_a_tool(monkeypatch) -> None:
    registry = _registry()

    def fail_execute(*args, **kwargs):
        raise AssertionError("planner adapter must not execute tools")

    monkeypatch.setattr(registry, "execute", fail_execute)
    valid_adapter = _adapter(_Client(_candidate_bytes), registry=registry)
    fallback_adapter = _adapter(_Client(lambda request: b"not-json"), registry=registry)

    valid = valid_adapter.plan(
        "Give me the safety summary",
        context=_context(),
        requested_period=PERIOD,
    )
    fallback = fallback_adapter.plan(
        "Give me the safety summary",
        context=_context(),
        requested_period=PERIOD,
    )

    assert valid.planning_path == "LLM_VALIDATED"
    assert fallback.planning_path == "DETERMINISTIC_FALLBACK"


def test_audit_metadata_excludes_question_and_candidate_payloads() -> None:
    question = "Give me the safety summary for private site"
    client = _Client(
        lambda request: _candidate_bytes(
            request,
            arguments={**PERIOD, "note": "secret payload"},
        )
    )
    audit = AgentAuditService(clock=_clock)
    adapter = _adapter(client, audit=audit)

    outcome = adapter.plan(
        question,
        context=_context(),
        requested_period=PERIOD,
    )
    serialized = "".join(event.to_json() for event in outcome.audit_events)

    assert "private site" not in serialized
    assert "secret payload" not in serialized
    assert "arguments" not in json.loads(outcome.audit_events[0].to_json())


def test_deterministic_precheck_refuses_before_provider_call() -> None:
    client = _Client(_candidate_bytes)
    audit = AgentAuditService(clock=_clock)
    adapter = _adapter(client, audit=audit)

    with pytest.raises(LLMPlannerError) as error:
        adapter.plan(
            "Delete all events",
            context=_context(),
            requested_period=PERIOD,
        )

    assert error.value.code == "FORBIDDEN_REQUEST"
    assert client.calls == 0
    assert audit.events()[0].execution_status is AgentAuditStatus.REFUSED


def test_llm_planner_modules_have_no_agent_framework_or_system_execution_dependency() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = (
        root / "core" / "agent" / "llm_planner.py",
        root / "services" / "llm_planner_adapter.py",
    )
    forbidden = {
        "ctypes",
        "langchain",
        "llama_index",
        "openai",
        "requests",
        "shutil",
        "socket",
        "subprocess",
        "urllib",
    }

    for path in paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not {
            item
            for item in imported
            if any(
                item == name or item.startswith(f"{name}.")
                for name in forbidden
            )
        }
        assert "registry.execute" not in source
