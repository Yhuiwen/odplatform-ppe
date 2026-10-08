from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.agent.permissions import ToolPermissionPolicy
from core.schemas.agent import (
    AgentCapability,
    AgentOutcome,
    ToolError,
)
from core.schemas.agent_api import (
    AgentApiOperation,
    AgentApiRequest,
    AgentApiResponse,
    AgentPresentationState,
    ProviderStatus,
)
from infra.database.database import Database
from infra.database.repository import EventRepository
from services.event_query_service import EventQueryService
from utils.paths import PROJECT_ROOT
from web.agent_support import (
    AgentWebAdapter,
    LocalDemoIdentityProvider,
    build_agent_application_service,
    project_agent_response,
    render_agent_projection,
)

PERIOD = {
    "start_at": "2026-09-01T00:00:00Z",
    "end_at": "2026-09-24T23:59:59Z",
}


class _RecordingStreamlit:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def write(self, value: str) -> None:
        self.calls.append(("write", value))

    def caption(self, value: str) -> None:
        self.calls.append(("caption", value))

    def subheader(self, value: str) -> None:
        self.calls.append(("subheader", value))


def _answered_response() -> AgentApiResponse:
    return AgentApiResponse(
        request_id="REQ-WEB-SUCCESS",
        audit_id="AUD-WEB-SUCCESS",
        status=AgentOutcome.ANSWERED,
        presentation_state=AgentPresentationState.SUCCESS,
        answer="Safety summary is available.",
        facts=(
            {
                "event_id": "EVT-WEB-1",
                "timestamp": "2026-09-24T12:00:00Z",
                "track_id": 7,
                "type": "NO_HELMET",
                "confidence": 0.91,
            },
        ),
        metrics=(
            {"metric_id": "event_statistics.total_count", "value": 1},
        ),
        evidence_refs=("20260924/EVT-WEB-1.jpg",),
        report={
            "generation": {
                "mode": "TEMPLATE_FALLBACK",
                "degraded": True,
            },
            "grounding_status": "valid",
            "executive_summary": (
                {"statement": "One event was observed."},
            ),
            "key_findings": (),
            "risk_observations": (
                {"statement": "Helmet compliance requires review."},
            ),
            "recommendations": (
                {
                    "action": "Reinforce helmet checks.",
                    "priority": "high",
                },
            ),
            "evidence_references": (
                {
                    "evidence_ref": "EVID:EVT-WEB-1",
                    "snapshot_ref": "20260924/EVT-WEB-1.jpg",
                },
            ),
        },
        provider_status=ProviderStatus.TEMPLATE_FALLBACK,
        degraded=True,
    )


def _request(
    question: str,
    *,
    request_id: str = "WEB-CACHE-1",
) -> AgentApiRequest:
    return AgentApiRequest(
        request_id=request_id,
        operation=AgentApiOperation.ASK,
        question=question,
        requested_period=PERIOD,
    )


def test_projection_exposes_exactly_five_ui_safe_fields() -> None:
    projection = project_agent_response(_answered_response())

    assert projection.answer == "Safety summary is available."
    assert projection.summary == (
        "One event was observed.",
        "Helmet compliance requires review.",
    )
    assert projection.evidence_references == (
        "20260924/EVT-WEB-1.jpg",
        "EVID:EVT-WEB-1",
    )
    assert projection.recommendations == (
        "[HIGH] Reinforce helmet checks.",
    )
    assert projection.safe_status == (
        "success / TEMPLATE_FALLBACK / degraded / grounding=valid"
    )
    assert set(projection.to_dict()) == {
        "answer",
        "summary",
        "evidence_references",
        "recommendations",
        "safe_status",
    }
    assert json.loads(projection.to_json()) == projection.to_dict()


def test_refused_and_failed_projection_release_no_result_data() -> None:
    refused = AgentApiResponse(
        request_id="REQ-WEB-REFUSED",
        audit_id="AUD-WEB-REFUSED",
        status=AgentOutcome.REFUSED,
        presentation_state=AgentPresentationState.REFUSED,
        answer="The request was refused by the Agent policy.",
        safe_error=ToolError(
            code="FORBIDDEN_REQUEST",
            message="the request is outside the read-only scope",
        ),
    )
    failed = AgentApiResponse(
        request_id="REQ-WEB-FAILED",
        audit_id="AUD-WEB-FAILED",
        status=AgentOutcome.TOOL_ERROR,
        presentation_state=AgentPresentationState.TOOL_ERROR,
        answer="The request failed safely.",
        safe_error=ToolError(
            code="TOOL_ERROR",
            message="tool execution failed safely",
        ),
    )

    refused_projection = project_agent_response(refused)
    failed_projection = project_agent_response(failed)

    assert refused_projection.summary == ()
    assert refused_projection.evidence_references == ()
    assert refused_projection.recommendations == ()
    assert refused_projection.safe_status == "refused / FORBIDDEN_REQUEST"
    assert failed_projection.safe_status == "tool_error / TOOL_ERROR"


def test_projection_does_not_release_internal_or_path_text() -> None:
    response = AgentApiResponse(
        request_id="REQ-WEB-SAFE-TEXT",
        audit_id="AUD-WEB-SAFE-TEXT",
        status=AgentOutcome.ANSWERED,
        presentation_state=AgentPresentationState.SUCCESS,
        answer=r"C:\private\provider-trace.txt",
        facts=(
            {
                "event_id": "EVT-WEB-2",
                "source_ref": "SRC-safe",
            },
        ),
    )

    projection = project_agent_response(response)
    serialized = projection.to_json()

    assert projection.answer == "The Agent response is unavailable."
    assert "provider-trace" not in serialized
    assert "C:\\private" not in serialized
    assert "provider_output" not in serialized
    assert "sqlite" not in serialized


