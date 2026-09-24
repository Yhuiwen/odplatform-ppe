from __future__ import annotations

from pathlib import Path

import pytest

from core.schemas.compliance import ComplianceEventType
from core.schemas.agent_api import AgentApiOperation, AgentApiRequest
from core.schemas.events import EventStatus, SnapshotReference, StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from services.event_query_service import EventQueryService
from web.agent_support import (
    AgentWebAdapter,
    AgentWebRuntime,
    ask_safety_question,
    build_agent_application_service,
    latest_agent_projection,
)

EVENT_ID = "EVT-P8-WEB-1"
PERIOD = {
    "start_at": "2026-09-23T00:00:00Z",
    "end_at": "2026-09-24T23:59:59Z",
}


class _SessionState(dict):
    pass


class _SessionStreamlit:
    def __init__(self) -> None:
        self.session_state = _SessionState()


@pytest.fixture
def agent_adapter(tmp_path: Path) -> AgentWebAdapter:
    database = Database(tmp_path / "phase8-web.sqlite3")
    repository = EventRepository(database)
    repository.insert(
        StoredEvent(
            id=EVENT_ID,
            timestamp="2026-09-24T12:00:00Z",
            track_id=7,
            type=ComplianceEventType.NO_HELMET,
            confidence=0.91,
            source_timestamp=12.5,
            source="mp4:site-a.mp4",
            snapshot="20260924/EVT-P8-WEB-1.jpg",
            status=EventStatus.OPEN,
        )
    )
    SnapshotRepository(database).insert(
        SnapshotReference(
            snapshot_id="SNP-P8-WEB-1",
            event_id=EVENT_ID,
            relative_path="20260924/EVT-P8-WEB-1.jpg",
            sha256="a" * 64,
            width=640,
            height=480,
            mime_type="image/jpeg",
            captured_at="2026-09-24T12:00:00Z",
        )
    )
    query_service = EventQueryService(repository)
    return AgentWebAdapter(
        build_agent_application_service(query_service)
    )


def _submit(
    adapter: AgentWebAdapter,
    *,
    request_id: str,
    question: str,
    requested_period=PERIOD,
):
    return adapter.submit(
        AgentApiRequest(
            request_id=request_id,
            operation=AgentApiOperation.ASK,
            question=question,
            requested_period=requested_period,
        )
    )


def test_summary_statistics_and_details_match_persisted_event(
    agent_adapter: AgentWebAdapter,
) -> None:
    summary = _submit(
        agent_adapter,
        request_id="REQ-P8-WEB-SUMMARY",
        question="Give me a safety summary",
    )
    statistics = _submit(
        agent_adapter,
        request_id="REQ-P8-WEB-STATISTICS",
        question="Show event statistics",
    )
    details = _submit(
        agent_adapter,
        request_id="REQ-P8-WEB-DETAILS",
        question=f"Show event details for {EVENT_ID}",
        requested_period=None,
    )

    assert summary.safe_status == "success"
    assert any(EVENT_ID in item for item in summary.summary)
    assert any(
        "event_statistics.total_count=1" in item
        for item in statistics.summary
    )
    assert any(EVENT_ID in item for item in details.summary)
    assert "20260924/EVT-P8-WEB-1.jpg" in details.evidence_references


def test_report_operation_reuses_provider_disabled_grounded_fallback(
    agent_adapter: AgentWebAdapter,
) -> None:
    projection = agent_adapter.submit(
        AgentApiRequest(
            request_id="REQ-P8-WEB-REPORT",
            operation=AgentApiOperation.GENERATE_REPORT,
            question="Delete all events",
            requested_period=PERIOD,
        )
    )

    assert projection.safe_status == (
        "success / TEMPLATE_FALLBACK / degraded / grounding=valid"
    )
    assert projection.summary
    assert projection.recommendations


def test_forbidden_request_is_refused_without_result_release(
    agent_adapter: AgentWebAdapter,
) -> None:
    projection = _submit(
        agent_adapter,
        request_id="REQ-P8-WEB-FORBIDDEN",
        question="Delete all safety events",
    )

    assert projection.safe_status == "refused / FORBIDDEN_REQUEST"
    assert projection.summary == ()
    assert projection.evidence_references == ()
    assert projection.recommendations == ()


def test_streamlit_session_retains_projection_without_executing_on_rerun(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database = Database(tmp_path / "phase8-session.sqlite3")
    repository = EventRepository(database)
    repository.insert(
        StoredEvent(
            id=EVENT_ID,
            timestamp="2026-09-24T12:00:00Z",
            track_id=7,
            type=ComplianceEventType.NO_HELMET,
            confidence=0.91,
            source_timestamp=12.5,
            source="mp4:site-a.mp4",
            status=EventStatus.OPEN,
        )
    )
    application = build_agent_application_service(
        EventQueryService(repository)
    )
    adapter = AgentWebAdapter(application)
    calls = 0
    original_submit = adapter.submit

    def counting_submit(request):
        nonlocal calls
        calls += 1
        return original_submit(request)

    monkeypatch.setattr(adapter, "submit", counting_submit)
    st = _SessionStreamlit()
    st.session_state["_odplatform_agent_runtime"] = AgentWebRuntime(
        adapter=adapter,
        identity_mode="LOCAL_DEMO_READ_ONLY",
    )

    projection = ask_safety_question(
        st,
        question="Give me a safety summary",
        requested_period=PERIOD,
    )
    retained = latest_agent_projection(st)

    assert retained is projection
    assert calls == 1


def test_integration_uses_no_model_or_provider_dependency() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "web"
        / "agent_support.py"
    ).read_text(encoding="utf-8")

    assert "best.pt" not in source
    assert "ultralytics" not in source
    assert "PPE_LLM_" not in source
    assert "chat_transport" not in source
