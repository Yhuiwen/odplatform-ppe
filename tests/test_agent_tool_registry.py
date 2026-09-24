from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.agent.permissions import (
    ToolPermissionError,
    ToolPermissionPolicy,
)
from core.agent.tool_registry import (
    STATIC_TOOL_DESCRIPTORS,
    ToolRegistry,
    ToolRegistryError,
)
from core.schemas.agent import (
    AGENT_POLICY_VERSION,
    AGENT_TOOL_REGISTRY_VERSION,
    AgentCapability,
    AgentRole,
    AgentTool,
    AgentToolDescriptor,
    ToolEffect,
    ToolExecutionContext,
    ToolExecutionStatus,
    ToolResult,
)
from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus, StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from services.agent_tool_service import AgentToolService
from services.event_query_service import EventQueryService
from services.report_service import ReportService
from services.safety_analytics_service import SafetyAnalyticsService
from services.safety_context_builder import SafetyContextBuilder

FIXED_CLOCK = lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)


def _service(tmp_path: Path) -> AgentToolService:
    database = Database(tmp_path / "agent-events.sqlite3")
    repository = EventRepository(database)
    repository.insert(
        StoredEvent(
            id="EVT-AGENT-1",
            timestamp="2026-09-24T12:00:00Z",
            track_id=7,
            type=ComplianceEventType.NO_HELMET,
            confidence=0.91,
            source_timestamp=12.5,
            source="mp4:site-a.mp4",
            status=EventStatus.OPEN,
        )
    )
    event_query = EventQueryService(repository)
    return AgentToolService(
        event_query_service=event_query,
        safety_analytics_service=SafetyAnalyticsService(event_query),
        context_builder=SafetyContextBuilder(clock=FIXED_CLOCK),
        report_service=ReportService(),
    )


def _context(
    role: AgentRole,
    *,
    capabilities: frozenset[AgentCapability] = frozenset(),
) -> ToolExecutionContext:
    return ToolExecutionContext(
        request_id="REQ-AGENT-1",
        principal_ref="principal:test",
        role=role,
        capabilities=capabilities,
    )


def test_registered_tools_are_stable_and_exactly_allowlisted(tmp_path) -> None:
    registry = _service(tmp_path).registry

    assert registry.tool_names == (
        "get_safety_summary",
        "get_event_statistics",
        "get_event_details",
        "generate_safety_report",
    )
    assert tuple(item.tool_name for item in registry.descriptors) == (
        registry.tool_names
    )
    assert all(item.effect is ToolEffect.READ_ONLY for item in registry.descriptors)


def test_unknown_tool_is_rejected_before_handler_execution(tmp_path) -> None:
    registry = _service(tmp_path).registry

    with pytest.raises(ToolRegistryError) as error:
        registry.execute(
            "drop_events",
            {},
            _context(AgentRole.SYSTEM),
        )

    assert error.value.code == "TOOL_NOT_FOUND"


def test_dynamic_registration_and_unknown_descriptors_are_rejected(
    tmp_path,
) -> None:
    registry = _service(tmp_path).registry
    extra = AgentTool(
        AgentToolDescriptor(
            tool_name="delete_evidence",
            tool_version="1.0.0",
            description="forbidden dynamic tool",
            effect=ToolEffect.READ_ONLY,
            input_schema=("event_id",),
            output_schema=("deleted",),
            required_capabilities=(),
            timeout_seconds=1.0,
        ),
        lambda arguments, context: ToolResult(
            tool_name="delete_evidence",
            tool_version="1.0.0",
            status=ToolExecutionStatus.SUCCESS,
            data={},
        ),
    )

    assert not hasattr(registry, "register")
    with pytest.raises(ToolRegistryError) as error:
        ToolRegistry((*tuple(registry._tools.values()), extra))

    assert error.value.code == "TOOL_NOT_ALLOWED"


def test_forbidden_permission_is_rejected_by_deny_by_default_policy() -> None:
    policy = ToolPermissionPolicy()

    with pytest.raises(ToolPermissionError) as error:
        policy.authorize(
            _context(AgentRole.SYSTEM),
            ("sql:execute",),
        )

    assert error.value.code == "FORBIDDEN_CAPABILITY"
    assert AgentCapability.PROVIDER_INVOKE not in policy.capabilities_for(
        AgentRole.SAFETY_REPORTER
    )
    assert AgentCapability.PROVIDER_INVOKE in policy.capabilities_for(
        AgentRole.SYSTEM
    )


def test_unauthorized_read_returns_refused_without_running_handler(
    tmp_path,
) -> None:
    registry = _service(tmp_path).registry

    result = registry.execute(
        "get_event_details",
        {"event_id": "EVT-AGENT-1"},
        _context(AgentRole.SAFETY_VIEWER),
    )

    assert result.status is ToolExecutionStatus.REFUSED
    assert result.safe_error is not None
    assert result.safe_error.code == "UNAUTHORIZED"
    assert result.audit_metadata is not None
    assert result.audit_metadata.outcome is ToolExecutionStatus.REFUSED


