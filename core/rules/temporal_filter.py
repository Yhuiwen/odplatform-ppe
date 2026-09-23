"""Multi-frame confirmation for compliance candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.rules.compliance_engine import (
    ComplianceInputError,
    RuleSettings,
    load_rule_settings,
)
from core.schemas.compliance import (
    ComplianceEventType,
    ComplianceFinding,
    ComplianceResult,
)

__all__ = ["TemporalViolationFilter"]


@dataclass(slots=True)
class _CandidateState:
    first_timestamp: float
    last_timestamp: float
    frame_count: int = 1
    confidences: list[float] = field(default_factory=list)
    confirmed: bool = False


class TemporalViolationFilter:
    """Confirm only candidates that satisfy frame and duration thresholds."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        settings: RuleSettings | None = None,
    ) -> None:
        self.settings = settings or load_rule_settings(config_path)
        self._states: dict[
            tuple[int, ComplianceEventType], _CandidateState
        ] = {}

    def update(self, result: ComplianceResult) -> tuple[ComplianceFinding, ...]:
        """Return newly confirmed findings for one ordered frame."""

        if not isinstance(result, ComplianceResult):
            raise ComplianceInputError(
                "TemporalViolationFilter input must be a ComplianceResult"
            )

        candidates: dict[
            tuple[int, ComplianceEventType], ComplianceFinding
        ] = {
            (finding.track_id, finding.event_type): finding
            for finding in result.candidate_findings
        }

        for key in tuple(self._states):
            if key not in candidates:
                del self._states[key]

        confirmed: list[ComplianceFinding] = []
        for key, finding in candidates.items():
            state = self._states.get(key)
            if state is None:
                state = _CandidateState(
                    first_timestamp=finding.timestamp,
                    last_timestamp=finding.timestamp,
                    confidences=[finding.confidence],
                )
                self._states[key] = state
            else:
                if finding.timestamp < state.last_timestamp:
                    raise ComplianceInputError(
                        "Compliance timestamps must be non-decreasing"
                    )
                state.last_timestamp = finding.timestamp
                state.frame_count += 1
                state.confidences.append(finding.confidence)

            duration = state.last_timestamp - state.first_timestamp
            if (
                not state.confirmed
                and state.frame_count
                >= self.settings.min_consecutive_frames
                and duration >= self.settings.min_duration_seconds
            ):
                state.confirmed = True
                confirmed.append(
                    finding.with_evidence(
                        (
                            f"temporal_frames={state.frame_count}",
                            f"temporal_duration={duration:.6f}",
                        )
                    )
                )

        return tuple(confirmed)

    def reset(self) -> None:
        """Discard all temporal state."""

        self._states.clear()
