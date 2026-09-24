from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.agent.planner import DeterministicAgentPlanner
from core.agent.tool_registry import STATIC_TOOL_DESCRIPTORS, ToolRegistry
from core.schemas.agent import (
    AGENT_AUDIT_VERSION,
    AGENT_TOOL_AUDIT_VERSION,
    AgentAuditStatus,
    AgentIntent,
    AgentRole,
    AgentTool,
    AuditEvent,
    ToolError,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
)
from infra.storage.agent_audit_store import (
    AgentAuditStoreError,
    InMemoryAgentAuditStore,
)
from services.agent_audit_service import (
    AgentAuditError,
    AgentAuditService,
)

FIXED_TIMESTAMP = "2026-09-24T14:00:00Z"


def _clock() -> datetime:
    return datetime(2026, 9, 24, 14, 0, tzinfo=timezone.utc)


def _context(role: AgentRole = AgentRole.SYSTEM) -> ToolExecutionContext:
    return ToolExecutionContext(
        request_id="REQ-AUDIT-1",
        principal_ref="principal:audit-test",
        role=role,
    )


def _service() -> AgentAuditService:
    return AgentAuditService(clock=_clock)


def _registry() -> ToolRegistry:
    def handler(tool_name: str):
        def handle(arguments, context):
            return ToolResult(
                tool_name=tool_name,
                tool_version="1.0.0",
                status=ToolExecutionStatus.SUCCESS,
                data={},
            )

        return handle

    return ToolRegistry(
        tuple(
            AgentTool(descriptor, handler(descriptor.tool_name))
            for descriptor in STATIC_TOOL_DESCRIPTORS
        )
    )


def test_append_only_store_keeps_append_order_and_immutable_snapshot() -> None:
    service = _service()
    first = service.record_event(
        request_id="REQ-AUDIT-1",
        principal_ref="principal:audit-test",
        role_ref=AgentRole.SYSTEM,
        intent=AgentIntent.SAFETY_SUMMARY,
        plan_id="PLAN-AUDIT-1",
        tools_requested=("get_safety_summary",),
        execution_status=AgentAuditStatus.PLANNED,
    )
    snapshot = service.events()
    second = service.record_event(
        request_id="REQ-AUDIT-2",
        principal_ref="principal:audit-test",
        role_ref=AgentRole.SYSTEM,
        intent=AgentIntent.EVENT_STATISTICS,
        plan_id="PLAN-AUDIT-2",
        tools_requested=("get_event_statistics",),
        execution_status=AgentAuditStatus.SUCCESS,
    )

    assert snapshot == (first,)
    assert service.events() == (first, second)
    assert isinstance(service.store, InMemoryAgentAuditStore)
    assert not hasattr(service.store, "update")
    assert not hasattr(service.store, "delete")
    assert not hasattr(service.store, "clear")


def test_audit_serialization_is_deterministic_and_schema_versioned() -> None:
    first = _service().record_event(
        request_id="REQ-AUDIT-1",
        principal_ref="principal:audit-test",
        role_ref=AgentRole.SYSTEM,
        intent=AgentIntent.SAFETY_REPORT,
        plan_id="PLAN-AUDIT-3",
        tools_requested=("generate_safety_report",),
        execution_status=AgentAuditStatus.SUCCESS,
        metadata={"row_count": 4, "fallback_used": True},
    )
    second = _service().record_event(
        request_id="REQ-AUDIT-1",
        principal_ref="principal:audit-test",
        role_ref=AgentRole.SYSTEM,
        intent=AgentIntent.SAFETY_REPORT,
        plan_id="PLAN-AUDIT-3",
        tools_requested=("generate_safety_report",),
        execution_status=AgentAuditStatus.SUCCESS,
        metadata={"row_count": 4, "fallback_used": True},
    )

    assert first.to_json() == second.to_json()
    payload = json.loads(first.to_json())
    assert payload["schema_version"] == AGENT_AUDIT_VERSION
    assert AGENT_AUDIT_VERSION != AGENT_TOOL_AUDIT_VERSION
    assert payload["execution_status"] == "SUCCESS"
    assert payload["safe_metadata"] == {
        "fallback_used": True,
        "row_count": 4,
    }


def test_audit_privacy_filtering_drops_secrets_payloads_and_paths() -> None:
    service = _service()
    event = service.record_event(
        request_id="REQ-AUDIT-1",
        principal_ref="principal:audit-test",
        role_ref=AgentRole.SYSTEM,
        intent=AgentIntent.SAFETY_SUMMARY,
        plan_id="PLAN-AUDIT-4",
        tools_requested=("get_safety_summary",),
        execution_status=AgentAuditStatus.PLANNED,
        metadata={
            "duration_ms": 12.5,
            "row_count": 2,
            "tool_version": "1.0.0",
            "api_key": "sk-secret-value",
            "authorization": "Bearer secret-token",
            "provider_output": "raw provider payload",
            "database_path": "C:/private/events.sqlite3",
            "prompt": "raw user prompt",
            "policy_version": "C:/private/policy",
            "registry_version": "C:/private/registry",
            "report_generation_status": "C:/private/report",
        },
    )

    assert dict(event.safe_metadata) == {
        "duration_ms": 12.5,
        "row_count": 2,
        "tool_version": "1.0.0",
    }
    serialized = event.to_json()
    for forbidden in (
        "sk-secret-value",
        "secret-token",
        "raw provider payload",
        "C:/private/events.sqlite3",
        "raw user prompt",
    ):
        assert forbidden not in serialized


