"""Person-PPE association adapter.

The adapter consumes only project-owned schemas. It never modifies a person
track or synthesizes a PPE detection, and uncertain ownership remains
explicitly ``unknown``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from core.detection.schemas import BoundingBox
from core.schemas.association import (
    AssociationMethod,
    AssociationResult,
    AssociationStatus,
    PPEAssociation,
)
from core.schemas.detection import DetectionResult
from core.schemas.tracking import PERSON_CLASS_ID, TrackResult
from utils.config_loader import load_config


class AssociationError(RuntimeError):
    """Base association error with a stable machine-readable code."""

    code = "association_error"


class AssociationConfigurationError(AssociationError):
    code = "invalid_association_configuration"


class AssociationExecutionDisabledError(AssociationError):
    code = "execution_disabled"


class InvalidAssociationClassError(AssociationError):
    code = "invalid_association_class"


class AssociationFrameContextError(AssociationError):
    code = "invalid_frame_context"


class AssociationInputError(AssociationError):
    code = "invalid_association_input"


@dataclass(frozen=True, slots=True)
class AssociationSettings:
    """Frozen association policy parsed from ``configs/association.yaml``."""

    person_class_id: int
    ppe_class_ids: tuple[int, ...]
    ppe_class_names: tuple[str, ...]
    min_detection_confidence: float
    min_containment_ratio: float
    min_iou: float
    ambiguity_margin: float
    allow_nearest_distance: bool
    max_assignments_per_ppe: int


@dataclass(frozen=True, slots=True)
class _AssociationCandidate:
    track: TrackResult
    method: AssociationMethod
    containment_ratio: float
    iou: float
    method_priority: int
    primary_score: float

    @property
    def rank_key(self) -> tuple[float, ...]:
        """Return a deterministic descending-priority ranking key."""

        return (
            float(self.method_priority),
            -self.primary_score,
            -self.containment_ratio,
            -self.iou,
            -self.track.confidence,
            float(self.track.track_id),
        )


__all__ = [
    "AssociationConfigurationError",
    "AssociationError",
    "AssociationExecutionDisabledError",
    "AssociationFrameContextError",
    "AssociationInputError",
    "AssociationSettings",
    "InvalidAssociationClassError",
    "PPEPersonAssociationAdapter",
]


class PPEPersonAssociationAdapter:
    """Associate PPE detections with existing person tracks conservatively."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        execution_enabled: bool | None = None,
    ) -> None:
        config = load_config(config_path or "association")
        association = config.get("association")
        if not isinstance(association, dict):
            raise AssociationConfigurationError(
                "Association configuration requires an 'association' mapping"
            )

        self._execution_enabled = (
            bool(association.get("execution_enabled", False))
            if execution_enabled is None
            else bool(execution_enabled)
        )
        self._settings = self._parse_settings(association)

    @property
    def settings(self) -> AssociationSettings:
        return self._settings

    def associate(
        self,
        tracks: Sequence[TrackResult],
        ppe_detections: Sequence[DetectionResult],
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> AssociationResult:
        """Return one associated or explicit unknown record per PPE detection."""

        self._ensure_execution_enabled()
        self._validate_frame_context(
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
        )

        normalized_tracks = self._validate_tracks(
            tracks,
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
        )
        associations = tuple(
            self._associate_ppe(
                ppe,
                normalized_tracks,
                frame_id=frame_id,
                timestamp=timestamp,
                source=source,
            )
            for ppe in ppe_detections
        )
        return AssociationResult(
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
            tracks=normalized_tracks,
            associations=associations,
        )

    def _associate_ppe(
        self,
        ppe: DetectionResult,
        tracks: tuple[TrackResult, ...],
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> PPEAssociation:
        self._validate_ppe_detection(
            ppe,
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
        )

        candidates: list[_AssociationCandidate] = []
        measured_candidates: list[tuple[float, float, TrackResult]] = []
        for track in tracks:
            containment_ratio, iou = self._measure_pair(ppe.bbox, track.bbox)
            measured_candidates.append((containment_ratio, iou, track))
            if track.confidence < self._settings.min_detection_confidence:
                continue
            candidate = self._build_candidate(
                track,
                containment_ratio=containment_ratio,
                iou=iou,
            )
            if candidate is not None:
                candidates.append(candidate)

        if ppe.confidence < self._settings.min_detection_confidence:
            return self._unknown_association(ppe)

        if not candidates:
            containment_ratio, iou = self._best_measured_geometry(
                measured_candidates
            )
            return self._unknown_association(
                ppe,
                containment_ratio=containment_ratio,
                iou=iou,
            )

        ranked = sorted(candidates, key=lambda candidate: candidate.rank_key)
        winner = ranked[0]
        if (
            len(ranked) > 1
            and ranked[1].method_priority == winner.method_priority
            and winner.primary_score - ranked[1].primary_score
            < self._settings.ambiguity_margin
        ):
            return self._unknown_association(
                ppe,
                containment_ratio=winner.containment_ratio,
                iou=winner.iou,
            )

        return PPEAssociation(
            ppe=ppe,
            status=AssociationStatus.ASSOCIATED,
            track_id=winner.track.track_id,
            person=winner.track,
            method=winner.method,
            containment_ratio=winner.containment_ratio,
            iou=winner.iou,
        )

    def _build_candidate(
        self,
        track: TrackResult,
        *,
        containment_ratio: float,
        iou: float,
    ) -> _AssociationCandidate | None:
        if containment_ratio >= self._settings.min_containment_ratio:
            return _AssociationCandidate(
                track=track,
                method=AssociationMethod.CONTAINMENT,
                containment_ratio=containment_ratio,
                iou=iou,
                method_priority=0,
                primary_score=containment_ratio,
            )
        if iou >= self._settings.min_iou:
            return _AssociationCandidate(
                track=track,
                method=AssociationMethod.IOU,
                containment_ratio=containment_ratio,
                iou=iou,
                method_priority=1,
                primary_score=iou,
            )
        return None

    @staticmethod
    def _measure_pair(
        ppe_bbox: BoundingBox,
        person_bbox: BoundingBox,
    ) -> tuple[float, float]:
        intersection_width = max(
            0.0,
            min(ppe_bbox.x2, person_bbox.x2)
            - max(ppe_bbox.x1, person_bbox.x1),
        )
        intersection_height = max(
            0.0,
            min(ppe_bbox.y2, person_bbox.y2)
            - max(ppe_bbox.y1, person_bbox.y1),
        )
        intersection_area = intersection_width * intersection_height
        containment_ratio = intersection_area / ppe_bbox.area
        union_area = ppe_bbox.area + person_bbox.area - intersection_area
        iou = intersection_area / union_area if union_area > 0 else 0.0
        return containment_ratio, iou

    @staticmethod
    def _best_measured_geometry(
        measured_candidates: Sequence[tuple[float, float, TrackResult]],
    ) -> tuple[float, float]:
        if not measured_candidates:
            return 0.0, 0.0
        containment_ratio, iou, _ = max(
            measured_candidates,
            key=lambda item: (
                item[0],
                item[1],
                item[2].confidence,
                -item[2].track_id,
            ),
        )
        return containment_ratio, iou

    @staticmethod
    def _unknown_association(
        ppe: DetectionResult,
        *,
        containment_ratio: float = 0.0,
        iou: float = 0.0,
    ) -> PPEAssociation:
        return PPEAssociation(
            ppe=ppe,
            status=AssociationStatus.UNKNOWN,
            containment_ratio=containment_ratio,
            iou=iou,
        )

    def _validate_tracks(
        self,
        tracks: Sequence[TrackResult],
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> tuple[TrackResult, ...]:
        normalized: list[TrackResult] = []
        track_ids: set[int] = set()
        for track in tracks:
            if not isinstance(track, TrackResult):
                raise AssociationInputError(
                    "tracks must contain TrackResult objects"
                )
            if track.track_id in track_ids:
                raise AssociationInputError(
                    "track IDs must be unique within one frame"
                )
            if (
                track.frame_id != frame_id
                or track.timestamp != timestamp
                or track.source != source
            ):
                raise AssociationFrameContextError(
                    "Track frame context does not match association input"
                )
            track_ids.add(track.track_id)
            normalized.append(track)
        return tuple(normalized)

    def _validate_ppe_detection(
        self,
        ppe: DetectionResult,
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> None:
        if not isinstance(ppe, DetectionResult):
            raise AssociationInputError(
                "ppe_detections must contain DetectionResult objects"
            )
        if (
            ppe.frame_id != frame_id
            or ppe.timestamp != timestamp
            or ppe.source != source
        ):
            raise AssociationFrameContextError(
                "PPE frame context does not match association input"
            )
        expected_name = self._expected_ppe_class_name(ppe.class_id)
        if expected_name is None or expected_name != ppe.class_name:
            raise InvalidAssociationClassError(
                "PPE detections must use the frozen class mapping "
                "1=hardhat, 2=no_hardhat, 3=vest, 4=no_vest"
            )

    def _expected_ppe_class_name(self, class_id: int) -> str | None:
        try:
            index = self._settings.ppe_class_ids.index(class_id)
        except ValueError:
            return None
        return self._settings.ppe_class_names[index]

    def _ensure_execution_enabled(self) -> None:
        if not self._execution_enabled:
            raise AssociationExecutionDisabledError(
                "Person-PPE association is disabled by configs/association.yaml"
            )

    @staticmethod
    def _validate_frame_context(
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> None:
        if frame_id < 0:
            raise AssociationFrameContextError("frame_id cannot be negative")
        if timestamp < 0 or not math.isfinite(timestamp):
            raise AssociationFrameContextError(
                "timestamp must be finite and non-negative"
            )
        if not source:
            raise AssociationFrameContextError("source cannot be empty")

    @staticmethod
    def _parse_settings(association: dict[str, Any]) -> AssociationSettings:
        input_config = association.get("input")
        thresholds = association.get("thresholds")
        selection = association.get("selection")
        if not all(
            isinstance(value, dict)
            for value in (input_config, thresholds, selection)
        ):
            raise AssociationConfigurationError(
                "Association configuration requires input, thresholds and "
                "selection mappings"
            )

        try:
            ppe_classes = input_config["ppe_classes"]
            if not isinstance(ppe_classes, dict):
                raise TypeError("ppe_classes must be a mapping")
            class_items = tuple(
                (str(name), int(class_id))
                for name, class_id in ppe_classes.items()
            )
            expected_class_items = (
                ("hardhat", 1),
                ("no_hardhat", 2),
                ("vest", 3),
                ("no_vest", 4),
            )
            if tuple(sorted(class_items)) != tuple(
                sorted(expected_class_items)
            ):
                raise ValueError("PPE class mapping is not frozen")

            priority = selection["priority"]
            if tuple(priority) != ("containment", "iou"):
                raise ValueError("selection priority is not frozen")
            allow_nearest_distance = bool(
                selection["allow_nearest_distance"]
            )
            if allow_nearest_distance:
                raise ValueError("nearest-distance assignment is prohibited")
            max_assignments_per_ppe = int(
                selection["max_assignments_per_ppe"]
            )
            if max_assignments_per_ppe != 1:
                raise ValueError("max_assignments_per_ppe must be 1")

            settings = AssociationSettings(
                person_class_id=int(input_config["person_class_id"]),
                ppe_class_ids=tuple(
                    class_id for _, class_id in class_items
                ),
                ppe_class_names=tuple(
                    class_name for class_name, _ in class_items
                ),
                min_detection_confidence=float(
                    thresholds["min_detection_confidence"]
                ),
                min_containment_ratio=float(
                    thresholds["min_containment_ratio"]
                ),
                min_iou=float(thresholds["min_iou"]),
                ambiguity_margin=float(thresholds["ambiguity_margin"]),
                allow_nearest_distance=allow_nearest_distance,
                max_assignments_per_ppe=max_assignments_per_ppe,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AssociationConfigurationError(
                "Association configuration contains invalid or missing fields"
            ) from exc

        if settings.person_class_id != PERSON_CLASS_ID:
            raise AssociationConfigurationError(
                "Frozen association policy must use person class_id=0"
            )
        if settings.ppe_class_names != (
            "hardhat",
            "no_hardhat",
            "vest",
            "no_vest",
        ):
            raise AssociationConfigurationError(
                "Frozen association policy must preserve PPE class order"
            )
        for field_name, value in (
            ("min_detection_confidence", settings.min_detection_confidence),
            ("min_containment_ratio", settings.min_containment_ratio),
            ("min_iou", settings.min_iou),
            ("ambiguity_margin", settings.ambiguity_margin),
        ):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise AssociationConfigurationError(
                    f"{field_name} must be finite and between 0 and 1"
                )
        return settings
