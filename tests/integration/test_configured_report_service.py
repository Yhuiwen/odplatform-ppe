from dataclasses import replace

import pytest

from core.schemas.agent_api import AgentApiOperation, AgentApiRequest, ProviderStatus
from core.schemas.safety_report import GenerationMode, GroundingStatus, ReportGeneration
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.llm.fallback import TemplateFallback
from infra.llm.provider import ProviderCandidate, ProviderError, ProviderErrorCode
from services.configured_report_service import configured_report_client, configure_report_application
from services.event_query_service import EventQueryService
from web.agent_support import build_agent_application_service


def _request(operation, question="Generate a safety report"):
    return AgentApiRequest(
        request_id="REQ-configured-report",
        operation=operation,
        question=question,
        requested_period={"start_at": "2026-10-01T00:00:00Z", "end_at": "2026-10-08T23:59:59Z"},
    )


def test_missing_configuration_keeps_local_application(tmp_path):
    query = EventQueryService(EventRepository(Database(tmp_path / "events.sqlite3")))
    local = build_agent_application_service(query)
    assert configured_report_client({}) is None
    assert configure_report_application(query, local) is local


@pytest.mark.parametrize("failure", [False, True])
def test_only_explicit_report_operation_invokes_provider(tmp_path, monkeypatch, failure):
    query = EventQueryService(EventRepository(Database(tmp_path / "events.sqlite3")))
    client = configured_report_client({
        "PPE_LLM_ENDPOINT": "https://api.deepseek.com/chat/completions",
        "PPE_LLM_MODEL": "deepseek-flash",
        "PPE_LLM_API_KEY": "test-only-key",
    })
    assert client.transport.thinking_enabled is False
    calls = []

    def generate(context):
        calls.append(context)
        if failure:
            raise ProviderError(code=ProviderErrorCode.PROVIDER_TIMEOUT, message="provider request timed out")
        report = replace(
            TemplateFallback().generate(context),
            generation=ReportGeneration(mode=GenerationMode.LLM, degraded=False, provider_ref="openai-compatible", failure_code=None),
            grounding_status=GroundingStatus.UNVALIDATED,
        )
        return ProviderCandidate(report=report, request=client.request_builder.build(context))

    monkeypatch.setattr(client, "generate_candidate", generate)
    application = configure_report_application(query, build_agent_application_service(query), client=client)
    # A question that requests a report cannot acquire the internal provider identity.
    application.execute(_request(AgentApiOperation.ASK, "Generate a safety report"))
    assert calls == []
    response = application.execute(_request(AgentApiOperation.GENERATE_REPORT))
    assert len(calls) == 1
    assert response.report is not None
    assert response.provider_status is (ProviderStatus.TEMPLATE_FALLBACK if failure else ProviderStatus.LLM)
    assert response.degraded is failure
    assert response.report["grounding_status"] == "valid"
