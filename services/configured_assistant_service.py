"""Server-owned assistant composition with request-bound read-only planning."""

import json
from dataclasses import replace
from core.schemas.agent import AgentRole
from core.schemas.agent_api import AgentApiOperation, AgentApiRequest, TrustedIdentity
from core.agent.llm_planner import LLMPlannerClientError
from infra.llm.assistant_client import AssistantClient, _strict_object
from services.agent_api_service import AgentApplicationService
from services.agent_audit_service import AgentAuditService
from services.agent_service import AgentService
from services.agent_tool_service import AgentToolService
from services.llm_planner_adapter import LLMPlannerAdapter
from services.report_service import ReportService
from services.safety_analytics_service import SafetyAnalyticsService
from services.safety_context_builder import SafetyContextBuilder

ASSISTANT_SERVICE_VERSION = 1


def configured_assistant_client(report_client):
    from infra.llm.assistant_client import AssistantClient

    return AssistantClient(report_client.transport) if report_client is not None else None


class ConfiguredAssistantApplication(AgentApplicationService):
    """Use provider planning for ASK, preserving the existing explicit report path."""

    def __init__(self, query_service, report_application, client):
        self._query_service = query_service
        self._report_application = report_application
        self._client = client

    def execute(self, request: AgentApiRequest):
        if not isinstance(request, AgentApiRequest):
            raise TypeError("request must be an AgentApiRequest")
        if request.operation is not AgentApiOperation.ASK:
            return self._report_application.execute(request)
        application = _assistant_application(
            self._query_service, _RequestBoundAssistantClient(self._client, request)
        )
        return application.execute(request)


class _RequestBoundAssistantClient:
    """Bind candidate date/filter scope to the caller's already validated selection."""

    def __init__(self, client, request):
        self.client = client
        self.request = request

    def generate_candidate(self, planner_request):
        constraints = dict(self.request.requested_period or {})
        constraints.update(dict(self.request.filters or {}))
        scoped_request = replace(planner_request, user_prompt=(
            planner_request.user_prompt + "\nAuthoritative selected date/filter scope: "
            + json.dumps(constraints, ensure_ascii=False)
            + ". Do not change these supplied values."
        ))
        raw = self.client.generate_candidate(scoped_request)
        try:
            candidate = _strict_object(raw)
            arguments = candidate.get("proposed_arguments")
            if isinstance(arguments, dict):
                for field, value in constraints.items():
                    if field in arguments and arguments[field] != value:
                        raise ValueError("candidate changed selected scope")
                    arguments[field] = value
            return json.dumps(candidate, ensure_ascii=False).encode("utf-8")
        except (ValueError, UnicodeDecodeError, TypeError):
            raise LLMPlannerClientError("INVALID_PLANNER_OUTPUT", "candidate scope or JSON is invalid") from None


class _ServerAssistantIdentity:
    def resolve(self, request_id: str) -> TrustedIdentity:
        return TrustedIdentity(
            principal_ref="principal:configured-assistant-service",
            role=AgentRole.SYSTEM,
            capabilities=frozenset(),
        )


def configure_assistant_application(query_service, report_application, *, client=None):
    if client is None:
        return report_application
    return ConfiguredAssistantApplication(query_service, report_application, client)


def _assistant_application(query_service, client):
    tools = AgentToolService(
        event_query_service=query_service,
        safety_analytics_service=SafetyAnalyticsService(query_service),
        context_builder=SafetyContextBuilder(),
        report_service=ReportService(),
        # Assistant planning is remote; queried facts still come from local tools.
        provider_client=None,
    )
    planner = LLMPlannerAdapter(
        tools.registry,
        candidate_client=client,
        audit_service=AgentAuditService(),
    )
    assistant = AgentApplicationService(AgentService(planner), _ServerAssistantIdentity())
    return assistant
