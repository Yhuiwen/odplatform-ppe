from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.agent.candidate import (
    AgentPlanCandidateError,
    AgentPlanCandidateParser,
    AgentPlanCandidateValidator,
    build_agent_plan_request_binding,
)
from core.agent.tool_registry import STATIC_TOOL_DESCRIPTORS, ToolRegistry
from core.schemas.agent import (
    AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
    AGENT_PLAN_SCHEMA_VERSION,
    AgentIntent,
    AgentPlanCandidateReason,
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


def _context(role: AgentRole) -> ToolExecutionContext:
    return ToolExecutionContext(
        request_id="REQ-CANDIDATE-1",
        principal_ref="principal:candidate-test",
        role=role,
    )


def _candidate_bytes(
    question: str,
    *,
    intent: str = "SAFETY_SUMMARY",
    tool_name: str = "get_safety_summary",
    tool_version: str = "1.0.0",
    arguments=None,
    reason_code: str = "SUMMARY_REQUEST",
    request_binding_sha256: str | None = None,
) -> bytes:
    payload = {
        "schema_version": AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
        "request_binding_sha256": (
            request_binding_sha256
            or build_agent_plan_request_binding(question)
        ),
        "proposed_intent": intent,
        "proposed_tool_name": tool_name,
        "proposed_tool_version": tool_version,
        "proposed_arguments": (
            dict(PERIOD) if arguments is None else arguments
        ),
        "reason_code": reason_code,
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def test_valid_candidate_parses_and_converts_to_agent_plan() -> None:
    question = "Give me the safety summary"
    parser = AgentPlanCandidateParser()
    validator = AgentPlanCandidateValidator(_registry())

    candidate = parser.parse(_candidate_bytes(question))
    plan = validator.validate(
        candidate,
        question=question,
        context=_context(AgentRole.SAFETY_VIEWER),
    )

    assert candidate.schema_version == AGENT_PLAN_CANDIDATE_SCHEMA_VERSION
    assert candidate.proposed_intent is AgentIntent.SAFETY_SUMMARY
    assert (
        candidate.reason_code
        is AgentPlanCandidateReason.SUMMARY_REQUEST
    )
    assert plan.schema_version == AGENT_PLAN_SCHEMA_VERSION
    assert plan.intent is AgentIntent.SAFETY_SUMMARY
    assert plan.tool_name == "get_safety_summary"
    assert plan.arguments == PERIOD


@pytest.mark.parametrize(
    "raw",
    (
        b"",
        b"{",
        b'{"schema_version":"phase8-agent-plan-candidate-v1",'
        b'"schema_version":"phase8-agent-plan-candidate-v1"}',
        b'{"schema_version":"phase8-agent-plan-candidate-v1",'
        b'"request_binding_sha256":NaN}',
        b'{"schema_version":"phase8-agent-plan-candidate-v1",'
        b'"request_binding_sha256":1e400}',
    ),
)
def test_malformed_json_is_rejected_without_repair(raw: bytes) -> None:
    with pytest.raises(AgentPlanCandidateError) as error:
        AgentPlanCandidateParser().parse(raw)

    assert error.value.code == "INVALID_CANDIDATE"


def test_unknown_and_extra_fields_are_rejected() -> None:
    question = "Give me the safety summary"
    payload = json.loads(_candidate_bytes(question))
    payload["reasoning"] = "untrusted chain of thought"

    with pytest.raises(AgentPlanCandidateError) as error:
        AgentPlanCandidateParser().parse(
            json.dumps(payload).encode("utf-8")
        )

    assert error.value.code == "INVALID_CANDIDATE"


def test_unknown_tool_is_rejected_before_execution() -> None:
    question = "Give me the safety summary"
    candidate = AgentPlanCandidateParser().parse(
        _candidate_bytes(
            question,
            tool_name="get_unknown_tool",
        )
    )

    with pytest.raises(AgentPlanCandidateError) as error:
        AgentPlanCandidateValidator(_registry()).validate(
            candidate,
            question=question,
            context=_context(AgentRole.SAFETY_VIEWER),
        )

    assert error.value.code == "TOOL_NOT_FOUND"


@pytest.mark.parametrize(
    "tool_name",
    ("delete_events", "execute_shell", "read_filesystem", "run_sql"),
)
def test_forbidden_tool_capabilities_are_rejected(tool_name: str) -> None:
    question = "Give me the safety summary"
    candidate = AgentPlanCandidateParser().parse(
        _candidate_bytes(question, tool_name=tool_name)
    )

    with pytest.raises(AgentPlanCandidateError) as error:
        AgentPlanCandidateValidator(_registry()).validate(
            candidate,
            question=question,
            context=_context(AgentRole.SAFETY_VIEWER),
        )

    assert error.value.code == "FORBIDDEN_CAPABILITY"


@pytest.mark.parametrize(
    "arguments",
    (
        {"limit": 101},
        {"start_at": PERIOD["start_at"]},
        {**PERIOD, "sql": "DELETE FROM events"},
        {**PERIOD, "command": "powershell Get-ChildItem"},
        {**PERIOD, "event_id": "/etc/passwd"},
        {**PERIOD, "mutation": "delete_event"},
    ),
)
def test_invalid_and_forbidden_arguments_are_rejected(arguments) -> None:
    question = "Give me the safety summary"
    candidate = AgentPlanCandidateParser().parse(
        _candidate_bytes(question, arguments=arguments)
    )

    with pytest.raises(AgentPlanCandidateError) as error:
        AgentPlanCandidateValidator(_registry()).validate(
            candidate,
            question=question,
            context=_context(AgentRole.SAFETY_VIEWER),
        )

    assert error.value.code in {
        "INVALID_ARGUMENTS",
        "FORBIDDEN_CAPABILITY",
    }


def test_unknown_intent_is_rejected() -> None:
    question = "How is the weather?"
    candidate = AgentPlanCandidateParser().parse(
        _candidate_bytes(
            question,
            intent="UNKNOWN",
            reason_code="SUMMARY_REQUEST",
        )
    )

    with pytest.raises(AgentPlanCandidateError) as error:
        AgentPlanCandidateValidator(_registry()).validate(
            candidate,
            question=question,
            context=_context(AgentRole.SAFETY_VIEWER),
        )

    assert error.value.code == "UNKNOWN_INTENT"


def test_deterministic_intent_conflict_is_rejected() -> None:
    question = "Give me the safety summary"
    candidate = AgentPlanCandidateParser().parse(
        _candidate_bytes(
            question,
            intent="EVENT_STATISTICS",
            tool_name="get_event_statistics",
            reason_code="STATISTICS_REQUEST",
        )
    )

    with pytest.raises(AgentPlanCandidateError) as error:
        AgentPlanCandidateValidator(_registry()).validate(
            candidate,
            question=question,
            context=_context(AgentRole.SAFETY_VIEWER),
        )

    assert error.value.code == "INTENT_CONFLICT"


def test_request_binding_and_permission_are_enforced() -> None:
    question = "Show event details for EVT-CANDIDATE-1"
    parser = AgentPlanCandidateParser()
    validator = AgentPlanCandidateValidator(_registry())

    wrong_binding = parser.parse(
        _candidate_bytes(
            question,
            intent="EVENT_DETAIL",
            tool_name="get_event_details",
            arguments={"event_id": "EVT-CANDIDATE-1"},
            reason_code="EVENT_DETAIL_REQUEST",
            request_binding_sha256="0" * 64,
        )
    )
    with pytest.raises(AgentPlanCandidateError) as binding_error:
        validator.validate(
            wrong_binding,
            question=question,
            context=_context(AgentRole.EVENT_VIEWER),
        )
    assert binding_error.value.code == "INVALID_REQUEST_BINDING"

    candidate = parser.parse(
        _candidate_bytes(
            question,
            intent="EVENT_DETAIL",
            tool_name="get_event_details",
            arguments={"event_id": "EVT-CANDIDATE-1"},
            reason_code="EVENT_DETAIL_REQUEST",
        )
    )
    with pytest.raises(AgentPlanCandidateError) as permission_error:
        validator.validate(
            candidate,
            question=question,
            context=_context(AgentRole.SAFETY_VIEWER),
        )
    assert permission_error.value.code == "UNAUTHORIZED"


def test_validator_is_deterministic_and_never_executes_a_tool(
    monkeypatch,
) -> None:
    question = "Show event statistics for this period"
    registry = _registry()
    validator = AgentPlanCandidateValidator(registry)
    candidate = AgentPlanCandidateParser().parse(
        _candidate_bytes(
            question,
            intent="EVENT_STATISTICS",
            tool_name="get_event_statistics",
            reason_code="STATISTICS_REQUEST",
        )
    )

    def fail_execute(*args, **kwargs):
        raise AssertionError("candidate validation must not execute tools")

    monkeypatch.setattr(registry, "execute", fail_execute)
    first = validator.validate(
        candidate,
        question=question,
        context=_context(AgentRole.SAFETY_VIEWER),
    )
    second = validator.validate(
        candidate,
        question=question,
        context=_context(AgentRole.SAFETY_VIEWER),
    )

    assert first.to_dict() == second.to_dict()
    assert first.tool_name == "get_event_statistics"
    assert first.question_sha256 == second.question_sha256


def test_candidate_module_has_no_network_or_system_execution_dependency() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "core"
        / "agent"
        / "candidate.py"
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
        "os",
        "pathlib",
        "requests",
        "shutil",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    assert not {
        item
        for item in imported
        if any(item == name or item.startswith(f"{name}.") for name in forbidden)
    }
    assert "registry.execute" not in source
