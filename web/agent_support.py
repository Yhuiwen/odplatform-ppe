"""Streamlit composition and UI-safe projection for the Phase 8 Agent."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, replace
from typing import Any, Mapping

from core.schemas.agent import AgentOutcome, AgentRole
from core.schemas.agent_api import (
    AgentApiOperation,
    AgentApiRequest,
    AgentApiResponse,
    AgentPresentationState,
    TrustedIdentity,
    TrustedIdentityProvider,
)
from services.agent_api_service import AgentApplicationService
from services.agent_audit_service import AgentAuditService
from services.agent_service import AgentService
from services.agent_tool_service import AgentToolService
from services.configured_report_service import (
    configured_report_client, configure_report_application,
)
from services.configured_assistant_service import configured_assistant_client, configure_assistant_application
from services.event_query_service import EventQueryService
from services.llm_planner_adapter import LLMPlannerAdapter
from services.report_service import ReportService
from services.safety_analytics_service import SafetyAnalyticsService
from services.safety_context_builder import SafetyContextBuilder
from web.dashboard_support import get_runtime
from web.ui.components import render_empty_state, render_page_header, render_section_header
from web.ui.formatting import available_date_range, period_from_dates
from web.ui.formatting import format_event_status, format_event_type, format_timestamp

ASSISTANT_RUNTIME_VERSION = 4

__all__ = [
    "AgentUiProjection",
    "AgentWebAdapter",
    "AgentWebRuntime",
    "LocalDemoIdentityProvider",
    "ask_safety_question",
    "build_agent_application_service",
    "build_agent_runtime",
    "generate_safety_report",
    "get_agent_runtime",
    "latest_agent_projection",
    "project_agent_response",
    "render_agent_projection",
    "agent_date_range",
    "agent_period",
    "render_agent_header",
    "render_agent_empty",
    "render_agent_section",
    "agent_event_count",
]

_MAX_PROJECTION_ITEMS = 24
_MAX_PROJECTION_TEXT = 500
_MAX_CACHED_REQUESTS = 64
_LAST_PROJECTION_KEY = "_odplatform_agent_last_projection"
_RUNTIME_KEY = "_odplatform_agent_runtime"

_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:^|[\s(\"'=])(?:"
    r"[A-Za-z]:[\\/]|"
    r"\\\\|"
    r"/(?:home|root|var|tmp|usr|etc|mnt|opt|users)/"
    r")",
    re.IGNORECASE,
)
_SQL_PATTERN = re.compile(
    r"\b(?:select\s+.+\s+from|insert\s+into|delete\s+from|"
    r"drop\s+table|update\s+.+\s+set)\b",
    re.IGNORECASE,
)
_SHELL_PATTERN = re.compile(
    r"\b(?:rm\s+-rf|powershell|cmd(?:\.exe)?|bash|sh)\b",
    re.IGNORECASE,
)
_TRACEBACK_PATTERN = re.compile(
    r"\b(?:traceback|stack trace|provider_output|raw_provider_response)\b",
    re.IGNORECASE,
)
_SECRET_PATTERN = re.compile(
    r"\b(?:api[_-]?key|authorization|credential|password|secret|token)\b"
    r"\s*[:=]",
    re.IGNORECASE,
)
_SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,299}$")
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_EVENT_REFERENCE = re.compile(
    r"\b(EVT-[A-Za-z0-9][A-Za-z0-9._:-]{0,155})\b",
    re.IGNORECASE,
)

_FACT_FIELDS = (
    "fact_id",
    "event_id",
    "id",
    "timestamp",
    "track_id",
    "type",
    "status",
    "confidence",
    "source_ref",
)
_METRIC_FIELDS = ("metric_id", "value")
_REPORT_SUMMARY_SECTIONS = (
    "executive_summary",
    "key_findings",
    "risk_observations",
)


@dataclass(frozen=True, slots=True)
class AgentUiProjection:
    """The complete data surface released to Streamlit pages."""

    answer: str
    summary: tuple[str, ...]
    evidence_references: tuple[str, ...]
    recommendations: tuple[str, ...]
    safe_status: str

    def __post_init__(self) -> None:
        answer = _safe_ui_text(
            self.answer,
            fallback="The Agent response is unavailable.",
        )
        safe_status = _safe_ui_text(
            self.safe_status,
            fallback="unavailable",
        )
        summary = _normalize_text_sequence(self.summary, "summary")
        references = _normalize_reference_sequence(
            self.evidence_references,
            "evidence_references",
        )
        recommendations = _normalize_text_sequence(
            self.recommendations,
            "recommendations",
        )
        object.__setattr__(self, "answer", answer)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "evidence_references", references)
        object.__setattr__(self, "recommendations", recommendations)
        object.__setattr__(self, "safe_status", safe_status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "summary": list(self.summary),
            "evidence_references": list(self.evidence_references),
            "recommendations": list(self.recommendations),
            "safe_status": self.safe_status,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


class LocalDemoIdentityProvider:
    """Explicit, read-only identity for the local Streamlit demo."""

    mode = "LOCAL_DEMO_READ_ONLY"

    def resolve(self, request_id: str) -> TrustedIdentity:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("request_id must be a non-empty string")
        return TrustedIdentity(
            principal_ref="principal:web-local-demo",
            role=AgentRole.SAFETY_REPORTER,
            capabilities=frozenset(),
        )


class AgentWebAdapter:
    """Cache one UI-safe projection per submitted request identity."""

    def __init__(self, application_service: AgentApplicationService, *, assistant_client=None) -> None:
        if not isinstance(application_service, AgentApplicationService):
            raise TypeError(
                "application_service must be an AgentApplicationService"
            )
        self._application_service = application_service
        self._assistant_client = assistant_client
        self._cache: dict[str, tuple[str, AgentUiProjection]] = {}

    def submit(self, request: AgentApiRequest) -> AgentUiProjection:
        """Execute once and return the same projection on a rerun."""

        if not isinstance(request, AgentApiRequest):
            raise TypeError("request must be an AgentApiRequest")
        fingerprint = _request_fingerprint(request)
        cached = self._cache.get(request.request_id)
        if cached is not None:
            cached_fingerprint, projection = cached
            if cached_fingerprint != fingerprint:
                raise ValueError(
                    "request_id was already used for a different request"
                )
            return projection

        response = self._application_service.execute(request)
        projection = project_agent_response(response)
        if request.operation is AgentApiOperation.ASK and self._assistant_client is not None:
            projection = self._compose_assistant_answer(request, response, projection)
        if len(self._cache) >= _MAX_CACHED_REQUESTS:
            oldest_request_id = next(iter(self._cache))
            del self._cache[oldest_request_id]
        self._cache[request.request_id] = (fingerprint, projection)
        return projection

    def _compose_assistant_answer(self, request, response, projection):
        if response.status is not AgentOutcome.ANSWERED:
            return projection
        lines = list(dict.fromkeys(
            _display_agent_line(line)
            for line in (projection.answer, *projection.summary)
            if line.strip()
        ))
        try:
            selected = self._assistant_client.select_statements(request.question, lines)
            if not selected:
                raise ValueError("assistant supplied no statements")
            verified = tuple(lines[index] for index in selected)
        except Exception as exc:
            code = getattr(getattr(exc, "code", None), "value", getattr(exc, "code", None))
            known_codes = {"PROVIDER_AUTH_ERROR", "PROVIDER_TIMEOUT", "PROVIDER_RATE_LIMITED", "PROVIDER_HTTP_ERROR", "PROVIDER_UNAVAILABLE", "PROVIDER_MALFORMED_RESPONSE", "PROVIDER_EMPTY_RESPONSE"}
            failure_code = code if code in known_codes else "INVALID_ASSISTANT_RESPONSE"
            return replace(projection, safe_status=projection.safe_status + " / assistant_fallback / " + failure_code)
        return replace(
            projection, answer="根据所选范围的已记录事件，查询结果如下：",
            summary=verified, safe_status=projection.safe_status + " / assistant_llm",
        )


@dataclass(frozen=True, slots=True)
class AgentWebRuntime:
    """Session-scoped projection adapter plus its identity mode."""

    adapter: AgentWebAdapter
    identity_mode: str
    report_provider_configured: bool = False
    assistant_provider_configured: bool = False


def _request_fingerprint(request: AgentApiRequest) -> str:
    return json.dumps(
        request.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def build_agent_application_service(
    event_query_service: EventQueryService,
    *,
    identity_provider: TrustedIdentityProvider | None = None,
) -> AgentApplicationService:
    """Build the existing Agent graph without a provider client."""

    if not isinstance(event_query_service, EventQueryService):
        raise TypeError("event_query_service must be an EventQueryService")
    tool_service = AgentToolService(
        event_query_service=event_query_service,
        safety_analytics_service=SafetyAnalyticsService(event_query_service),
        context_builder=SafetyContextBuilder(),
        report_service=ReportService(),
        provider_client=None,
    )
    audit_service = AgentAuditService()
    planner_adapter = LLMPlannerAdapter(
        tool_service.registry,
        candidate_client=None,
        audit_service=audit_service,
    )
    return AgentApplicationService(
        AgentService(planner_adapter),
        identity_provider or LocalDemoIdentityProvider(),
    )


def build_agent_runtime(st: Any) -> AgentWebRuntime:
    """Build one Agent session around the dashboard query boundary."""

    dashboard_runtime = get_runtime(st)
    application_service = build_agent_application_service(
        dashboard_runtime.query_service
    )
    report_client = configured_report_client()
    application_service = configure_report_application(
        dashboard_runtime.query_service, application_service, client=report_client
    )
    assistant_client = configured_assistant_client(report_client)
    application_service = configure_assistant_application(
        dashboard_runtime.query_service, application_service, client=assistant_client
    )
    return AgentWebRuntime(
        adapter=AgentWebAdapter(application_service, assistant_client=assistant_client),
        identity_mode=LocalDemoIdentityProvider.mode,
        report_provider_configured=report_client is not None,
        assistant_provider_configured=assistant_client is not None,
    )


def get_agent_runtime(st: Any) -> AgentWebRuntime:
    """Return one Streamlit-session-scoped Agent runtime."""

    from services.configured_report_service import provider_configuration_fingerprint

    fingerprint = provider_configuration_fingerprint()
    config_key = _RUNTIME_KEY + "_configuration"
    runtime = st.session_state.get(_RUNTIME_KEY)
    if config_key in st.session_state and st.session_state[config_key] != fingerprint:
        runtime = None
    if runtime is not None and not isinstance(runtime, AgentWebRuntime):
        if type(runtime).__module__ == __name__ and type(runtime).__name__ == "AgentWebRuntime":
            # Refresh an older session composition after a live code upgrade.
            runtime = None
    if runtime is None:
        runtime = build_agent_runtime(st)
        st.session_state[_RUNTIME_KEY] = runtime
        st.session_state[config_key] = fingerprint
    if not isinstance(runtime, AgentWebRuntime):
        raise TypeError("Agent session runtime has an invalid type")
    st.session_state[config_key] = fingerprint
    return runtime


def ask_safety_question(
    st: Any,
    *,
    question: str,
    requested_period: Mapping[str, Any] | None,
    filters: Mapping[str, Any] | None = None,
) -> AgentUiProjection:
    """Submit one bounded assistant question and retain its safe projection."""

    period = (
        None
        if _EVENT_REFERENCE.search(question) is not None
        else requested_period
    )
    return _submit(
        st,
        operation=AgentApiOperation.ASK,
        question=question,
        requested_period=period,
        filters=filters,
    )


def generate_safety_report(
    st: Any,
    *,
    requested_period: Mapping[str, Any],
    filters: Mapping[str, Any] | None = None,
) -> AgentUiProjection:
    """Submit the report operation without selecting provider or tool values."""

    return _submit(
        st,
        operation=AgentApiOperation.GENERATE_REPORT,
        question="Generate a safety report",
        requested_period=requested_period,
        filters=filters,
    )


def latest_agent_projection(
    st: Any, operation: str | None = None
) -> AgentUiProjection | None:
    """Return the retained projection without executing another request."""

    if operation not in (None, "report", "ask"):
        raise ValueError("unsupported projection operation")
    suffix = AgentApiOperation.GENERATE_REPORT.value if operation == "report" else AgentApiOperation.ASK.value
    key = _LAST_PROJECTION_KEY if operation is None else f"{_LAST_PROJECTION_KEY}_{suffix}"
    projection = st.session_state.get(key)
    if projection is None:
        return None
    if not isinstance(projection, AgentUiProjection):
        raise TypeError("stored Agent projection has an invalid type")
    return projection


def render_agent_projection(
    st: Any,
    projection: AgentUiProjection,
) -> None:
    """Render only the five approved projection fields."""

    if not isinstance(projection, AgentUiProjection):
        raise TypeError("projection must be an AgentUiProjection")
    st.write(_display_agent_line(projection.answer))
    status = projection.safe_status.lower()
    if "assistant_fallback" in status:
        reasons = {
            "provider_auth_error": "接口认证失败，请检查密钥。",
            "provider_timeout": "接口调用超时。",
            "provider_rate_limited": "接口请求受到限流。",
            "provider_http_error": "接口返回错误，请检查模型名称和服务状态。",
            "provider_unavailable": "暂时无法连接大模型服务。",
            "invalid_assistant_response": "模型返回的回复未通过校验。",
        }
        reason = next((label for code, label in reasons.items() if code in status), "大模型回复整理不可用。")
        st.caption(reason + "已显示本地查询结果。")
    elif "assistant_llm" in status:
        st.caption("大模型已整理回复；数字与证据来自平台查询结果。")
    elif " / degraded" in status or "fallback" in status:
        st.caption("当前使用确定性安全分析模式；内容基于已确认事件。")
    elif "unavailable" in status or "failed" in status:
        st.caption("当前结果暂不可用。")
    elif " / llm / " in status:
        st.caption("当前报告由大模型生成，已通过结构与数据依据校验。")
    else:
        st.caption("只读安全分析结果")
    if projection.summary:
        st.subheader("关键发现")
        for item in projection.summary:
            st.write(_display_agent_line(item))
    if projection.recommendations:
        st.subheader("整改建议")
        for index, item in enumerate(projection.recommendations, 1):
            st.write(f"{index}. {_display_agent_line(item)}")
    if projection.evidence_references:
        st.subheader("数据依据")
        for reference in projection.evidence_references:
            st.write(reference)


_STAT_LABELS = {
    "total_count": "事件总数",
    "by_type": "按违规类型",
    "by_status": "按处理状态",
    "by_source_ref": "按来源",
    "by_day": "按日期",
    "earliest_at": "最早事件",
    "latest_at": "最近事件",
}


def _display_agent_line(value: str) -> str:
    """Translate only recognized, already approved projection text for display."""

    report_line = _display_template_report_line(value)
    if report_line is not None:
        return report_line

    match = re.fullmatch(r"event_statistics\.([a-z_]+)=(.*)", value)
    if match and match.group(1) in _STAT_LABELS:
        field, raw = match.groups()
        if field.startswith("by_"):
            entries = []
            for pair in raw.split(", "):
                key, separator, count = pair.rpartition("=")
                if not separator or not count.isdigit():
                    return value
                label = (format_event_type(key) if field == "by_type"
                         else format_event_status(key) if field == "by_status"
                         else key)
                entries.append(f"{label} {count} 条")
            return f"{_STAT_LABELS[field]}：{'、'.join(entries)}"
        if field == "total_count" and raw.isdigit():
            return f"事件总数：{raw} 条"
        if field in {"earliest_at", "latest_at"}:
            return f"{_STAT_LABELS[field]}：{format_timestamp(raw)}"
    count = re.fullmatch(r"Event statistics returned total_count=(\d+)\.", value)
    if count:
        return f"在所选范围内查询到 {count.group(1)} 条已确认事件。"
    return value


def _display_template_report_line(value: str) -> str | None:
    """Localize the fixed fallback template after its grounding validation."""

    generated = re.fullmatch(r"Safety report generated via (.+)\.", value)
    if generated:
        return "安全报告已生成，以下内容基于已确认的事件和留证。"
    match = re.fullmatch(
        r"The reporting period contains (\d+) persisted events in the inclusive interval from "
        r"(\d{4}-\d\d-\d\dT[^ ]+Z) to (\d{4}-\d\d-\d\dT[^ ;]+Z)\.", value
    )
    if match:
        count, start, end = match.groups()
        return f"统计范围：{format_timestamp(start)} 至 {format_timestamp(end)}；共 {count} 条已持久化事件。"
    match = re.fullmatch(
        r"The reporting period contains 0 persisted events in the inclusive interval from "
        r"(\d{4}-\d\d-\d\dT[^ ]+Z) to (\d{4}-\d\d-\d\dT[^ ;]+Z); no activity is inferred for this period\.", value
    )
    if match:
        start, end = match.groups()
        return f"统计范围：{format_timestamp(start)} 至 {format_timestamp(end)}；无已持久化事件，不能据此推断期间没有活动。"
    match = re.fullmatch(r"The filtered event set contains (\d+) persisted compliance events\.", value)
    if match:
        return f"筛选范围内共有 {match.group(1)} 条已持久化的 PPE 事件。"
    match = re.fullmatch(r"Recorded events of type (NO_HELMET|NO_VEST|PPE_UNKNOWN): (\d+)\.", value)
    if match:
        event_type, count = match.groups()
        return f"{format_event_type(event_type)}：{count} 条。"
    for prefix, label in (
        ("The earliest persisted event timestamp in the reporting period is ", "最早事件"),
        ("The latest persisted event timestamp in the reporting period is ", "最近事件"),
    ):
        if value.startswith(prefix) and value.endswith("."):
            timestamp = value[len(prefix):-1]
            if re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", timestamp):
                return f"{label}：{format_timestamp(timestamp)}。"
    match = re.fullmatch(
        r"Persisted evidence references are available for (\d+) events and missing for (\d+) events\.", value
    )
    if match:
        available, missing = match.groups()
        return f"证据引用：{available} 条事件已留证，{missing} 条缺少证据。"
    match = re.fullmatch(
        r"Confirmed events were grouped across (\d+) tracker-scoped track_id values\. "
        r"These track_id values are tracker-scoped and are not stable person identity\.", value
    )
    if match:
        return f"已确认事件涉及 {match.group(1)} 个跟踪轨迹 ID；轨迹 ID 仅在跟踪范围内有效，不能视为人员身份。"
    match = re.fullmatch(
        r"The most frequent recorded event type is (NO_HELMET|NO_VEST|PPE_UNKNOWN) with (\d+) events\. "
        r"This statement is limited to observed frequency and does not establish severity, legal causation or employee identity\.", value
    )
    if match:
        event_type, count = match.groups()
        return f"记录最多的类型是{format_event_type(event_type)}（{count} 条）。这仅表示出现频次，不能据此判断严重程度、法律责任或人员身份。"
    recommendations = {
        "Review helmet-use procedures and the relevant recorded evidence for NO_HELMET events.": "核查安全帽佩戴流程，并复核未佩戴安全帽事件的留证。",
        "Review high-visibility vest procedures and the relevant recorded evidence for NO_VEST events.": "核查反光衣穿戴流程，并复核未穿反光衣事件的留证。",
        "Review uncertain PPE detections and their evidence before taking operational action.": "采取处置措施前，先人工核查 PPE 状态未知事件及其证据。",
    }
    priority = re.fullmatch(r"\[(HIGH|MEDIUM|LOW)\] (.+)", value)
    if priority and priority.group(2) in recommendations:
        priority_label = {"HIGH": "高", "MEDIUM": "中", "LOW": "低"}[priority.group(1)]
        return f"【{priority_label}优先级】{recommendations[priority.group(2)]}"
    return recommendations.get(value)


def agent_date_range(st: Any):
    return available_date_range(get_runtime(st).query_service.statistics())


def agent_period(start, end):
    return period_from_dates(start, end)


def agent_event_count(st: Any, period):
    return get_runtime(st).query_service.list_events(**period, limit=1).total_count


def render_agent_header(title, subtitle):
    render_page_header(title, subtitle)


def render_agent_empty(title, description):
    render_empty_state(title, description)


def render_agent_section(title):
    render_section_header(title)


def _submit(
    st: Any,
    *,
    operation: AgentApiOperation,
    question: str,
    requested_period: Mapping[str, Any] | None,
    filters: Mapping[str, Any] | None,
) -> AgentUiProjection:
    request = AgentApiRequest(
        request_id=f"WEB-{uuid.uuid4().hex}",
        operation=operation,
        question=question,
        requested_period=requested_period,
        filters=filters,
    )
    projection = get_agent_runtime(st).adapter.submit(request)
    st.session_state[_LAST_PROJECTION_KEY] = projection
    st.session_state[f"{_LAST_PROJECTION_KEY}_{operation.value}"] = projection
    return projection


def project_agent_response(
    response: AgentApiResponse,
) -> AgentUiProjection:
    """Convert the API response into the five-field UI contract."""

    if not isinstance(response, AgentApiResponse):
        raise TypeError("response must be an AgentApiResponse")

    state = AgentPresentationState(response.presentation_state)
    answer = _safe_ui_text(
        response.answer,
        fallback="The Agent response is unavailable.",
    )
    if response.status is not AgentOutcome.ANSWERED:
        return AgentUiProjection(
            answer=answer,
            summary=(),
            evidence_references=(),
            recommendations=(),
            safe_status=_safe_status(response),
        )

    return AgentUiProjection(
        answer=answer,
        summary=_project_summary(response),
        evidence_references=_project_evidence_references(response),
        recommendations=_project_recommendations(response),
        safe_status=_safe_status(response),
    )


def _project_summary(response: AgentApiResponse) -> tuple[str, ...]:
    if response.report is not None:
        statements: list[str] = []
        for section_name in _REPORT_SUMMARY_SECTIONS:
            section = response.report.get(section_name)
            if not isinstance(section, (list, tuple)):
                continue
            for item in section:
                if not isinstance(item, Mapping):
                    continue
                statement = _safe_ui_text(item.get("statement"), fallback="")
                if statement:
                    statements.append(statement)
                if len(statements) >= _MAX_PROJECTION_ITEMS:
                    return tuple(statements)
        if statements:
            return tuple(statements)

    entries: list[str] = []
    for fact in response.facts:
        line = _project_mapping(fact, _FACT_FIELDS)
        if line:
            entries.append(line)
        if len(entries) >= _MAX_PROJECTION_ITEMS:
            return tuple(entries)
    for metric in response.metrics:
        line = _project_mapping(metric, _METRIC_FIELDS)
        if line:
            entries.append(line)
        if len(entries) >= _MAX_PROJECTION_ITEMS:
            break
    return tuple(entries)


def _project_recommendations(response: AgentApiResponse) -> tuple[str, ...]:
    if response.report is None:
        return ()
    recommendations = response.report.get("recommendations")
    if not isinstance(recommendations, (list, tuple)):
        return ()

    projected: list[str] = []
    for item in recommendations:
        if not isinstance(item, Mapping):
            continue
        action = _safe_ui_text(item.get("action"), fallback="")
        if not action:
            continue
        priority = _safe_identifier(item.get("priority"))
        projected.append(
            action if priority is None else f"[{priority.upper()}] {action}"
        )
        if len(projected) >= _MAX_PROJECTION_ITEMS:
            break
    return tuple(projected)


def _project_evidence_references(
    response: AgentApiResponse,
) -> tuple[str, ...]:
    references = {
        reference
        for value in response.evidence_refs
        if (reference := _safe_reference(value)) is not None
    }
    if response.report is not None:
        report_refs = response.report.get("evidence_references")
        if isinstance(report_refs, (list, tuple)):
            for item in report_refs:
                if not isinstance(item, Mapping):
                    continue
                for field_name in ("evidence_ref", "snapshot_ref"):
                    reference = _safe_reference(item.get(field_name))
                    if reference is not None:
                        references.add(reference)
    return tuple(sorted(references))


def _project_mapping(
    item: Mapping[str, Any],
    allowed_fields: tuple[str, ...],
) -> str:
    if "metric_id" in allowed_fields and "value" in allowed_fields:
        metric_id = _safe_identifier(item.get("metric_id"))
        value = _render_scalar(item.get("value"))
        if metric_id is not None and value is not None:
            return f"{metric_id}={value}"

    parts: list[str] = []
    for field_name in allowed_fields:
        value = item.get(field_name)
        rendered = _render_scalar(value)
        if rendered is not None:
            parts.append(f"{field_name}={rendered}")
    return "; ".join(parts)


def _render_scalar(value: Any) -> str | None:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, str):
        return _safe_ui_text(value, fallback="") or None
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key, child in sorted(value.items(), key=lambda pair: str(pair[0])):
            if not isinstance(key, str) or not _SAFE_IDENTIFIER.fullmatch(key):
                continue
            rendered = _render_scalar(child)
            if rendered is None:
                continue
            parts.append(f"{key}={rendered}")
            if len(parts) >= 12:
                break
        return ", ".join(parts) if parts else None
    return None


def _safe_status(response: AgentApiResponse) -> str:
    state = AgentPresentationState(response.presentation_state)
    parts = [state.value]
    if state is AgentPresentationState.SUCCESS and response.report is not None:
        parts.append(response.provider_status.value)
        parts.append("degraded" if response.degraded else "not_degraded")
        grounding = _safe_identifier(response.report.get("grounding_status"))
        if grounding is not None:
            parts.append(f"grounding={grounding}")
    if response.safe_error is not None:
        parts.append(response.safe_error.code)
    return " / ".join(parts)


def _safe_ui_text(value: Any, *, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    normalized = " ".join(value.split())
    if not normalized:
        return fallback
    if (
        _ABSOLUTE_PATH_PATTERN.search(normalized) is not None
        or _SQL_PATTERN.search(normalized) is not None
        or _SHELL_PATTERN.search(normalized) is not None
        or _TRACEBACK_PATTERN.search(normalized) is not None
        or _SECRET_PATTERN.search(normalized) is not None
    ):
        return fallback
    return normalized[:_MAX_PROJECTION_TEXT]


def _safe_identifier(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if _SAFE_IDENTIFIER.fullmatch(normalized) is None:
        return None
    return normalized


def _safe_reference(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if (
        _SAFE_REFERENCE.fullmatch(normalized) is None
        or normalized.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:[\\/]", normalized) is not None
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        return None
    return normalized


def _normalize_text_sequence(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be a tuple of strings") from exc
    if any(not isinstance(value, str) for value in normalized):
        raise TypeError(f"{field_name} must contain strings")
    return tuple(
        safe
        for value in normalized
        if (safe := _safe_ui_text(value, fallback=""))
    )[:_MAX_PROJECTION_ITEMS]


def _normalize_reference_sequence(
    values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be a tuple of strings") from exc
    references: list[str] = []
    for value in normalized:
        reference = _safe_reference(value)
        if reference is None:
            raise ValueError(f"{field_name} contains an unsafe reference")
        references.append(reference)
    return tuple(sorted(set(references)))[:_MAX_PROJECTION_ITEMS]
