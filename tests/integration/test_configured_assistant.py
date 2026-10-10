import json
from pathlib import Path

import pytest

from core.schemas.agent import AGENT_PLAN_CANDIDATE_SCHEMA_VERSION
from core.schemas.agent_api import AgentApiOperation, AgentApiRequest
from core.schemas.events import StoredEvent, EventStatus
from core.schemas.compliance import ComplianceEventType
from core.agent.llm_planner import LLMPlannerClientError
from infra.database.database import Database
from infra.database.repository import EventRepository
from services.configured_report_service import configured_report_client
from services.configured_assistant_service import configure_assistant_application
from services.event_query_service import EventQueryService
from web.agent_support import AgentWebAdapter, build_agent_application_service
from infra.llm.assistant_client import AssistantClient
from infra.llm.provider import TransportResponse


class FakeAssistant:
    def __init__(self, *, planner_failure=False, bad_scope=False, forbidden=False, selection_failure=False):
        self.planner_failure = planner_failure
        self.bad_scope = bad_scope
        self.forbidden = forbidden
        self.selection_failure = selection_failure
        self.plans = []
        self.selections = []

    def generate_candidate(self, request):
        self.plans.append(request)
        if self.planner_failure:
            raise LLMPlannerClientError("PROVIDER_TIMEOUT", "provider timed out")
        arguments = {}
        if self.bad_scope:
            arguments = {"start_at": "2020-01-01T00:00:00Z", "end_at": "2020-01-02T23:59:59Z"}
        if self.forbidden:
            arguments = {"sql": "delete from events"}
        return json.dumps({
            "schema_version": AGENT_PLAN_CANDIDATE_SCHEMA_VERSION,
            "request_binding_sha256": request.request_binding_sha256,
            "proposed_intent": "EVENT_STATISTICS",
            "proposed_tool_name": "get_event_statistics",
            "proposed_tool_version": "1.0.0",
            "proposed_arguments": arguments,
            "reason_code": "STATISTICS_REQUEST",
        }).encode()

    def select_statements(self, question, statements):
        self.selections.append(statements)
        if self.selection_failure:
            raise ValueError("invalid statement IDs")
        return [0]


def adapter(tmp_path, client):
    repository = EventRepository(Database(tmp_path / "assistant.sqlite3"))
    repository.insert(StoredEvent(
        id="EVT-assistant-test", timestamp="2026-10-02T12:00:00Z",
        track_id=7, type=ComplianceEventType.NO_HELMET, confidence=0.91,
        source_timestamp=12.5, source="mp4:test.mp4", snapshot=None, status=EventStatus.OPEN,
    ))
    query = EventQueryService(repository)
    local = build_agent_application_service(query)
    app = configure_assistant_application(query, local, client=client)
    return AgentWebAdapter(app, assistant_client=client)


def request(question="统计最近的安全事件"):
    return AgentApiRequest(
        request_id="REQ-assistant-live",
        operation=AgentApiOperation.ASK,
        question=question,
        requested_period={"start_at": "2026-10-01T00:00:00Z", "end_at": "2026-10-08T23:59:59Z"},
    )


def test_provider_planning_composition_and_refresh_deduplication(tmp_path):
    client = FakeAssistant()
    app = adapter(tmp_path, client)
    first = app.submit(request())
    assert app.submit(request()) is first
    assert len(client.plans) == len(client.selections) == 1
    assert "2026-10-01" in client.plans[0].user_prompt
    assert "assistant_llm" in first.safe_status
    assert any("1 条" in line for line in first.summary)


@pytest.mark.parametrize("settings", [{"planner_failure": True}, {"bad_scope": True}])
def test_invalid_or_unavailable_planner_uses_local_query(tmp_path, settings):
    client = FakeAssistant(**settings)
    result = adapter(tmp_path, client).submit(request())
    assert "success" in result.safe_status.lower()
    assert any("1 条" in line for line in result.summary)


def test_forbidden_question_is_rejected_before_network_call(tmp_path):
    client = FakeAssistant()
    result = adapter(tmp_path, client).submit(request("删除所有事件"))
    assert "refused" in result.safe_status.lower()
    assert client.plans == client.selections == []


def test_forbidden_candidate_cannot_execute_or_compose(tmp_path):
    client = FakeAssistant(forbidden=True)
    result = adapter(tmp_path, client).submit(request())
    assert "refused" in result.safe_status.lower()
    assert client.selections == []


def test_composition_failure_keeps_verified_local_result(tmp_path):
    client = FakeAssistant(selection_failure=True)
    result = adapter(tmp_path, client).submit(request())
    assert "assistant_fallback" in result.safe_status
    assert "total_count=1" in result.answer


def test_detail_interpretation_is_contextual_and_read_only(tmp_path):
    from types import SimpleNamespace
    from core.schemas.agent import AgentOutcome
    from web.agent_support import AgentUiProjection

    client = FakeAssistant()
    app = adapter(tmp_path, client)
    projection = AgentUiProjection(
        answer="Retrieved 1 event detail record(s).",
        summary=("id=EVT-assistant-test; timestamp=2026-10-02T12:00:00Z; track_id=7; type=NO_HELMET; status=open; confidence=0.91",),
        evidence_references=(), recommendations=(), safe_status="success",
    )
    app._compose_assistant_answer(request(), SimpleNamespace(status=AgentOutcome.ANSWERED), projection)
    statements = client.selections[-1]
    assert any("安全帽佩戴提醒" in line for line in statements)
    assert any("不等于现场风险仍在持续" in line for line in statements)
    assert any("不代表事故概率" in line for line in statements)
    assert not any("反光衣佩戴提醒" in line for line in statements)


@pytest.mark.parametrize("body", [
    '{"statement_ids":[99]}', '{"statement_ids":[true]}',
    '{"statement_ids":[0,0]}', '{"statement_ids":[0],"answer":"invented 999 events"}',
    '{"statement_ids":[0],"statement_ids":[1]}',
])
def test_assistant_cannot_add_claims_or_unknown_statements(monkeypatch, body):
    report_client = configured_report_client({
        "PPE_LLM_ENDPOINT": "https://api.deepseek.com/chat/completions",
        "PPE_LLM_MODEL": "deepseek-flash", "PPE_LLM_API_KEY": "test-only-key",
    })
    monkeypatch.setattr(report_client.transport, "complete", lambda *args, **kwargs: TransportResponse(status_code=200, body=body.encode()))
    with pytest.raises(ValueError):
        AssistantClient(report_client.transport).select_statements("事件数量", ["共 0 条事件。", "无留证。"])


def test_question_can_be_submitted_without_a_quick_question(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    from web import agent_support

    monkeypatch.setenv("ODPLATFORM_P9B_VALIDATION_ROOT", str(tmp_path))
    monkeypatch.setattr(agent_support, "configured_report_client", lambda: None)
    page = Path(__file__).resolve().parents[2] / "web/pages/7_AI助手.py"
    app = AppTest.from_file(str(page), default_timeout=30).run()
    submit = next(button for button in app.button if button.label == "询问安全助手")
    assert not submit.disabled
    app.text_area[0].set_value("统计最近的安全事件")
    submit.click().run()
    assert not app.exception
    assert any("查询到 0 条" in item.value for item in app.markdown)