def test_allowed_read_operation_uses_existing_event_query_service(
    tmp_path,
) -> None:
    registry = _service(tmp_path).registry

    result = registry.execute(
        "get_event_statistics",
        {
            "start_at": "2026-09-23T00:00:00Z",
            "end_at": "2026-09-24T23:59:59Z",
        },
        _context(AgentRole.SAFETY_VIEWER),
    )

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.row_count == 1
    assert result.data["total_count"] == 1
    assert "by_source" not in result.data
    assert len(result.data["by_source_ref"]) == 1


def test_each_frozen_tool_executes_with_its_required_capability(
    tmp_path,
) -> None:
    registry = _service(tmp_path).registry
    period = {
        "start_at": "2026-09-23T00:00:00Z",
        "end_at": "2026-09-24T23:59:59Z",
    }

    summary = registry.execute(
        "get_safety_summary",
        period,
        _context(AgentRole.SAFETY_VIEWER),
    )
    details = registry.execute(
        "get_event_details",
        {"event_id": "EVT-AGENT-1"},
        _context(AgentRole.EVENT_VIEWER),
    )
    report = registry.execute(
        "generate_safety_report",
        period,
        _context(AgentRole.SAFETY_REPORTER),
    )

    assert summary.status is ToolExecutionStatus.SUCCESS
    assert details.status is ToolExecutionStatus.SUCCESS
    assert details.data["events"][0]["id"] == "EVT-AGENT-1"
    assert report.status is ToolExecutionStatus.SUCCESS
    assert report.data["generation_path"] == "TEMPLATE_FALLBACK"
    assert report.data["degraded"] is True


def test_audit_metadata_is_deterministic_and_omits_raw_arguments(
    tmp_path,
) -> None:
    registry = _service(tmp_path).registry
    arguments = {
        "start_at": "2026-09-23T00:00:00Z",
        "end_at": "2026-09-24T23:59:59Z",
        "track_id": 7,
    }

    result = registry.execute(
        "get_event_statistics",
        arguments,
        _context(AgentRole.SAFETY_VIEWER),
    )

    assert result.audit_metadata is not None
    audit = result.audit_metadata
    assert audit.request_id == "REQ-AGENT-1"
    assert audit.tool_name == "get_event_statistics"
    assert audit.policy_version == AGENT_POLICY_VERSION
    assert audit.registry_version == AGENT_TOOL_REGISTRY_VERSION
    assert audit.outcome is ToolExecutionStatus.SUCCESS
    assert len(audit.arguments_sha256) == 64
    assert "mp4:site-a.mp4" not in str(audit.to_dict())


def test_unknown_filesystem_shell_and_mutation_arguments_are_refused(
    tmp_path,
) -> None:
    registry = _service(tmp_path).registry

    for arguments in (
        {"path": "C:/private/events.sqlite3"},
        {"command": "rm -rf artifacts"},
        {"sql": "DELETE FROM events"},
        {"mutation": "delete_event"},
    ):
        result = registry.execute(
            "get_event_statistics",
            arguments,
            _context(AgentRole.SAFETY_VIEWER),
        )
        assert result.status is ToolExecutionStatus.REFUSED
        assert result.safe_error is not None
        assert result.safe_error.code == "FORBIDDEN_ARGUMENT"


def test_tool_result_serializes_with_audit_metadata(tmp_path) -> None:
    registry = _service(tmp_path).registry
    result = registry.execute(
        "get_event_statistics",
        {
            "start_at": "2026-09-23T00:00:00Z",
            "end_at": "2026-09-24T23:59:59Z",
        },
        _context(AgentRole.SAFETY_VIEWER),
    )

    payload = result.to_dict()

    assert payload["status"] == "SUCCESS"
    assert payload["audit_metadata"]["tool_name"] == "get_event_statistics"
    assert payload["safe_error"] is None


def test_agent_registry_has_no_filesystem_shell_or_database_capability() -> None:
    project_root = Path(__file__).resolve().parents[1]
    paths = (
        project_root / "core" / "agent" / "permissions.py",
        project_root / "core" / "agent" / "tool_registry.py",
        project_root / "services" / "agent_tool_service.py",
    )
    forbidden = {
        "os",
        "pathlib",
        "shutil",
        "sqlite3",
        "subprocess",
        "ctypes",
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
            if any(item == name or item.startswith(f"{name}.") for name in forbidden)
        }


def test_static_descriptors_are_read_only_and_bounded() -> None:
    assert len(STATIC_TOOL_DESCRIPTORS) == 4
    assert all(item.effect is ToolEffect.READ_ONLY for item in STATIC_TOOL_DESCRIPTORS)
    assert all(item.max_calls_per_request == 1 for item in STATIC_TOOL_DESCRIPTORS)
    assert all(item.timeout_seconds > 0 for item in STATIC_TOOL_DESCRIPTORS)
