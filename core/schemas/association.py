"""Phase 5 Person-PPE association output contracts.

The contracts are model-independent. They preserve unknown outcomes explicitly
and do not expose tracker or Ultralytics runtime objects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult

PPE_CLASS_NAMES = frozenset({"hardhat", "no_hardhat", "vest", "no_vest"})

__all__ = [
    "AssociationMethod",
    "AssociationResult",
    "AssociationStatus",
    "PPEAssociation",
    "PPE_CLASS_NAMES",
]


class AssociationStatus(str, Enum):
    """Whether a PPE detection has a defensible person assignment."""

    ASSOCIATED = "associated"
    UNKNOWN = "unknown"


class AssociationMethod(str, Enum):
    """Allowed geometric evidence for an accepted assignment."""

    CONTAINMENT = "containment"
    IOU = "iou"


@dataclass(frozen=True, slots=True)
class PPEAssociation:
    """One PPE detection and its assigned or unknown person track."""

    ppe: DetectionResult
    status: AssociationStatus
    track_id: int | None = None
    person: TrackResult | None = None
    method: AssociationMethod | None = None
    containment_ratio: float = 0.0
    iou: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.ppe, DetectionResult):
            raise TypeError("ppe must be a DetectionResult")
        if self.ppe.class_name not in PPE_CLASS_NAMES:
            raise ValueError("ppe must be a supported PPE class")
        if not isinstance(self.status, AssociationStatus):
            raise TypeError("status must be an AssociationStatus")
        if self.method is not None and not isinstance(
            self.method, AssociationMethod
        ):
            raise TypeError("method must be an AssociationMethod or None")
        for field_name, value in (
            ("containment_ratio", self.containment_ratio),
            ("iou", self.iou),
        ):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{field_name} must be finite and between 0 and 1"
                )

        if self.status is AssociationStatus.ASSOCIATED:
            if self.track_id is None or self.person is None or self.method is None:
                raise ValueError(
                    "associated PPE requires track_id, person and method"
                )
            if not isinstance(self.person, TrackResult):
                raise TypeError("person must be a TrackResult")
            if self.person.track_id != self.track_id:
                raise ValueError("person track_id must match association track_id")
            if (
                self.person.frame_id != self.ppe.frame_id
                or self.person.timestamp != self.ppe.timestamp
                or self.person.source != self.ppe.source
            ):
                raise ValueError("person and PPE frame context must match")
        else:
            if self.track_id is not None or self.person is not None:
                raise ValueError("unknown PPE cannot carry a person assignment")
            if self.method is not None:
                raise ValueError("unknown PPE cannot carry an association method")

    @property
    def frame_id(self) -> int:
        return self.ppe.frame_id

    @property
    def timestamp(self) -> float:
        return self.ppe.timestamp

    @property
    def source(self) -> str:
        return self.ppe.source

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable association record."""

        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "class_id": self.ppe.class_id,
            "class_name": self.ppe.class_name,
            "confidence": self.ppe.confidence,
            "bbox": {
                "x1": self.ppe.bbox.x1,
                "y1": self.ppe.bbox.y1,
                "x2": self.ppe.bbox.x2,
                "y2": self.ppe.bbox.y2,
            },
            "status": self.status.value,
            "track_id": self.track_id,
            "method": self.method.value if self.method is not None else None,
            "containment_ratio": self.containment_ratio,
            "iou": self.iou,
        }


@dataclass(frozen=True, slots=True)
class AssociationResult:
    """Frame-level output for tracking and Person-PPE association."""

    frame_id: int
    timestamp: float
    source: str
    tracks: tuple[TrackResult, ...] = ()
    associations: tuple[PPEAssociation, ...] = ()

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id cannot be negative")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite and non-negative")
        if not self.source:
            raise ValueError("source cannot be empty")

        tracks = tuple(self.tracks)
        track_ids: set[int] = set()
        for track in tracks:
            if not isinstance(track, TrackResult):
                raise TypeError("tracks must contain TrackResult objects")
            if (
                track.frame_id != self.frame_id
                or track.timestamp != self.timestamp
                or track.source != self.source
            ):
                raise ValueError("track frame context must match result context")
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
                or association.source != self.source
            ):
                raise ValueError(
                    "association frame context must match result context"
                )
            if (
                association.track_id is not None
                and association.track_id not in track_ids
            ):
                raise ValueError(
                    "associated track_id must reference a result track"
                )

        object.__setattr__(self, "tracks", tracks)
        object.__setattr__(self, "associations", associations)

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def association_count(self) -> int:
        return len(self.associations)

    @property
    def unknown_count(self) -> int:
        return sum(
            item.status is AssociationStatus.UNKNOWN
            for item in self.associations
        )

    def associations_for_track(self, track_id: int) -> tuple[PPEAssociation, ...]:
        """Return only defensible assignments for one person track."""

        return tuple(
            item for item in self.associations if item.track_id == track_id
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable frame result."""

        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "track_count": self.track_count,
            "association_count": self.association_count,
            "unknown_count": self.unknown_count,
            "tracks": [track.to_dict() for track in self.tracks],
            "associations": [
                association.to_dict() for association in self.associations
            ],
        }
