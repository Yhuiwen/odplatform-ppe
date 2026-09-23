"""Compliance event creation, deduplication and lifecycle."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from core.rules.compliance_engine import (
    ComplianceInputError,
    RuleSettings,
    load_rule_settings,
)
from core.rules.temporal_filter import TemporalViolationFilter
from core.schemas.compliance import (
    ComplianceEvent,
    ComplianceEventType,
    ComplianceResult,
    ComplianceState,
)

__all__ = ["EventEngine"]


class EventEngine:
    """Turn temporally confirmed findings into deduplicated events."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        settings: RuleSettings | None = None,
        temporal_filter: TemporalViolationFilter | None = None,
    ) -> None:
        self.settings = settings or load_rule_settings(config_path)
        self.temporal_filter = temporal_filter or TemporalViolationFilter(
            config_path,
            settings=self.settings,
        )
        self._active: dict[
            tuple[int, ComplianceEventType], str
        ] = {}
        self._recovery_counts: dict[
            tuple[int, ComplianceEventType], int
        ] = {}
        self._last_recovered: dict[
            tuple[int, ComplianceEventType], float
        ] = {}

    def process(self, result: ComplianceResult) -> tuple[ComplianceEvent, ...]:
        """Process one ordered frame and return newly created events only."""

        if not isinstance(result, ComplianceResult):
            raise ComplianceInputError(
                "EventEngine input must be a ComplianceResult"
            )

        confirmed = self.temporal_filter.update(result)
        self._update_recovery_state(result)

        events: list[ComplianceEvent] = []
        for finding in confirmed:
            key = (finding.track_id, finding.event_type)
            if key in self._active:
                continue
            if self._is_cooling_down(key, finding.timestamp):
                continue

            event_id = f"EVT-{uuid4().hex}"
            self._active[key] = event_id
            self._recovery_counts.pop(key, None)
            events.append(
                ComplianceEvent(
                    event_id=event_id,
                    track_id=finding.track_id,
                    event_type=finding.event_type,
                    confidence=finding.confidence,
                    timestamp=finding.timestamp,
                    evidence=finding.evidence,
                )
            )
        return tuple(events)

    def reset(self) -> None:
        """Clear event lifecycle and temporal state."""

        self.temporal_filter.reset()
        self._active.clear()
        self._recovery_counts.clear()
        self._last_recovered.clear()

    def _update_recovery_state(self, result: ComplianceResult) -> None:
        findings = {
            (finding.track_id, finding.event_type): finding
            for finding in result.findings
        }
        for key in tuple(self._active):
            finding = findings.get(key)
            if finding is None or finding.state is not ComplianceState.COMPLIANT:
                self._recovery_counts[key] = 0
                continue

            count = self._recovery_counts.get(key, 0) + 1
            if count < self.settings.recovery_frames:
                self._recovery_counts[key] = count
                continue

            self._active.pop(key, None)
            self._recovery_counts.pop(key, None)
            self._last_recovered[key] = result.timestamp

    def _is_cooling_down(
        self,
        key: tuple[int, ComplianceEventType],
        timestamp: float,
    ) -> bool:
        recovered_at = self._last_recovered.get(key)
        if recovered_at is None:
            return False
        if timestamp - recovered_at < self.settings.cooldown_seconds:
            return True
        self._last_recovered.pop(key, None)
        return False
