from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.agent.planner import (
    AgentPlanningError,
    DeterministicAgentPlanner,
)
from core.agent.tool_registry import STATIC_TOOL_DESCRIPTORS, ToolRegistry
from core.schemas.agent import (
    AgentIntent,
    AgentRole,
    AgentTool,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
)

PERIOD = {
    "start_at": "2026-09-01T00:00:00Z",
    "end_at": "2026-09-24T23:59:59Z",
}


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


def _planner() -> DeterministicAgentPlanner:
    return DeterministicAgentPlanner(_registry())


def _context(role: AgentRole) -> ToolExecutionContext:
    return ToolExecutionContext(
        request_id="REQ-PLANNER-1",
        principal_ref="principal:planner-test",
        role=role,
    )


def test_same_question_and_context_produce_same_plan() -> None:
    planner = _planner()

    first = planner.plan(
        "Give me the safety summary",
        context=_context(AgentRole.SAFETY_VIEWER),
        requested_period=PERIOD,
    )
    second = planner.plan(
        "Give me the safety summary",
        context=_context(AgentRole.SAFETY_VIEWER),
        requested_period=PERIOD,
    )

    assert first.to_dict() == second.to_dict()
    assert first.intent is AgentIntent.SAFETY_SUMMARY
    assert first.arguments == {
        "start_at": "2026-09-01T00:00:00Z",
        "end_at": "2026-09-24T23:59:59Z",
    }


@pytest.mark.parametrize(
    ("question", "role", "intent", "tool_name"),
    (
        (
            "Give me the safety summary",
            AgentRole.SAFETY_VIEWER,
            AgentIntent.SAFETY_SUMMARY,
            "get_safety_summary",
        ),
        (
            "Show event statistics for this period",
            AgentRole.SAFETY_VIEWER,
            AgentIntent.EVENT_STATISTICS,
            "get_event_statistics",
        ),
        (
            "Show event details for EVT-AGENT-1",
            AgentRole.EVENT_VIEWER,
            AgentIntent.EVENT_DETAIL,
            "get_event_details",
        ),
        (
            "Generate a safety report",
            AgentRole.SAFETY_REPORTER,
            AgentIntent.SAFETY_REPORT,
            "generate_safety_report",
        ),
    ),
)
def test_supported_intents_map_to_frozen_tools(
    question: str,
    role: AgentRole,
    intent: AgentIntent,
    tool_name: str,
) -> None:
    plan = _planner().plan(
        question,
        context=_context(role),
        requested_period=(
            None if intent is AgentIntent.EVENT_DETAIL else PERIOD
        ),
    )

    assert plan.intent is intent
    assert plan.tool_name == tool_name
    assert plan.tool_name in _registry().tool_names


def test_unknown_intent_is_out_of_scope() -> None:
    planner = _planner()

    assert planner.classify("How is the weather?") is AgentIntent.UNKNOWN
    with pytest.raises(AgentPlanningError) as error:
        planner.plan(
            "How is the weather?",
            context=_context(AgentRole.SYSTEM),
            requested_period=PERIOD,
        )

    assert error.value.code == "OUT_OF_SCOPE"


@pytest.mark.parametrize(
    "question",
    (
        "Delete all events",
        "Update the event status",
        "Run SQL against the event database",
        "Execute a shell command",
        "Grant the administrator permission",
        "删除所有事件",
    ),
)
def test_forbidden_mutation_admin_and_system_requests_are_rejected(
    question: str,
) -> None:
    planner = _planner()

    assert planner.classify(question) is AgentIntent.FORBIDDEN_REQUEST
    with pytest.raises(AgentPlanningError) as error:
        planner.plan(
            question,
            context=_context(AgentRole.SYSTEM),
            requested_period=PERIOD,
        )

    assert error.value.code == "FORBIDDEN_REQUEST"


@pytest.mark.parametrize(
    ("question", "period", "filters", "code"),
    (
        (
            "Give me the safety summary",
            None,
            None,
            "INVALID_REQUEST",
        ),
        (
            "Give me the safety summary",
            {
                "start_at": "2026-09-24T00:00:00Z",
                "end_at": "2026-09-01T00:00:00Z",
            },
            None,
            "INVALID_ARGUMENTS",
        ),
        (
            "Give me the safety summary",
            {
                "start_at": "2024-01-01T00:00:00Z",
                "end_at": "2026-01-02T00:00:00Z",
            },
            None,
            "INVALID_ARGUMENTS",
        ),
        (
            "Give me the safety summary",
            PERIOD,
            {"unknown_filter": "value"},
            "INVALID_ARGUMENTS",
        ),
        (
            "Show event details for EVT-AGENT-1",
            None,
            {"event_id": "../private"},
            "INVALID_ARGUMENTS",
        ),
        (
            "Show event statistics for this period",
            PERIOD,
            {"limit": 101},
            "INVALID_ARGUMENTS",
        ),
    ),
)
def test_invalid_arguments_are_rejected_before_planning(
    question: str,
    period,
    filters,
    code: str,
) -> None:
    planner = _planner()
    role = (
        AgentRole.EVENT_VIEWER
        if "event details" in question
        else AgentRole.SAFETY_VIEWER
    )

    with pytest.raises(AgentPlanningError) as error:
        planner.plan(
            question,
            context=_context(role),
            requested_period=period,
            filters=filters,
        )

    assert error.value.code == code


def test_registry_integration_never_executes_a_tool(monkeypatch) -> None:
    registry = _registry()
    planner = DeterministicAgentPlanner(registry)

    def fail_execute(*args, **kwargs):
        raise AssertionError("planner must not execute tools")

    monkeypatch.setattr(registry, "execute", fail_execute)
    plan = planner.plan(
        "Show event details for EVT-AGENT-1",
        context=_context(AgentRole.EVENT_VIEWER),
    )

    assert plan.tool_name == "get_event_details"
    assert registry.resolve(plan.tool_name) is not None


def test_permission_policy_blocks_unallowed_plan() -> None:
    planner = _planner()

    with pytest.raises(AgentPlanningError) as error:
        planner.plan(
            "Show event details for EVT-AGENT-1",
            context=_context(AgentRole.SAFETY_VIEWER),
        )

    assert error.value.code == "UNAUTHORIZED"


def test_planner_has_no_llm_network_or_execution_dependency() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "core"
        / "agent"
        / "planner.py"
    )
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden = {
        "http",
        "langchain",
        "llama_index",
        "openai",
        "requests",
        "socket",
        "urllib",
    }
    assert not {
        item
        for item in imported
        if any(item == name or item.startswith(f"{name}.") for name in forbidden)
    }
    assert "registry.execute" not in source
