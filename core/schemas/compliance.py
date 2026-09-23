"""Phase 6 PPE compliance and event contracts.

These schemas are model-independent. They contain no detector, tracker,
Ultralytics, Torch or storage implementation details.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from core.schemas.association import AssociationResult, PPEAssociation
from core.schemas.tracking import TrackResult

__all__ = [
    "ComplianceEvent",
    "ComplianceEventType",
    "ComplianceFinding",
    "ComplianceInput",
    "ComplianceResult",
    "ComplianceState",
]


class ComplianceEventType(str, Enum):
    """Frozen event vocabulary for Phase 6."""

    NO_HELMET = "NO_HELMET"
    NO_VEST = "NO_VEST"
    PPE_UNKNOWN = "PPE_UNKNOWN"


class ComplianceState(str, Enum):
    """Outcome of one rule/domain evaluation for one person track."""

    COMPLIANT = "compliant"
    VIOLATION = "violation"
    UNKNOWN = "unknown"


def _normalize_evidence(evidence: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(str(item) for item in evidence)
    if any(not item for item in normalized):
        raise ValueError("evidence entries cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class ComplianceInput:
    """Frame-level input adapted from one Phase 5 ``AssociationResult``."""

    frame_id: int
    timestamp: float
    tracks: tuple[TrackResult, ...] = ()
    associations: tuple[PPEAssociation, ...] = ()

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id cannot be negative")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite and non-negative")

        tracks = tuple(self.tracks)
        track_ids: set[int] = set()
        for track in tracks:
            if not isinstance(track, TrackResult):
                raise TypeError("tracks must contain TrackResult objects")
            if (
                track.frame_id != self.frame_id
                or track.timestamp != self.timestamp
            ):
                raise ValueError("track frame context must match compliance input")
            if track.track_id in track_ids:
                raise ValueError("track IDs must be unique within one frame")
            track_ids.add(track.track_id)

        associations = tuple(self.associations)
        for association in associations:
            if not isinstance(association, PPEAssociation):
                raise TypeError(
                    "associations must contain PPEAssociation objects"
                )
            if (
                association.frame_id != self.frame_id
                or association.timestamp != self.timestamp
            ):
                raise ValueError(
                    "association frame context must match compliance input"
                )
            if (
                association.track_id is not None
                and association.track_id not in track_ids
            ):
                raise ValueError(
                    "associated track_id must reference an input track"
                )

        object.__setattr__(self, "tracks", tracks)
        object.__setattr__(self, "associations", associations)

    @classmethod
    def from_association_result(
        cls, result: AssociationResult
    ) -> "ComplianceInput":
        """Create a stable copy of one frozen Phase 5 frame result."""

        if not isinstance(result, AssociationResult):
            raise TypeError("result must be an AssociationResult")
        return cls(
            frame_id=result.frame_id,
            timestamp=result.timestamp,
            tracks=result.tracks,
            associations=result.associations,
        )

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def association_count(self) -> int:
        return len(self.associations)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable contract representation."""

        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "tracks": [track.to_dict() for track in self.tracks],
            "associations": [
                association.to_dict() for association in self.associations
            ],
        }


@dataclass(frozen=True, slots=True)
class ComplianceFinding:
    """One rule-domain observation for one person track in one frame."""

    track_id: int
    event_type: ComplianceEventType
    state: ComplianceState
    confidence: float
    timestamp: float
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.track_id < 0:
            raise ValueError("track_id cannot be negative")
        if not isinstance(self.event_type, ComplianceEventType):
            raise TypeError("event_type must be a ComplianceEventType")
        if not isinstance(self.state, ComplianceState):
            raise TypeError("state must be a ComplianceState")
        if (
            self.confidence < 0.0
            or self.confidence > 1.0
            or not math.isfinite(self.confidence)
        ):
            raise ValueError("confidence must be finite and between 0 and 1")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite and non-negative")

        if self.event_type is ComplianceEventType.PPE_UNKNOWN:
            if self.state is not ComplianceState.UNKNOWN:
                raise ValueError("PPE_UNKNOWN findings must use unknown state")

        object.__setattr__(
            self, "evidence", _normalize_evidence(self.evidence)
        )

    @property
    def is_candidate(self) -> bool:
        """Return whether this finding is eligible for temporal confirmation."""

        return self.state is not ComplianceState.COMPLIANT

    def with_evidence(
        self, additional_evidence: Iterable[str]
    ) -> "ComplianceFinding":
        """Return a copy with additional deterministic evidence labels."""

        return ComplianceFinding(
            track_id=self.track_id,
            event_type=self.event_type,
            state=self.state,
            confidence=self.confidence,
            timestamp=self.timestamp,
            evidence=self.evidence
            + _normalize_evidence(additional_evidence),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable finding representation."""

        return {
            "track_id": self.track_id,
            "event_type": self.event_type.value,
            "state": self.state.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class ComplianceResult:
    """All compliance findings produced for one frame."""

    frame_id: int
    timestamp: float
    findings: tuple[ComplianceFinding, ...] = ()

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id cannot be negative")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite and non-negative")

        findings = tuple(self.findings)
        keys: set[tuple[int, ComplianceEventType]] = set()
        for finding in findings:
            if not isinstance(finding, ComplianceFinding):
                raise TypeError(
                    "findings must contain ComplianceFinding objects"
                )
            if finding.timestamp != self.timestamp:
                raise ValueError(
                    "finding timestamp must match its frame result"
                )
            key = (finding.track_id, finding.event_type)
            if key in keys:
                raise ValueError(
                    "a track/event_type can appear only once per frame"
                )
            keys.add(key)

        object.__setattr__(self, "findings", findings)

    @property
    def candidate_findings(self) -> tuple[ComplianceFinding, ...]:
        return tuple(finding for finding in self.findings if finding.is_candidate)

    @property
    def compliant_findings(self) -> tuple[ComplianceFinding, ...]:
        return tuple(
            finding
            for finding in self.findings
            if finding.state is ComplianceState.COMPLIANT
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable result representation."""

        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True, slots=True)
class ComplianceEvent:
    """One deduplicated compliance event confirmed over multiple frames."""

    event_id: str
    track_id: int
    event_type: ComplianceEventType
    confidence: float
    timestamp: float
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if self.track_id < 0:
            raise ValueError("track_id cannot be negative")
        if not isinstance(self.event_type, ComplianceEventType):
            raise TypeError("event_type must be a ComplianceEventType")
        if (
            self.confidence < 0.0
            or self.confidence > 1.0
            or not math.isfinite(self.confidence)
        ):
            raise ValueError("confidence must be finite and between 0 and 1")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite and non-negative")
        object.__setattr__(
            self, "evidence", _normalize_evidence(self.evidence)
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the frozen four-field JSONL wire contract."""

        return {
            "type": self.event_type.value,
            "track_id": self.track_id,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }

    def to_full_dict(self) -> dict[str, Any]:
        """Return the complete event representation for diagnostics."""

        return {
            **self.to_dict(),
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "evidence": list(self.evidence),
        }
