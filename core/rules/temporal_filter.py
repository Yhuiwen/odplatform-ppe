"""Multi-frame confirmation for compliance candidates."""

from __future__ import annotations

from collections import deque
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
    ComplianceState,
)

__all__ = ["TemporalViolationFilter"]


@dataclass(slots=True)
class _CandidateState:
    first_timestamp: float
    last_timestamp: float
    frame_count: int = 1
    confidences: list[float] = field(default_factory=list)
    confirmed: bool = False


@dataclass(slots=True)
class _VestEvidenceState:
    observations: deque[tuple[float, ComplianceState]] = field(default_factory=deque)
    confirmed: bool = False
    last_timestamp: float = 0.0


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
        self._vest_states: dict[int, _VestEvidenceState] = {}
        # ADR P9-D-001: bounded, track-scoped vest evidence resilience.
        self._vest_window_seconds = 1.5
        self._vest_min_violation_ratio = 0.60

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
            if finding.event_type is not ComplianceEventType.NO_VEST
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

        confirmed.extend(self._update_vest(result))
        return tuple(confirmed)

    def _update_vest(self, result: ComplianceResult) -> tuple[ComplianceFinding, ...]:
        """Confirm persistent vest violations despite brief conflicting evidence."""

        observations: dict[int, tuple[ComplianceState, ComplianceFinding | None]] = {}
        for finding in result.findings:
            if finding.event_type is ComplianceEventType.NO_VEST:
                observations[finding.track_id] = (finding.state, finding)
            elif (
                finding.event_type is ComplianceEventType.PPE_UNKNOWN
                and any(item.startswith("vest=") for item in finding.evidence)
                and finding.track_id not in observations
            ):
                observations[finding.track_id] = (ComplianceState.UNKNOWN, None)

        for track_id in tuple(self._vest_states):
            if track_id not in observations:
                del self._vest_states[track_id]

        confirmed: list[ComplianceFinding] = []
        for track_id, (observation, finding) in observations.items():
            state = self._vest_states.setdefault(track_id, _VestEvidenceState())
            if result.timestamp < state.last_timestamp:
                raise ComplianceInputError(
                    "Compliance timestamps must be non-decreasing"
                )
            state.last_timestamp = result.timestamp
            state.observations.append((result.timestamp, observation))
            while (
                state.observations
                and result.timestamp - state.observations[0][0] > self._vest_window_seconds
            ):
                state.observations.popleft()

            if observation is ComplianceState.COMPLIANT and self._last_n_compliant(
                state.observations, self.settings.recovery_frames
            ):
                state.observations.clear()
                state.confirmed = False
                continue
            if state.confirmed or observation is not ComplianceState.VIOLATION:
                continue

            violation_times = [
                timestamp
                for timestamp, value in state.observations
                if value is ComplianceState.VIOLATION
            ]
            if not violation_times or finding is None:
                continue
            longest_run = 0
            current_run = 0
            for _, value in state.observations:
                current_run = (
                    current_run + 1
                    if value is ComplianceState.VIOLATION
                    else 0
                )
                longest_run = max(longest_run, current_run)
            duration = violation_times[-1] - violation_times[0]
            ratio = len(violation_times) / len(state.observations)
            if (
                longest_run >= self.settings.min_consecutive_frames
                and duration >= self.settings.min_duration_seconds
                and ratio >= self._vest_min_violation_ratio
            ):
                state.confirmed = True
                confirmed.append(
                    finding.with_evidence(
                        (
                            f"temporal_frames={len(violation_times)}",
                            f"temporal_duration={duration:.6f}",
                            f"vest_evidence_ratio={ratio:.3f}",
                        )
                    )
                )
        return tuple(confirmed)

    @staticmethod
    def _last_n_compliant(
        observations: deque[tuple[float, ComplianceState]], count: int
    ) -> bool:
        return len(observations) >= count and all(
            value is ComplianceState.COMPLIANT
            for _, value in list(observations)[-count:]
        )

    def reset(self) -> None:
        """Discard all temporal state."""

        self._states.clear()
        self._vest_states.clear()
