"""Non-production real-track fixture and current-context tracker control."""

from __future__ import annotations

import json
import math
from pathlib import Path

from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult


def track_template(track: TrackResult, detections: list[DetectionResult]) -> dict:
    index = next((i for i, item in enumerate(detections) if item is track.detection), None)
    if index is None:
        raise ValueError("real track does not reference a current-frame detection")
    return {
        "track_id": track.track_id, "detection_index": index,
        "class_id": track.detection.class_id, "class_name": track.detection.class_name,
        "confidence": track.confidence,
        "bbox": {"x1": track.bbox.x1, "y1": track.bbox.y1,
                 "x2": track.bbox.x2, "y2": track.bbox.y2},
    }


def load_track_fixture(path: Path, *, detection_sha256: str,
                       tracker_config_sha256: str, ultralytics_version: str,
                       lap_version: str) -> dict:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "detection_fixture_sha256": detection_sha256,
        "tracker_config_sha256": tracker_config_sha256,
        "ultralytics_version": ultralytics_version,
        "lap_version": lap_version,
    }
    if fixture.get("schema") != "p9c3b-real-tracks-v1" or fixture.get("diagnostic_only") is not True:
        raise ValueError("invalid real-track diagnostic fixture")
    for key, value in expected.items():
        if fixture.get(key) != value:
            raise ValueError(f"track fixture identity mismatch: {key}")
    frames = fixture.get("frames")
    if not isinstance(frames, list) or len(frames) != 47 or fixture.get("total_frames") != 47:
        raise ValueError("track fixture must contain 47 frames")
    if [row.get("ordinal") for row in frames] != list(range(47)):
        raise ValueError("track fixture ordinals must be contiguous")
    if any(not isinstance(row.get("tracks"), list) for row in frames):
        raise ValueError("track fixture tracks must be lists")
    if sum(len(row["tracks"]) for row in frames) != fixture.get("total_tracks"):
        raise ValueError("track fixture total count mismatch")
    return fixture


class PrecomputedTrackingAdapter:
    """Rebuild formal tracks from current detections; never invoke BYTETracker."""

    def __init__(self, fixture: dict) -> None:
        self._frames = tuple(fixture["frames"])
        self._cursor = 0
        self._session_count = 0

    def reset(self) -> None:
        self._cursor = 0
        self._session_count += 1

    def update(self, detections, *, frame_id: int, timestamp: float,
               source: str) -> tuple[TrackResult, ...]:
        if self._session_count < 1 or frame_id != self._cursor or not 0 <= frame_id < len(self._frames):
            raise ValueError(f"diagnostic track cursor mismatch: {frame_id}")
        current = tuple(detections)
        if any(not isinstance(item, DetectionResult) or item.frame_id != frame_id
               or item.timestamp != timestamp or item.source != source for item in current):
            raise ValueError("diagnostic track detection context mismatch")
        result = []
        for template in self._frames[frame_id]["tracks"]:
            index = template["detection_index"]
            if not isinstance(index, int) or not 0 <= index < len(current):
                raise ValueError("diagnostic track detection index invalid")
            detection = current[index]
            if detection.class_id != template["class_id"] or detection.class_name != template["class_name"]:
                raise ValueError("diagnostic track class mismatch")
            if not math.isclose(detection.confidence, template["confidence"], abs_tol=1e-6):
                raise ValueError("diagnostic track confidence mismatch")
            if any(not math.isclose(getattr(detection.bbox, key), template["bbox"][key], abs_tol=1e-5)
                   for key in ("x1", "y1", "x2", "y2")):
                raise ValueError("diagnostic track bbox mismatch")
            result.append(TrackResult(track_id=template["track_id"], detection=detection))
        self._cursor += 1
        return tuple(result)
