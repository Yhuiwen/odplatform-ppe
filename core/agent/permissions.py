"""Deny-by-default permissions for the frozen P8-6 tool registry."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable

from core.schemas.agent import (
    AGENT_POLICY_VERSION,
    AgentCapability,
    AgentRole,
    ToolExecutionContext,
)

__all__ = [
    "PermissionDecision",
    "ToolPermissionError",
    "ToolPermissionPolicy",
]

_ROLE_CAPABILITIES = MappingProxyType(
    {
        AgentRole.SAFETY_VIEWER: frozenset(
            {
                AgentCapability.SAFETY_READ,
                AgentCapability.STATISTICS_READ,
            }
        ),
        AgentRole.EVENT_VIEWER: frozenset(
            {AgentCapability.EVENTS_READ}
        ),
        AgentRole.SAFETY_REPORTER: frozenset(
            {
                AgentCapability.SAFETY_READ,
                AgentCapability.STATISTICS_READ,
                AgentCapability.EVENTS_READ,
                AgentCapability.REPORTS_GENERATE,
            }
        ),
        AgentRole.SYSTEM: frozenset(AgentCapability),
    }
)

_FORBIDDEN_CAPABILITY_PREFIXES = (
    "sql:",
    "filesystem:",
    "shell:",
    "mutation:",
    "event:mutate",
    "evidence:delete",
    "alert:action",
    "compliance:override",
)


class ToolPermissionError(RuntimeError):
    """Structured permission failure returned before handler execution."""

    def __init__(self, code: str, message: str) -> None:
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PermissionDecision:
    """Result of one permission check."""

    allowed: bool
    role: AgentRole
    granted_capabilities: frozenset[AgentCapability]
    required_capabilities: frozenset[AgentCapability]
    version: str = AGENT_POLICY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a boolean")
        try:
            role = AgentRole(self.role)
        except ValueError as exc:
            raise ValueError("role must be a supported AgentRole") from exc
        object.__setattr__(self, "role", role)
        object.__setattr__(
            self,
            "granted_capabilities",
            frozenset(self.granted_capabilities),
        )
        object.__setattr__(
            self,
            "required_capabilities",
            frozenset(self.required_capabilities),
        )


class ToolPermissionPolicy:
    """Map project-owned roles to explicit read/report capabilities."""

    version = AGENT_POLICY_VERSION

    def capabilities_for(
        self,
        role: AgentRole | str,
    ) -> frozenset[AgentCapability]:
        """Return the complete capability grant for one role."""

        try:
            normalized = AgentRole(role)
        except ValueError as exc:
            raise ToolPermissionError(
                "UNKNOWN_ROLE",
                "principal role is not in the project-owned allowlist",
            ) from exc
        return _ROLE_CAPABILITIES[normalized]

    def authorize(
        self,
        context: ToolExecutionContext,
        required_capabilities: Iterable[AgentCapability | str],
    ) -> PermissionDecision:
        """Authorize only explicit, known capabilities for the context role."""

        if not isinstance(context, ToolExecutionContext):
            raise TypeError("context must be a ToolExecutionContext")

        granted = self.capabilities_for(context.role)
        required = self._normalize_required(required_capabilities)

        declared = frozenset(context.capabilities)
        if declared and not declared.issubset(granted):
            raise ToolPermissionError(
                "UNAUTHORIZED",
                "execution context declares capabilities beyond its role",
            )
        if not required.issubset(granted):
            raise ToolPermissionError(
                "UNAUTHORIZED",
                "principal role does not grant every required capability",
            )
        return PermissionDecision(
            allowed=True,
            role=context.role,
            granted_capabilities=granted,
            required_capabilities=required,
        )

    @staticmethod
    def _normalize_required(
        values: Iterable[AgentCapability | str],
    ) -> frozenset[AgentCapability]:
        normalized: set[AgentCapability] = set()
        try:
            iterator = iter(values)
        except TypeError as exc:
            raise ToolPermissionError(
                "INVALID_CAPABILITY",
                "required capabilities must be iterable",
            ) from exc
        for value in iterator:
            if isinstance(value, str):
                lowered = value.strip().lower()
                if any(
                    lowered == prefix
                    or lowered.startswith(prefix)
                    for prefix in _FORBIDDEN_CAPABILITY_PREFIXES
                ):
                    raise ToolPermissionError(
                        "FORBIDDEN_CAPABILITY",
                        "the requested capability is outside the read-only policy",
                    )
            try:
                normalized.add(AgentCapability(value))
            except ValueError as exc:
                raise ToolPermissionError(
                    "INVALID_CAPABILITY",
                    "the requested capability is not in the project allowlist",
                ) from exc
        return frozenset(normalized)
