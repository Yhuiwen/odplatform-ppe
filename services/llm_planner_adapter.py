"""LLM planner adapter with strict validation and deterministic fallback."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from core.agent.candidate import (
    AgentPlanCandidateError,
    AgentPlanCandidateParser,
    AgentPlanCandidateValidator,
    normalize_agent_question,
)
from core.agent.llm_planner import (
    LLMPlannerCandidateClient,
    LLMPlannerClientError,
    PlannerCandidateRequestBuilder,
)
from core.agent.permissions import (
    ToolPermissionError,
    ToolPermissionPolicy,
)
from core.agent.planner import (
    AgentPlanningError,
    DeterministicAgentPlanner,
)
from core.agent.tool_registry import ToolRegistry
from core.schemas.agent import (
    AgentAuditStatus,
    AgentCapability,
    AgentIntent,
    AgentPlan,
    AuditEvent,
    ToolExecutionContext,
)
from services.agent_audit_service import (
    AgentAuditError,
    AgentAuditService,
)

__all__ = [
    "LLMPlannerAdapter",
    "LLMPlannerError",
    "LLMPlannerOutcome",
]

_PLANNING_PATH_LLM = "LLM_VALIDATED"
_PLANNING_PATH_DETERMINISTIC = "DETERMINISTIC"
_PLANNING_PATH_FALLBACK = "DETERMINISTIC_FALLBACK"

_REFUSAL_CODES = frozenset(
    {
        "FORBIDDEN_REQUEST",
        "FORBIDDEN_CAPABILITY",
        "UNAUTHORIZED",
    }
)


class LLMPlannerError(RuntimeError):
    """A structured planner failure that never returns an executable plan."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        audit_events: tuple[AuditEvent, ...] = (),
    ) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message.strip()
        self.audit_events = tuple(audit_events)
        super().__init__(self.message)


@dataclass(frozen=True, slots=True)
class LLMPlannerOutcome:
    """One validated plan plus bounded planning-path audit evidence."""

    plan: AgentPlan
    planning_path: str
    candidate_attempted: bool
    fallback_used: bool
    audit_events: tuple[AuditEvent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.plan, AgentPlan):
            raise TypeError("plan must be an AgentPlan")
        if self.planning_path not in {
            _PLANNING_PATH_LLM,
            _PLANNING_PATH_DETERMINISTIC,
            _PLANNING_PATH_FALLBACK,
        }:
            raise ValueError("planning_path is not supported")
        if not isinstance(self.candidate_attempted, bool):
            raise TypeError("candidate_attempted must be a boolean")
        if not isinstance(self.fallback_used, bool):
            raise TypeError("fallback_used must be a boolean")
        events = tuple(self.audit_events)
        if any(not isinstance(event, AuditEvent) for event in events):
            raise TypeError("audit_events must contain AuditEvent values")
        object.__setattr__(self, "audit_events", events)