def test_repeated_request_identity_uses_cached_projection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database = Database(tmp_path / "agent-web.sqlite3")
    application = build_agent_application_service(
        EventQueryService(EventRepository(database))
    )
    adapter = AgentWebAdapter(application)
    calls = 0
    original_execute = application.execute

    def counting_execute(request):
        nonlocal calls
        calls += 1
        return original_execute(request)

    monkeypatch.setattr(application, "execute", counting_execute)
    request = _request("Give me a safety summary")

    first = adapter.submit(request)
    second = adapter.submit(request)

    assert first is second
    assert calls == 1
    with pytest.raises(ValueError, match="different request"):
        adapter.submit(_request("How many events were recorded?"))


def test_local_demo_identity_is_read_only() -> None:
    identity = LocalDemoIdentityProvider().resolve("REQ-WEB-IDENTITY")
    granted = ToolPermissionPolicy().capabilities_for(identity.role)

    assert identity.principal_ref == "principal:web-local-demo"
    assert identity.capabilities == frozenset()
    assert AgentCapability.PROVIDER_INVOKE not in granted
    assert granted == frozenset(
        {
            AgentCapability.SAFETY_READ,
            AgentCapability.STATISTICS_READ,
            AgentCapability.EVENTS_READ,
            AgentCapability.REPORTS_GENERATE,
        }
    )


def test_renderer_writes_only_projection_fields() -> None:
    st = _RecordingStreamlit()
    projection = project_agent_response(_answered_response())

    render_agent_projection(st, projection)

    rendered = " ".join(value for _, value in st.calls)
    assert "Safety summary is available." in rendered
    assert "当前使用确定性安全分析模式" in rendered
    assert "Reinforce helmet checks." in rendered
    assert "20260924/EVT-WEB-1.jpg" in rendered
    assert "ToolRegistry" not in rendered
    assert "provider_output" not in rendered


def test_renderer_translates_known_statistics_without_changing_projection() -> None:
    from web.agent_support import AgentUiProjection

    projection = AgentUiProjection(
        answer="Event statistics returned total_count=6.",
        summary=(
            "event_statistics.total_count=6",
            "event_statistics.by_type=NO_HELMET=4, NO_VEST=1, PPE_UNKNOWN=1",
            "event_statistics.by_status=open=6",
        ),
        evidence_references=(),
        recommendations=(),
        safe_status="success",
    )
    st = _RecordingStreamlit()
    render_agent_projection(st, projection)
    rendered = " ".join(value for _, value in st.calls)
    assert "在所选范围内查询到 6 条已确认事件" in rendered
    assert "未佩戴安全帽 4 条" in rendered
    assert "未穿反光衣 1 条" in rendered
    assert "待处理 6 条" in rendered
    assert projection.summary[1].startswith("event_statistics.by_type=")


def test_renderer_localizes_complete_fallback_report_text() -> None:
    from web.agent_support import AgentUiProjection

    projection = AgentUiProjection(
        answer="Safety report generated via TEMPLATE_FALLBACK.",
        summary=(
            "The reporting period contains 6 persisted events in the inclusive interval from 2026-09-23T00:00:00Z to 2026-10-07T23:59:59Z.",
            "The filtered event set contains 6 persisted compliance events.",
            "Recorded events of type NO_HELMET: 4.",
            "Recorded events of type NO_VEST: 1.",
            "Recorded events of type PPE_UNKNOWN: 1.",
            "The earliest persisted event timestamp in the reporting period is 2026-09-23T13:58:26Z.",
            "The latest persisted event timestamp in the reporting period is 2026-10-07T07:30:42Z.",
            "Persisted evidence references are available for 6 events and missing for 0 events.",
            "Confirmed events were grouped across 3 tracker-scoped track_id values. These track_id values are tracker-scoped and are not stable person identity.",
            "The most frequent recorded event type is NO_HELMET with 4 events. This statement is limited to observed frequency and does not establish severity, legal causation or employee identity.",
        ),
        evidence_references=("EVID:EVT-WEB-1",),
        recommendations=(
            "[HIGH] Review helmet-use procedures and the relevant recorded evidence for NO_HELMET events.",
            "[MEDIUM] Review high-visibility vest procedures and the relevant recorded evidence for NO_VEST events.",
            "[MEDIUM] Review uncertain PPE detections and their evidence before taking operational action.",
        ),
        safe_status="success / TEMPLATE_FALLBACK / degraded",
    )
    st = _RecordingStreamlit()
    render_agent_projection(st, projection)
    rendered = " ".join(value for _, value in st.calls)
    assert "安全报告已生成" in rendered
    assert "未佩戴安全帽：4 条" in rendered
    assert "未穿反光衣：1 条" in rendered
    assert "已留证" in rendered
    assert "高优先级" in rendered
    assert "轨迹 ID" in rendered
    assert "EVID:EVT-WEB-1" in rendered
    assert "The filtered event set" not in rendered
    assert "Review helmet-use" not in rendered


def test_phase8_pages_import_only_the_agent_support_facade() -> None:
    page_paths = (
        PROJECT_ROOT / "web" / "pages" / "6_AI报告.py",
        PROJECT_ROOT / "web" / "pages" / "7_AI助手.py",
    )
    allowed_modules = {
        "__future__",
        "datetime",
        "streamlit",
        "web.agent_support",
    }
    forbidden_text = (
        "sqlite3",
        "ToolRegistry",
        "AgentApplicationService",
        "AgentService",
        "LLMPlannerAdapter",
        "SafetyLLMClient",
        "provider_output",
        "candidate",
        "best.pt",
    )

    for path in page_paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert imported_modules <= allowed_modules
        assert all(item not in source for item in forbidden_text)
