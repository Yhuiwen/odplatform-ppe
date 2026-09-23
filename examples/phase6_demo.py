"""Offline Phase 6 compliance-event demo.

The demo consumes project-owned association JSON only. It never imports or
loads Torch, Ultralytics, a checkpoint, a camera or a network stream.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.detection.schemas import BoundingBox, Detection
from core.schemas.association import (
    AssociationMethod,
    AssociationResult,
    AssociationStatus,
    PPEAssociation,
)
from core.schemas.compliance import ComplianceEvent
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult
from infra.storage.json_event_store import JSONEventStore
from services.compliance_service import ComplianceService
from services.event_service import EventService
from utils.paths import PROJECT_ROOT

DEFAULT_FIXTURE = (
    PROJECT_ROOT / "tests" / "fixtures" / "phase6_association_sample.json"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "events.jsonl"


def run_demo(
    fixture_path: str | Path = DEFAULT_FIXTURE,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> tuple[ComplianceEvent, ...]:
    """Run the frozen rule pipeline over one deterministic JSON fixture."""

    frames = _load_frames(Path(fixture_path))
    compliance_service = ComplianceService()
    event_service = EventService(
        store=JSONEventStore(output_path),
    )
    events: list[ComplianceEvent] = []
    for frame in frames:
        result = compliance_service.evaluate(frame)
        events.extend(event_service.process(result))
    return tuple(events)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the offline Phase 6 compliance event demo."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Association-result JSON fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="JSONL event output path.",
    )
    args = parser.parse_args(argv)

    events = run_demo(args.input, args.output)
    print(
        json.dumps(
            {
                "status": "PASS",
                "events_created": len(events),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0


def _load_frames(path: Path) -> tuple[AssociationResult, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read association fixture: {path}") from exc
    if not isinstance(payload, list):
        raise ValueError("Association fixture root must be a JSON array")
    return tuple(_parse_frame(item) for item in payload)


def _parse_frame(payload: Any) -> AssociationResult:
    if not isinstance(payload, dict):
        raise ValueError("Each association frame must be a JSON object")
    frame_id = int(payload["frame_id"])
    timestamp = float(payload["timestamp"])
    source = str(payload["source"])
    tracks = tuple(
        _parse_track(item, frame_id, timestamp, source)
        for item in payload.get("tracks", ())
    )
    track_by_id = {track.track_id: track for track in tracks}
    associations = tuple(
        _parse_association(
            item,
            frame_id,
            timestamp,
            source,
            track_by_id,
        )
        for item in payload.get("associations", ())
    )
    return AssociationResult(
        frame_id=frame_id,
        timestamp=timestamp,
        source=source,
        tracks=tracks,
        associations=associations,
    )


def _parse_track(
    payload: Any,
    frame_id: int,
    timestamp: float,
    source: str,
) -> TrackResult:
    if not isinstance(payload, dict):
        raise ValueError("Each track must be a JSON object")
    detection = _parse_detection(
        payload,
        frame_id=frame_id,
        timestamp=timestamp,
        source=source,
    )
    return TrackResult(track_id=int(payload["track_id"]), detection=detection)


def _parse_association(
    payload: Any,
    frame_id: int,
    timestamp: float,
    source: str,
    track_by_id: dict[int, TrackResult],
) -> PPEAssociation:
    if not isinstance(payload, dict):
        raise ValueError("Each association must be a JSON object")
    status = AssociationStatus(str(payload["status"]))
    track_id = payload.get("track_id")
    person = (
        track_by_id.get(int(track_id)) if track_id is not None else None
    )
    method_value = payload.get("method")
    method = (
        AssociationMethod(str(method_value))
        if method_value is not None
        else None
    )
    return PPEAssociation(
        ppe=_parse_detection(
            payload,
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
        ),
        status=status,
        track_id=int(track_id) if track_id is not None else None,
        person=person,
        method=method,
        containment_ratio=float(payload.get("containment_ratio", 0.0)),
        iou=float(payload.get("iou", 0.0)),
    )


def _parse_detection(
    payload: dict[str, Any],
    *,
    frame_id: int,
    timestamp: float,
    source: str,
) -> DetectionResult:
    bbox_payload = payload["bbox"]
    if not isinstance(bbox_payload, dict):
        raise ValueError("Detection bbox must be a JSON object")
    detection = Detection(
        bbox=BoundingBox(
            x1=float(bbox_payload["x1"]),
            y1=float(bbox_payload["y1"]),
            x2=float(bbox_payload["x2"]),
            y2=float(bbox_payload["y2"]),
        ),
        class_id=int(payload["class_id"]),
        class_name=str(payload["class_name"]),
        confidence=float(payload["confidence"]),
    )
    return DetectionResult(
        frame_id=frame_id,
        timestamp=timestamp,
        source=source,
        detection=detection,
    )


if __name__ == "__main__":
    raise SystemExit(main())
