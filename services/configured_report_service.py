"""Server-owned opt-in provider composition for explicit report operations."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from core.schemas.agent import AgentRole
from core.schemas.agent_api import AgentApiOperation, AgentApiRequest, TrustedIdentity
from infra.llm.chat_transport import OpenAICompatibleChatTransport
from infra.llm.config import LLMConfigurationError, LLMProviderConfig
from infra.llm.llm_client import SafetyLLMClient
from infra.llm.request_builder import ProviderRequestBuilder
from services.agent_api_service import AgentApplicationService
from services.agent_audit_service import AgentAuditService
from services.agent_service import AgentService
from services.agent_tool_service import AgentToolService
from services.llm_planner_adapter import LLMPlannerAdapter
from services.report_service import ReportService
from services.safety_analytics_service import SafetyAnalyticsService
from services.safety_context_builder import SafetyContextBuilder

REPORT_CONFIG_VERSION = 3
LOCAL_LLM_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "llm.local.json"


def report_environment(*, include_user: bool = True) -> dict[str, str]:
    """Resolve process settings, then saved Windows user settings if absent."""
    environment = dict(os.environ)
    if os.name == "nt" and include_user:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                for name in ("PPE_LLM_ENDPOINT", "PPE_LLM_MODEL", "PPE_LLM_API_KEY"):
                    if not environment.get(name):
                        try:
                            value, _ = winreg.QueryValueEx(key, name)
                            if isinstance(value, str):
                                environment[name] = value
                        except FileNotFoundError:
                            pass
        except OSError:
            pass
    # Explicit project credentials take precedence over stale shell settings.
    try:
        local = json.loads(LOCAL_LLM_CONFIG.read_text(encoding="utf-8"))
        names = {"PPE_LLM_ENDPOINT", "PPE_LLM_MODEL", "PPE_LLM_API_KEY"}
        if isinstance(local, dict) and set(local) == names and all(
            isinstance(value, str) and value.strip() for value in local.values()
        ):
            environment.update(local)
    except (OSError, ValueError):
        pass
    return environment


def provider_configuration_fingerprint() -> str:
    """Opaque server configuration identity; never release resolved values."""
    import hashlib
    settings = report_environment()
    selected = {name: settings.get(name, "") for name in (
        "PPE_LLM_ENDPOINT", "PPE_LLM_MODEL", "PPE_LLM_API_KEY"
    )}
    return hashlib.sha256(json.dumps(selected, sort_keys=True).encode()).hexdigest()


def configured_report_client(environ: Mapping[str, str] | None = None):
    """Load credentials without starting a network request or logging values."""
    try:
        config = LLMProviderConfig.from_file(
            environ=report_environment() if environ is None else environ
        )
    except (LLMConfigurationError, ValueError, TypeError):
        return None
    return SafetyLLMClient(
        transport=OpenAICompatibleChatTransport(
            config,
            thinking_enabled=False if (
                urlsplit(config.endpoint).hostname == "api.deepseek.com"
                and config.model_ref == "deepseek-flash"
            ) else None,
        ),
        request_builder=ProviderRequestBuilder(
            provider_ref=config.provider_ref,
            model_ref=config.model_ref,
            timeout_seconds=config.timeout_seconds,
            maximum_response_bytes=config.maximum_response_bytes,
        ),
    )


class _ServerReportIdentity:
    """Internal service identity, used only after an explicit report operation."""

    def resolve(self, request_id: str) -> TrustedIdentity:
        return TrustedIdentity(
            principal_ref="principal:configured-report-service",
            role=AgentRole.SYSTEM,
            capabilities=frozenset(),
        )


class ConfiguredReportApplication(AgentApplicationService):
    """Route only GENERATE_REPORT to the server-owned provider application."""

    def __init__(self, local_application, report_application):
        self._local_application = local_application
        self._report_application = report_application

    def execute(self, request: AgentApiRequest):
        if not isinstance(request, AgentApiRequest):
            raise TypeError("request must be an AgentApiRequest")
        application = (
            self._report_application
            if request.operation is AgentApiOperation.GENERATE_REPORT
            else self._local_application
        )
        return application.execute(request)


def configure_report_application(query_service, local_application, *, client=None):
    if client is None:
        return local_application
    tools = AgentToolService(
        event_query_service=query_service,
        safety_analytics_service=SafetyAnalyticsService(query_service),
        context_builder=SafetyContextBuilder(),
        report_service=ReportService(),
        provider_client=client,
    )
    planner = LLMPlannerAdapter(
        tools.registry, candidate_client=None, audit_service=AgentAuditService()
    )
    report_application = AgentApplicationService(
        AgentService(planner), _ServerReportIdentity()
    )
    return ConfiguredReportApplication(local_application, report_application)
