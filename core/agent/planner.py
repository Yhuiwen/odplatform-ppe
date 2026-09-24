"""Deterministic, rule-based planning for the frozen P8-6 tool registry."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Mapping

from core.agent.permissions import (
    ToolPermissionError,
    ToolPermissionPolicy,
)
from core.agent.tool_registry import ToolRegistry, ToolRegistryError
from core.schemas.agent import (
    AgentIntent,
    AgentPlan,
    ToolExecutionContext,
)
from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus
from core.schemas.safety import ReportingPeriod

__all__ = [
    "AgentPlanner",
    "AgentPlanningError",
    "DEFAULT_MAX_QUESTION_BYTES",
    "DEFAULT_MAX_REPORTING_INTERVAL_DAYS",
    "DeterministicAgentPlanner",
]

DEFAULT_MAX_QUESTION_BYTES = 2000
DEFAULT_MAX_REPORTING_INTERVAL_DAYS = 366

_SUPPORTED_TOOLS = {
    AgentIntent.SAFETY_SUMMARY: "get_safety_summary",
    AgentIntent.EVENT_STATISTICS: "get_event_statistics",
    AgentIntent.EVENT_DETAIL: "get_event_details",
    AgentIntent.SAFETY_REPORT: "generate_safety_report",
}

_REPORT_PATTERN = re.compile(
    r"\b(?:report|reports|reporting)\b|报告",
    re.IGNORECASE,
)
_EVENT_DETAIL_PATTERN = re.compile(
    r"\b(?:event\s+details?|details?\s+(?:for|of)\s+event|"
    r"show\s+(?:me\s+)?event\s+details?|event\s+id)\b|事件详情|具体事件",
    re.IGNORECASE,
)
_STATISTICS_PATTERN = re.compile(
    r"\b(?:statistics?|stats?|how\s+many|count|number\s+of)\b|统计|数量",
    re.IGNORECASE,
)
_SUMMARY_PATTERN = re.compile(
    r"\b(?:summary|summari[sz]e|overview)\b|安全摘要|摘要|总体情况",
    re.IGNORECASE,
)

_FORBIDDEN_PATTERNS = (
    re.compile(
        r"\b(?:delete|remove|update|modify|mutate|insert|drop|truncate|"
        r"erase|overwrite)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:admin|administrator|grant|revoke|permission|role)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:sql|shell|command|filesystem|file\s+system|system\s+action|"
        r"execute)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"删除|修改|更新|覆盖|管理|授权|权限|命令|文件系统|系统操作|"
        r"执行代码|执行命令",
        re.IGNORECASE,
    ),
)

_EVENT_ID_PATTERN = re.compile(
    r"\b(EVT-[A-Za-z0-9][A-Za-z0-9._:-]{0,155})\b",
    re.IGNORECASE,
)
_SAFE_EVENT_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$"
)
_TIME_FILTER_FIELDS = frozenset({"start_at", "end_at"})


class AgentPlanningError(RuntimeError):
    """A bounded planner refusal that never executes a tool."""

    def __init__(self, code: str, message: str) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message
        super().__init__(message)


class DeterministicAgentPlanner:
    """Map bounded questions to one validated static-tool execution plan."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        policy: ToolPermissionPolicy | None = None,
        max_question_bytes: int = DEFAULT_MAX_QUESTION_BYTES,
        max_reporting_interval_days: int = (
            DEFAULT_MAX_REPORTING_INTERVAL_DAYS
        ),
    ) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TypeError("registry must be a ToolRegistry")
        if policy is not None and not isinstance(
            policy,
            ToolPermissionPolicy,
        ):
            raise TypeError("policy must be a ToolPermissionPolicy or None")
        if (
            isinstance(max_question_bytes, bool)
            or not isinstance(max_question_bytes, int)
            or max_question_bytes <= 0
        ):
            raise ValueError("max_question_bytes must be a positive integer")
        if (
            isinstance(max_reporting_interval_days, bool)
            or not isinstance(max_reporting_interval_days, int)
            or max_reporting_interval_days <= 0
        ):
            raise ValueError(
                "max_reporting_interval_days must be a positive integer"
            )

        self.registry = registry
        self.policy = policy or ToolPermissionPolicy()
        self.max_question_bytes = max_question_bytes
        self.max_reporting_interval_days = max_reporting_interval_days

    def classify(self, question: str) -> AgentIntent:
        """Classify one question without executing a tool."""

        normalized = self._normalize_question(question)
        if any(pattern.search(normalized) for pattern in _FORBIDDEN_PATTERNS):
            return AgentIntent.FORBIDDEN_REQUEST
        if _REPORT_PATTERN.search(normalized):
            return AgentIntent.SAFETY_REPORT
        if (
            _EVENT_DETAIL_PATTERN.search(normalized)
            or _EVENT_ID_PATTERN.search(normalized)
        ):
            return AgentIntent.EVENT_DETAIL
        if _STATISTICS_PATTERN.search(normalized):
            return AgentIntent.EVENT_STATISTICS
        if _SUMMARY_PATTERN.search(normalized):
            return AgentIntent.SAFETY_SUMMARY
        return AgentIntent.UNKNOWN

    def plan(
        self,
        question: str,
        *,
        context: ToolExecutionContext,
        requested_period: ReportingPeriod | Mapping[str, Any] | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> AgentPlan:
        """Return a validated plan; this method never executes the tool."""

        normalized = self._normalize_question(question)
        intent = self.classify(normalized)
        if intent is AgentIntent.FORBIDDEN_REQUEST:
            raise AgentPlanningError(
                "FORBIDDEN_REQUEST",
                "the request asks for a mutation, administration or "
                "system action outside the read-only Agent scope",
            )
        if intent is AgentIntent.UNKNOWN:
            raise AgentPlanningError(
                "OUT_OF_SCOPE",
                "the question does not map to a supported read-only intent",
            )
        if not isinstance(context, ToolExecutionContext):
            raise AgentPlanningError(
                "INVALID_REQUEST",
                "a validated Agent execution context is required",
            )

        tool_name = _SUPPORTED_TOOLS[intent]
        try:
            tool = self.registry.resolve(tool_name, "1.0.0")
        except ToolRegistryError as exc:
            raise AgentPlanningError(
                "TOOL_UNAVAILABLE",
                "the deterministic plan does not resolve to an allowed tool",
            ) from exc

        try:
            self.policy.authorize(
                context,
                tool.descriptor.required_capabilities,
            )
        except ToolPermissionError as exc:
            raise AgentPlanningError("UNAUTHORIZED", exc.message) from exc

        normalized_filters = self._normalize_filters(
            filters,
            allowed_fields=tool.descriptor.input_schema,
        )
        arguments = self._build_arguments(
            intent=intent,
            question=normalized,
            requested_period=requested_period,
            filters=normalized_filters,
            input_schema=tool.descriptor.input_schema,
        )
        return AgentPlan(
            intent=intent,
            tool_name=tool.tool_name,
            tool_version=tool.tool_version,
            arguments=arguments,
            question_sha256=hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest(),
        )

    def _normalize_question(self, question: str) -> str:
        if not isinstance(question, str):
            raise AgentPlanningError(
                "INVALID_REQUEST",
                "question must be a UTF-8 string",
            )
        normalized = " ".join(question.split())
        if not normalized:
            raise AgentPlanningError(
                "INVALID_REQUEST",
                "question cannot be empty",
            )
        if len(normalized.encode("utf-8")) > self.max_question_bytes:
            raise AgentPlanningError(
                "INVALID_REQUEST",
                "question exceeds the frozen byte limit",
            )
        return normalized

    def _build_arguments(
        self,
        *,
        intent: AgentIntent,
        question: str,
        requested_period: ReportingPeriod | Mapping[str, Any] | None,
        filters: Mapping[str, Any],
        input_schema: tuple[str, ...],
    ) -> dict[str, Any]:
        if intent is AgentIntent.EVENT_DETAIL:
            return self._event_detail_arguments(
                question=question,
                requested_period=requested_period,
                filters=filters,
            )

        period = self._normalize_period(requested_period)
        if period is None:
            raise AgentPlanningError(
                "INVALID_REQUEST",
                "a valid reporting period is required for this intent",
            )
        if "start_at" not in input_schema or "end_at" not in input_schema:
            raise AgentPlanningError(
                "TOOL_UNAVAILABLE",
                "the selected tool does not accept a reporting period",
            )
        return {**period, **filters}

    def _event_detail_arguments(
        self,
        *,
        question: str,
        requested_period: ReportingPeriod | Mapping[str, Any] | None,
        filters: Mapping[str, Any],
    ) -> dict[str, Any]:
        question_event_id = self._extract_event_id(question)
        filter_event_id = filters.get("event_id")
        if (
            question_event_id is not None
            and filter_event_id is not None
            and question_event_id != filter_event_id
        ):
            raise AgentPlanningError(
                "INVALID_ARGUMENTS",
                "the question and filters contain different event identities",
            )

        event_id = question_event_id or filter_event_id
        if event_id is not None:
            if requested_period is not None:
                raise AgentPlanningError(
                    "INVALID_ARGUMENTS",
                    "event_id and requested_period cannot be combined",
                )
            remaining = {
                key: value
                for key, value in filters.items()
                if key != "event_id"
            }
            if remaining:
                raise AgentPlanningError(
                    "INVALID_ARGUMENTS",
                    "event_id cannot be combined with other query filters",
                )
            return {"event_id": event_id}

        period = self._normalize_period(requested_period)
        if period is None:
            raise AgentPlanningError(
                "INVALID_REQUEST",
                "event details require an event_id or reporting period",
            )
        arguments = {**period, **filters}
        arguments.setdefault("limit", 20)
        arguments.setdefault("offset", 0)
        return arguments

    def _normalize_period(
        self,
        requested_period: ReportingPeriod | Mapping[str, Any] | None,
    ) -> dict[str, str] | None:
        if requested_period is None:
            return None
        if isinstance(requested_period, ReportingPeriod):
            start_at = requested_period.start_at
            end_at = requested_period.end_at
        elif isinstance(requested_period, Mapping):
            unknown = set(requested_period) - {"start_at", "end_at"}
            if unknown:
                raise AgentPlanningError(
                    "INVALID_ARGUMENTS",
                    "requested_period contains unsupported fields",
                )
            try:
                period = ReportingPeriod(
                    requested_period["start_at"],
                    requested_period["end_at"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise AgentPlanningError(
                    "INVALID_ARGUMENTS",
                    "requested_period must contain valid UTC bounds",
                ) from exc
            start_at = period.start_at
            end_at = period.end_at
        else:
            raise AgentPlanningError(
                "INVALID_ARGUMENTS",
                "requested_period must be a ReportingPeriod or mapping",
            )

        start = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
        if end - start > timedelta(days=self.max_reporting_interval_days):
            raise AgentPlanningError(
                "INVALID_ARGUMENTS",
                "reporting period exceeds the frozen maximum interval",
            )
        return {"start_at": start_at, "end_at": end_at}

    @staticmethod
    def _normalize_filters(
        filters: Mapping[str, Any] | None,
        *,
        allowed_fields: tuple[str, ...],
    ) -> dict[str, Any]:
        if filters is None:
            return {}
        if not isinstance(filters, Mapping):
            raise AgentPlanningError(
                "INVALID_ARGUMENTS",
                "filters must be a mapping",
            )
        allowed = set(allowed_fields)
        normalized: dict[str, Any] = {}
        for key, value in filters.items():
            if not isinstance(key, str) or key not in allowed:
                raise AgentPlanningError(
                    "INVALID_ARGUMENTS",
                    "filters contain an unsupported field",
                )
            if key in _TIME_FILTER_FIELDS:
                raise AgentPlanningError(
                    "INVALID_ARGUMENTS",
                    "time bounds must be provided through requested_period",
                )
            if value is None:
                raise AgentPlanningError(
                    "INVALID_ARGUMENTS",
                    "filter values cannot be null",
                )
            if key == "event_type":
                try:
                    value = ComplianceEventType(value).value
                except (TypeError, ValueError) as exc:
                    raise AgentPlanningError(
                        "INVALID_ARGUMENTS",
                        "event_type is not supported",
                    ) from exc
            elif key == "status":
                try:
                    value = EventStatus(value).value
                except (TypeError, ValueError) as exc:
                    raise AgentPlanningError(
                        "INVALID_ARGUMENTS",
                        "status is not supported",
                    ) from exc
            elif key == "track_id":
                if isinstance(value, bool) or not isinstance(value, int):
                    raise AgentPlanningError(
                        "INVALID_ARGUMENTS",
                        "track_id must be a non-negative integer",
                    )
                if value < 0:
                    raise AgentPlanningError(
                        "INVALID_ARGUMENTS",
                        "track_id must be a non-negative integer",
                    )
            elif key == "limit":
                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or not 1 <= value <= 100
                ):
                    raise AgentPlanningError(
                        "INVALID_ARGUMENTS",
                        "limit must be between 1 and 100",
                    )
            elif key == "offset":
                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                ):
                    raise AgentPlanningError(
                        "INVALID_ARGUMENTS",
                        "offset must be a non-negative integer",
                    )
            elif key == "event_id":
                value = DeterministicAgentPlanner._normalize_event_id(value)
            normalized[key] = value
        return normalized

    @staticmethod
    def _normalize_event_id(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AgentPlanningError(
                "INVALID_ARGUMENTS",
                "event_id must be a bounded opaque identifier",
            )
        normalized = value.strip()
        if _SAFE_EVENT_ID_PATTERN.fullmatch(normalized) is None:
            raise AgentPlanningError(
                "INVALID_ARGUMENTS",
                "event_id must be a bounded opaque identifier",
            )
        return normalized

    @staticmethod
    def _extract_event_id(question: str) -> str | None:
        match = _EVENT_ID_PATTERN.search(question)
        if match is None:
            return None
        candidate = match.group(1).rstrip(".,;:!?")
        if _SAFE_EVENT_ID_PATTERN.fullmatch(candidate) is None:
            return None
        return candidate


AgentPlanner = DeterministicAgentPlanner
