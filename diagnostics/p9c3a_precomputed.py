"""Non-production P9-C.3a fixture and inference control."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def detection_template(result: DetectionResult) -> dict:
    return {
        "class_id": result.class_id,
        "class_name": result.class_name,
        "confidence": result.confidence,
        "bbox": {"x1": result.bbox.x1, "y1": result.bbox.y1,
                 "x2": result.bbox.x2, "y2": result.bbox.y2},
    }


def fixture_from_results(*, frames, results_by_frame, source_path: Path,
                         checkpoint_path: Path, config_path: Path,
                         lock_path: Path, generated_at: str, runtime: str) -> dict:
    if len(frames) != 47 or len(results_by_frame) != len(frames):
        raise ValueError("fixture requires all 47 real MP4 frames")
    rows = []
    for ordinal, (frame, results) in enumerate(zip(frames, results_by_frame)):
        if frame.frame_id != ordinal:
            raise ValueError("frame ordinal and frame_id differ")
        rows.append({"ordinal": ordinal, "detections": [detection_template(item) for item in results]})
    return {
        "schema": "p9c3a-real-detections-v1",
        "diagnostic_only": True,
        "source_mp4": str(source_path.resolve()),
        "source_mp4_sha256": sha256(source_path),
        "checkpoint_sha256": sha256(checkpoint_path),
        "inference_config_sha256": sha256(config_path),
        "runtime_lock_sha256": sha256(lock_path),
        "runtime": runtime,
        "generated_at_utc": generated_at,
        "total_frames": len(frames),
        "total_detections": sum(len(row["detections"]) for row in rows),
        "classes": dict(Counter(item["class_name"] for row in rows for item in row["detections"])),
        "frames": rows,
    }


def load_fixture(path: Path, *, expected_mp4_sha256: str,
                 expected_checkpoint_sha256: str,
                 expected_config_sha256: str,
                 expected_lock_sha256: str) -> dict:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "source_mp4_sha256": expected_mp4_sha256,
        "checkpoint_sha256": expected_checkpoint_sha256,
        "inference_config_sha256": expected_config_sha256,
        "runtime_lock_sha256": expected_lock_sha256,
    }
    if fixture.get("schema") != "p9c3a-real-detections-v1" or fixture.get("diagnostic_only") is not True:
        raise ValueError("invalid diagnostic detection fixture schema")
    for key, value in expected.items():
        if fixture.get(key) != value:
            raise ValueError(f"fixture frozen identity mismatch: {key}")
    rows = fixture.get("frames")
    if not isinstance(rows, list) or len(rows) != 47 or fixture.get("total_frames") != 47:
        raise ValueError("fixture must contain exactly 47 frames")
    if [row.get("ordinal") for row in rows] != list(range(47)):
        raise ValueError("fixture ordinals must be contiguous")
    if any(not isinstance(row.get("detections"), list) for row in rows):
        raise ValueError("fixture detections must be lists")
    if sum(len(row["detections"]) for row in rows) != fixture.get("total_detections"):
        raise ValueError("fixture detection count mismatch")
    return fixture


class PrecomputedInferenceService:
    """Rebuild formal DetectionResult with the current frame context."""

    def __init__(self, fixture: dict) -> None:
        self._templates = {row["ordinal"]: row["detections"] for row in fixture["frames"]}

    def infer_frame(self, frame, *, source: str) -> list[DetectionResult]:
        if frame.frame_id not in self._templates:
            raise ValueError(f"fixture has no frame {frame.frame_id}")
        return [DetectionResult(
            frame_id=frame.frame_id, timestamp=frame.timestamp, source=source,
            detection=Detection(
                bbox=BoundingBox(**item["bbox"]),
                class_id=item["class_id"], class_name=item["class_name"],
                confidence=item["confidence"],
            ),
        ) for item in self._templates[frame.frame_id]]

    def close(self) -> None:
        pass