class LLMPlannerAdapter:
    """Optional LLM candidate generation followed by deterministic validation."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        candidate_client: LLMPlannerCandidateClient | None = None,
        policy: ToolPermissionPolicy | None = None,
        audit_service: AgentAuditService | None = None,
        request_builder: PlannerCandidateRequestBuilder | None = None,
        parser: AgentPlanCandidateParser | None = None,
        validator: AgentPlanCandidateValidator | None = None,
        planner: DeterministicAgentPlanner | None = None,
    ) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TypeError("registry must be a ToolRegistry")
        if candidate_client is not None and not callable(
            getattr(candidate_client, "generate_candidate", None)
        ):
            raise TypeError(
                "candidate_client must expose generate_candidate(request)"
            )
        if policy is not None and not isinstance(
            policy,
            ToolPermissionPolicy,
        ):
            raise TypeError("policy must be a ToolPermissionPolicy or None")
        if audit_service is not None and not isinstance(
            audit_service,
            AgentAuditService,
        ):
            raise TypeError("audit_service must be an AgentAuditService or None")
        if request_builder is not None and not isinstance(
            request_builder,
            PlannerCandidateRequestBuilder,
        ):
            raise TypeError(
                "request_builder must be a PlannerCandidateRequestBuilder or None"
            )
        if parser is not None and not isinstance(
            parser,
            AgentPlanCandidateParser,
        ):
            raise TypeError("parser must be an AgentPlanCandidateParser or None")
        if validator is not None and not isinstance(
            validator,
            AgentPlanCandidateValidator,
        ):
            raise TypeError(
                "validator must be an AgentPlanCandidateValidator or None"
            )
        if planner is not None and not isinstance(
            planner,
            DeterministicAgentPlanner,
        ):
            raise TypeError(
                "planner must be a DeterministicAgentPlanner or None"
            )

        self.registry = registry
        self.candidate_client = candidate_client
        self.policy = policy or ToolPermissionPolicy()
        self.audit_service = audit_service or AgentAuditService()
        self.planner = planner or DeterministicAgentPlanner(
            registry,
            policy=self.policy,
        )
        self.request_builder = request_builder or PlannerCandidateRequestBuilder(
            registry
        )
        self.parser = parser or AgentPlanCandidateParser()
        self.validator = validator or AgentPlanCandidateValidator(
            registry,
            policy=self.policy,
            planner=self.planner,
        )

    def plan(
        self,
        question: str,
        *,
        context: ToolExecutionContext,
        requested_period: Mapping[str, Any] | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> LLMPlannerOutcome:
        """Return a validated plan without executing any tool."""

        if not isinstance(context, ToolExecutionContext):
            raise LLMPlannerError(
                "INVALID_REQUEST",
                "a validated Agent execution context is required",
            )
        try:
            normalized = normalize_agent_question(question)
            deterministic_intent = self.planner.classify(normalized)
        except (AgentPlanningError, AgentPlanCandidateError) as exc:
            raise LLMPlannerError(exc.code, exc.message) from exc

        if deterministic_intent is AgentIntent.FORBIDDEN_REQUEST:
            failure_event = self._record_failure(
                context=context,
                intent=deterministic_intent,
                question_sha256=self._question_sha256(normalized),
                execution_status=AgentAuditStatus.REFUSED,
                failure_status="FORBIDDEN_REQUEST",
                fallback_used=False,
            )
            raise LLMPlannerError(
                "FORBIDDEN_REQUEST",
                "the request asks for a mutation, administration or "
                "system action outside the read-only Agent scope",
                audit_events=(failure_event,),
            ) from None

        if self._provider_access_allowed(context) and self.candidate_client is not None:
            return self._plan_with_candidate(
                normalized=normalized,
                deterministic_intent=deterministic_intent,
                context=context,
                requested_period=requested_period,
                filters=filters,
            )

        return self._deterministic_outcome(
            normalized=normalized,
            context=context,
            requested_period=requested_period,
            filters=filters,
            candidate_attempted=False,
            fallback_used=False,
            prior_events=(),
        )

    def _plan_with_candidate(
        self,
        *,
        normalized: str,
        deterministic_intent: AgentIntent,
        context: ToolExecutionContext,
        requested_period: Mapping[str, Any] | None,
        filters: Mapping[str, Any] | None,
    ) -> LLMPlannerOutcome:
        request = self.request_builder.build(normalized)
        assert self.candidate_client is not None
        try:
            raw_candidate = self.candidate_client.generate_candidate(request)
        except LLMPlannerClientError as exc:
            failure_event = self._record_failure(
                context=context,
                intent=deterministic_intent,
                question_sha256=self._question_sha256(normalized),
                execution_status=AgentAuditStatus.FAILURE,
                failure_status=exc.code,
                fallback_used=True,
            )
            return self._deterministic_outcome(
                normalized=normalized,
                context=context,
                requested_period=requested_period,
                filters=filters,
                candidate_attempted=True,
                fallback_used=True,
                prior_events=(failure_event,),
            )
        except Exception:
            failure_event = self._record_failure(
                context=context,
                intent=deterministic_intent,
                question_sha256=self._question_sha256(normalized),
                execution_status=AgentAuditStatus.FAILURE,
                failure_status="PROVIDER_UNAVAILABLE",
                fallback_used=True,
            )
            return self._deterministic_outcome(
                normalized=normalized,
                context=context,
                requested_period=requested_period,
                filters=filters,
                candidate_attempted=True,
                fallback_used=True,
                prior_events=(failure_event,),
            )

        try:
            candidate = self.parser.parse(raw_candidate)
            plan = self.validator.validate(
                candidate,
                question=normalized,
                context=context,
            )
        except AgentPlanCandidateError as exc:
            if exc.code in _REFUSAL_CODES:
                failure_event = self._record_failure(
                    context=context,
                    intent=deterministic_intent,
                    question_sha256=self._question_sha256(normalized),
                    execution_status=AgentAuditStatus.REFUSED,
                    failure_status=exc.code,
                    fallback_used=False,
                )
                raise LLMPlannerError(
                    exc.code,
                    exc.message,
                    audit_events=(failure_event,),
                ) from None

            if exc.code == "TOOL_NOT_FOUND":
                failure_event = self._record_failure(
                    context=context,
                    intent=deterministic_intent,
                    question_sha256=self._question_sha256(normalized),
                    execution_status=AgentAuditStatus.UNKNOWN_TOOL,
                    failure_status="TOOL_NOT_FOUND",
                    fallback_used=True,
                )
            else:
                failure_event = self._record_failure(
                    context=context,
                    intent=deterministic_intent,
                    question_sha256=self._question_sha256(normalized),
                    execution_status=AgentAuditStatus.FAILURE,
                    failure_status="INVALID_PLANNER_OUTPUT",
                    fallback_used=True,
                )
            return self._deterministic_outcome(
                normalized=normalized,
                context=context,
                requested_period=requested_period,
                filters=filters,
                candidate_attempted=True,
                fallback_used=True,
                prior_events=(failure_event,),
            )

        try:
            plan_event = self.audit_service.record_plan(
                plan,
                context,
                metadata={
                    "fallback_used": False,
                    "policy_version": self.policy.version,
                    "registry_version": self.registry.version,
                },
            )
        except AgentAuditError as exc:
            raise LLMPlannerError("AUDIT_UNAVAILABLE", exc.message) from exc
        return LLMPlannerOutcome(
            plan=plan,
            planning_path=_PLANNING_PATH_LLM,
            candidate_attempted=True,
            fallback_used=False,
            audit_events=(plan_event,),
        )

    def _deterministic_outcome(
        self,
        *,
        normalized: str,
        context: ToolExecutionContext,
        requested_period: Mapping[str, Any] | None,
        filters: Mapping[str, Any] | None,
        candidate_attempted: bool,
        fallback_used: bool,
        prior_events: tuple[AuditEvent, ...],
    ) -> LLMPlannerOutcome:
        try:
            plan = self.planner.plan(
                normalized,
                context=context,
                requested_period=requested_period,
                filters=filters,
            )
        except AgentPlanningError as exc:
            status = (
                AgentAuditStatus.REFUSED
                if exc.code in _REFUSAL_CODES
                else AgentAuditStatus.FAILURE
            )
            failure_event = self._record_failure(
                context=context,
                intent=self.planner.classify(normalized),
                question_sha256=self._question_sha256(normalized),
                execution_status=status,
                failure_status=exc.code,
                fallback_used=fallback_used,
            )
            raise LLMPlannerError(
                exc.code,
                exc.message,
                audit_events=(*prior_events, failure_event),
            ) from exc

        try:
            plan_event = self.audit_service.record_plan(
                plan,
                context,
                metadata={
                    "fallback_used": fallback_used,
                    "policy_version": self.policy.version,
                    "registry_version": self.registry.version,
                },
            )
        except AgentAuditError as exc:
            raise LLMPlannerError("AUDIT_UNAVAILABLE", exc.message) from exc
        return LLMPlannerOutcome(
            plan=plan,
            planning_path=(
                _PLANNING_PATH_FALLBACK
                if fallback_used
                else _PLANNING_PATH_DETERMINISTIC
            ),
            candidate_attempted=candidate_attempted,
            fallback_used=fallback_used,
            audit_events=(*prior_events, plan_event),
        )

    def _provider_access_allowed(self, context: ToolExecutionContext) -> bool:
        try:
            self.policy.authorize(
                context,
                (AgentCapability.PROVIDER_INVOKE,),
            )
        except ToolPermissionError:
            return False
        return True

    def _record_failure(
        self,
        *,
        context: ToolExecutionContext,
        intent: AgentIntent,
        question_sha256: str,
        execution_status: AgentAuditStatus,
        failure_status: str,
        fallback_used: bool,
    ) -> AuditEvent:
        plan_id = "PLAN-" + hashlib.sha256(
            (
                f"{context.request_id}:{question_sha256}:"
                f"{execution_status.value}:{failure_status}"
            ).encode("utf-8")
        ).hexdigest()[:16]
        try:
            return self.audit_service.record_event(
                request_id=context.request_id,
                principal_ref=context.principal_ref,
                role_ref=context.role,
                intent=intent,
                plan_id=plan_id,
                tools_requested=(),
                execution_status=execution_status,
                failure_status=failure_status,
                question_sha256=question_sha256,
                metadata={
                    "fallback_used": fallback_used,
                    "policy_version": self.policy.version,
                    "registry_version": self.registry.version,
                },
            )
        except AgentAuditError as exc:
            raise LLMPlannerError("AUDIT_UNAVAILABLE", exc.message) from exc

    @staticmethod
    def _question_sha256(normalized: str) -> str:
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