def test_audit_schema_rejects_arbitrary_metadata_fields() -> None:
    with pytest.raises(ValueError):
        AuditEvent(
            audit_id="AUD-TEST",
            request_id="REQ-AUDIT-1",
            timestamp=FIXED_TIMESTAMP,
            principal_ref="principal:audit-test",
            role_ref=AgentRole.SYSTEM,
            intent=AgentIntent.SAFETY_SUMMARY,
            plan_id="PLAN-AUDIT-5",
            tools_requested=("get_safety_summary",),
            execution_status=AgentAuditStatus.PLANNED,
            safe_metadata={"api_key": "sk-secret-value"},
        )


def test_success_and_failure_tool_results_are_recorded_without_payload() -> None:
    service = _service()
    context = _context()
    success = service.record_tool_result(
        ToolResult(
            tool_name="get_event_statistics",
            tool_version="1.0.0",
            status=ToolExecutionStatus.SUCCESS,
            data={"secret_payload": "must not enter audit"},
            row_count=3,
            duration_ms=8.5,
        ),
        context,
        intent=AgentIntent.EVENT_STATISTICS,
        plan_id="PLAN-AUDIT-SUCCESS",
    )
    failure = service.record_tool_result(
        ToolResult(
            tool_name="get_event_details",
            tool_version="1.0.0",
            status=ToolExecutionStatus.ERROR,
            data={"provider_output": "must not enter audit"},
            safe_error=ToolError(
                code="TOOL_ERROR",
                message="tool execution failed safely",
            ),
        ),
        context,
        intent=AgentIntent.EVENT_DETAIL,
        plan_id="PLAN-AUDIT-FAILURE",
    )

    assert success.execution_status is AgentAuditStatus.SUCCESS
    assert success.failure_status is None
    assert failure.execution_status is AgentAuditStatus.FAILURE
    assert failure.failure_status == "TOOL_ERROR"
    assert "must not enter audit" not in success.to_json()
    assert "must not enter audit" not in failure.to_json()


def test_unknown_tool_attempt_records_bounded_failure() -> None:
    service = _service()
    event = service.record_unknown_tool(
        request_id="REQ-AUDIT-UNKNOWN",
        principal_ref="principal:audit-test",
        role_ref=AgentRole.SYSTEM,
        intent=AgentIntent.FORBIDDEN_REQUEST,
        tool_name="drop_events",
    )

    assert event.execution_status is AgentAuditStatus.UNKNOWN_TOOL
    assert event.failure_status == "TOOL_NOT_FOUND"
    assert event.tools_requested == ("drop_events",)


def test_planner_integration_records_plan_identity_without_raw_question() -> None:
    planner = DeterministicAgentPlanner(_registry())
    context = _context(AgentRole.EVENT_VIEWER)
    plan = planner.plan(
        "Show event details for EVT-AGENT-1",
        context=context,
    )
    event = _service().record_plan(plan, context)
    serialized = event.to_json()

    assert event.intent is AgentIntent.EVENT_DETAIL
    assert event.tools_requested == ("get_event_details",)
    assert event.plan_id.startswith("PLAN-")
    assert event.question_sha256 == plan.question_sha256
    assert "Show event details" not in serialized
    assert "EVT-AGENT-1" not in serialized
    assert "arguments" not in json.loads(serialized)


def test_audit_modules_have_no_database_filesystem_or_network_capability() -> None:
    project_root = Path(__file__).resolve().parents[1]
    paths = (
        project_root / "infra" / "storage" / "agent_audit_store.py",
        project_root / "services" / "agent_audit_service.py",
    )
    forbidden = {
        "ctypes",
        "os",
        "pathlib",
        "shutil",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
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


def test_audit_store_rejects_non_event_values() -> None:
    store = InMemoryAgentAuditStore()

    with pytest.raises(AgentAuditStoreError):
        store.append("not-an-event")


def test_invalid_audit_inputs_fail_closed() -> None:
    service = _service()

    with pytest.raises(AgentAuditError):
        service.record_event(
            request_id="REQ-AUDIT-INVALID",
            principal_ref="principal:audit-test",
            role_ref=AgentRole.SYSTEM,
            intent=AgentIntent.SAFETY_SUMMARY,
            plan_id="PLAN-AUDIT-INVALID",
            tools_requested=("get_safety_summary",),
            execution_status=AgentAuditStatus.FAILURE,
        )

    with pytest.raises(AgentAuditError):
        service.record_event(
            request_id="REQ-AUDIT-INVALID",
            principal_ref="principal:audit-test",
            role_ref=AgentRole.SYSTEM,
            intent=AgentIntent.SAFETY_SUMMARY,
            plan_id="PLAN-AUDIT-INVALID",
            tools_requested=("get_safety_summary",),
            execution_status=AgentAuditStatus.SUCCESS,
            failure_status="TOOL_ERROR",
        )
