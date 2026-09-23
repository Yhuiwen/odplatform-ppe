"""Run the Phase 7 offline runtime smoke path and write local evidence.

This script only composes existing Phase 4 through Phase 7 boundaries. It does
not modify model, data, inference, tracking, association, compliance or event
wire contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.events.event_engine import EventEngine
from core.schemas.video import SourceState
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from core.video.mp4_source import MP4VideoSource
from core.video.usb_camera_source import USBCameraSource
from core.video.video_source import VideoSourceError
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.json_event_store import JSONEventStore
from infra.storage.snapshot_storage import SnapshotStorage
from services.alert_service import AlertService
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService
from services.event_query_service import EventQueryService
from services.event_service import EventService
from services.inference_service import InferenceService
from services.snapshot_service import SnapshotService
from utils.paths import PROJECT_ROOT

__all__ = ["main", "run_runtime_validation"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def _bbox_dict(bbox: Any) -> dict[str, float]:
    return {
        "x1": float(bbox.x1),
        "y1": float(bbox.y1),
        "x2": float(bbox.x2),
        "y2": float(bbox.y2),
    }


class _ValidationCapture:
    """Small deterministic capture used only for source lifecycle validation."""

    def __init__(self) -> None:
        self.released = False
        self._read_count = 0

    def isOpened(self) -> bool:
        return True

    def get(self, code: int) -> float:
        return {3: 640.0, 4: 480.0, 5: 25.0}.get(code, 0.0)

    def set(self, code: int, value: float) -> None:
        return None

    def read(self) -> tuple[bool, object | None]:
        self._read_count += 1
        if self._read_count == 1:
            return True, object()
        return False, None

    def release(self) -> None:
        self.released = True


def _camera_validation(device_index: int) -> dict[str, Any]:
    real_attempt: dict[str, Any] = {
        "device_index": device_index,
        "attempted": True,
        "metadata": None,
        "open": "FAILED",
        "read": "NOT_RUN",
        "close": "NOT_RUN",
        "error_code": None,
        "error_message": None,
        "final_state": None,
    }
    real_source = USBCameraSource(device_index)
    try:
        metadata = real_source.open()
        real_attempt["metadata"] = metadata.to_dict()
        real_attempt["open"] = "PASS"
        frame = real_source.read()
        real_attempt["read"] = "PASS" if frame is not None else "FAILED"
    except VideoSourceError as exc:
        real_attempt["error_code"] = exc.code
        real_attempt["error_message"] = str(exc)
    except Exception as exc:
        real_attempt["error_code"] = "UNEXPECTED_CAMERA_ERROR"
        real_attempt["error_message"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            real_source.close()
            real_attempt["close"] = "PASS"
        except Exception as exc:
            real_attempt["close"] = "FAILED"
            real_attempt["error_message"] = (
                real_attempt["error_message"]
                or f"{type(exc).__name__}: {exc}"
            )
        real_attempt["final_state"] = real_source.status().state.value

    capture = _ValidationCapture()
    lifecycle: dict[str, Any] = {
        "open": "NOT_RUN",
        "read_frame_id": None,
        "second_read": "NOT_RUN",
        "error_code": None,
        "release": "NOT_RUN",
        "final_state": None,
    }
    source = USBCameraSource(
        device_index,
        capture_factory=lambda _: capture,
    )
    try:
        metadata = source.open()
        lifecycle["open"] = metadata.source_type.value
        frame = source.read()
        lifecycle["read_frame_id"] = (
            None if frame is None else frame.frame_id
        )
        try:
            source.read()
        except VideoSourceError as exc:
            lifecycle["second_read"] = "OBSERVABLE_FAILURE"
            lifecycle["error_code"] = exc.code
    except Exception as exc:
        lifecycle["open"] = "FAILED"
        lifecycle["error_code"] = getattr(exc, "code", type(exc).__name__)
    finally:
        try:
            source.close()
            lifecycle["release"] = "PASS" if capture.released else "FAILED"
        except Exception:
            lifecycle["release"] = "FAILED"
        lifecycle["final_state"] = source.status().state.value

    return {
        "real_usb_attempt": real_attempt,
        "synthetic_usb_lifecycle": lifecycle,
        "status": (
            "PASS"
            if lifecycle["open"] == "usb_camera"
            and lifecycle["read_frame_id"] == 0
            and lifecycle["second_read"] == "OBSERVABLE_FAILURE"
            and lifecycle["release"] == "PASS"
            else "FAILED"
        ),
    }


def _runtime_fingerprint() -> dict[str, Any]:
    import cv2
    import numpy
    import torch
    import torchvision
    import ultralytics

    return {
        "os": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "torch_cuda_build": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_policy": "cpu_only",
        "ultralytics": ultralytics.__version__,
        "opencv": cv2.__version__,
        "numpy": numpy.__version__,
        "streamlit": _package_version("streamlit"),
        "pandas": _package_version("pandas"),
        "lap": _package_version("lap"),
    }


def run_runtime_validation(
    *,
    video: str | Path,
    output_dir: str | Path,
    camera_index: int = 0,
    max_frames: int | None = None,
) -> dict[str, Any]:
    """Execute one full offline Phase 7 runtime smoke pass."""

    started_at = _utc_now()
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(output_dir).expanduser().resolve()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    video_path = Path(video).expanduser().resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"video does not exist: {video_path}")
    if max_frames is not None and max_frames <= 0:
        raise ValueError("max_frames must be positive or None")

    database_path = run_root / "runtime_validation.sqlite3"
    jsonl_path = run_root / "events.jsonl"
    snapshot_root = run_root / "snapshots"
    console_path = run_root / "console_alerts.jsonl"

    database = Database(database_path)
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    storage = SnapshotStorage(snapshot_root)
    ingest_service = EventIngestService(event_repository)
    snapshot_service = SnapshotService(
        event_repository,
        snapshot_repository,
        storage,
    )
    query_service = EventQueryService(
        event_repository,
        snapshot_repository,
        storage,
    )

    console_lines: list[str] = []
    published_alerts: list[str] = []
    console_adapter = ConsoleAlertAdapter(sink=console_lines.append)
    web_adapter = WebAlertAdapter(publisher=lambda item: published_alerts.append(item.event_id))
    alert_service = AlertService((console_adapter, web_adapter))

    inference_service = InferenceService(
        config_path="configs/inference.yaml",
        execution_enabled=True,
    )
    tracker = ByteTrackPersonTrackingAdapter()
    association_adapter = PPEPersonAssociationAdapter()
    compliance_service = ComplianceService()
    event_engine = EventEngine()
    event_service = EventService(
        engine=event_engine,
        store=JSONEventStore(jsonl_path),
    )

    source = MP4VideoSource(video_path)
    source_metadata = source.open()
    source_label = source_metadata.source_id
    frame_count = 0
    frames_with_detections = 0
    total_detections = 0
    class_counts: Counter[str] = Counter()
    track_updates = 0
    association_updates = 0
    unknown_associations = 0
    compliance_findings = 0
    generated_events: list[dict[str, Any]] = []
    runtime_errors: list[dict[str, str]] = []
    started = time.perf_counter()

    try:
        while True:
            if max_frames is not None and frame_count >= max_frames:
                break
            frame = source.read()
            if frame is None:
                break
            frame_count += 1

            detections = inference_service.infer_frame(
                frame,
                source=source_label,
            )
            total_detections += len(detections)
            if detections:
                frames_with_detections += 1
            class_counts.update(item.class_name for item in detections)

            people = [
                item
                for item in detections
                if item.class_id == 0 and item.class_name == "person"
            ]
            ppe = [
                item
                for item in detections
                if item.class_id in {1, 2, 3, 4}
            ]
            tracks = tracker.update(
                people,
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                source=source_label,
            )
            association = association_adapter.associate(
                tracks,
                ppe,
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                source=source_label,
            )
            compliance = compliance_service.evaluate(association)
            new_events = event_service.process(compliance)

            track_updates += len(tracks)
            association_updates += len(association.associations)
            unknown_associations += association.unknown_count
            compliance_findings += len(compliance.findings)

            for event in new_events:
                track = next(
                    (
                        item
                        for item in tracks
                        if item.track_id == event.track_id
                    ),
                    None,
                )
                persisted = ingest_service.ingest(
                    event,
                    source=source_label,
                    frame_id=frame.frame_id,
                    bbox=None if track is None else _bbox_dict(track.bbox),
                )
                snapshot = snapshot_service.capture(
                    event.event_id,
                    frame.image,
                )
                persisted = event_repository.get(event.event_id)
                if persisted is None:
                    raise RuntimeError(
                        f"persisted event disappeared: {event.event_id}"
                    )
                alert_results = alert_service.dispatch_event(persisted)
                generated_events.append(
                    {
                        "event_id": event.event_id,
                        "type": event.event_type.value,
                        "track_id": event.track_id,
                        "confidence": event.confidence,
                        "source_timestamp": event.timestamp,
                        "frame_id": frame.frame_id,
                        "persisted_id": persisted.id,
                        "snapshot": snapshot.relative_path,
                        "snapshot_sha256": snapshot.sha256,
                        "alerts": [
                            result.to_dict() for result in alert_results
                        ],
                    }
                )
    except Exception as exc:
        runtime_errors.append(
            {
                "type": type(exc).__name__,
                "message": str(exc),
                "code": str(getattr(exc, "code", "")),
            }
        )
    finally:
        try:
            source.close()
        except Exception as exc:
            runtime_errors.append(
                {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "code": str(getattr(exc, "code", "")),
                }
            )

    elapsed = time.perf_counter() - started
    source_status = source.status().to_dict()
    statistics = query_service.statistics()
    event_page = query_service.list_events(limit=1000)
    snapshot_events = query_service.snapshot_events()
    evidence_checks = [
        query_service.evidence(event.id)
        for event in snapshot_events
    ]
    verified_evidence = sum(
        view is not None and view.verified
        for view in evidence_checks
    )
    console_path.write_text(
        "".join(f"{line}\n" for line in console_lines),
        encoding="utf-8",
    )

    completed_at = _utc_now()
    checkpoint = PROJECT_ROOT / "models" / "checkpoints" / "EXP-001" / "best.pt"
    inference_config = PROJECT_ROOT / "configs" / "inference.yaml"
    generated_count = len(generated_events)
    persisted_count = event_page.total_count
    complete = (
        not runtime_errors
        and frame_count > 0
        and generated_count > 0
        and persisted_count == generated_count
        and len(snapshot_events) == generated_count
        and verified_evidence == generated_count
        and all(
            all(result["status"] == "delivered" for result in event["alerts"])
            for event in generated_events
        )
    )

    result: dict[str, Any] = {
        "validation_id": "P7-5",
        "run_id": run_id,
        "status": "PASS" if complete else "FAILED",
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "completed_at": completed_at.isoformat().replace("+00:00", "Z"),
        "runtime": _runtime_fingerprint(),
        "identities": {
            "checkpoint": _relative(checkpoint),
            "checkpoint_sha256": _sha256(checkpoint),
            "inference_config": _relative(inference_config),
            "inference_config_sha256": _sha256(inference_config),
            "video": _relative(video_path),
            "video_sha256": _sha256(video_path),
            "video_size_bytes": video_path.stat().st_size,
        },
        "input_source": source_metadata.to_dict(),
        "processing": {
            "processed_frames": frame_count,
            "elapsed_seconds": elapsed,
            "processing_fps": frame_count / elapsed if elapsed > 0 else None,
            "frames_with_detections": frames_with_detections,
            "total_detections": total_detections,
            "class_counts": dict(sorted(class_counts.items())),
            "track_updates": track_updates,
            "association_updates": association_updates,
            "unknown_associations": unknown_associations,
            "compliance_findings": compliance_findings,
            "generated_events": generated_count,
            "runtime_errors": runtime_errors,
            "source_status": source_status,
        },
        "events": generated_events,
        "persistence": {
            "jsonl": _relative(jsonl_path),
            "jsonl_records": len(JSONEventStore(jsonl_path).read_all()),
            "database": _relative(database_path),
            "persisted_event_count": persisted_count,
            "snapshot_event_count": len(snapshot_events),
            "verified_evidence_count": verified_evidence,
        },
        "dashboard_query": {
            "total_count": statistics.total_count,
            "by_type": [
                {"type": key.value, "count": value}
                for key, value in statistics.by_type
            ],
            "by_status": [
                {"status": key.value, "count": value}
                for key, value in statistics.by_status
            ],
            "sources": list(query_service.sources()),
        },
        "alerts": {
            "console_records": len(console_lines),
            "web_records": len(published_alerts),
            "web_event_ids": published_alerts,
        },
        "camera": _camera_validation(camera_index),
        "artifacts": {
            "run_root": _relative(run_root),
            "console_alerts": _relative(console_path),
        },
    }

    output_root.mkdir(parents=True, exist_ok=True)
    latest_path = output_root / "runtime_validation.json"
    run_path = run_root / "runtime_validation.json"
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    latest_path.write_text(serialized + "\n", encoding="utf-8")
    run_path.write_text(serialized + "\n", encoding="utf-8")
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Phase 7 offline runtime validation smoke path."
    )
    parser.add_argument(
        "--video",
        default=(
            "artifacts/validation/P4C-2/input/"
            "construction-workers-public-domain.mp4"
        ),
        help="MP4 source used for the real model smoke path.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/validation/P7-5",
        help="Directory for ignored runtime evidence.",
    )
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--max-frames", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_runtime_validation(
        video=args.video,
        output_dir=args.output_dir,
        camera_index=args.camera_index,
        max_frames=args.max_frames,
    )
    summary = {
        "status": result["status"],
        "run_id": result["run_id"],
        "processed_frames": result["processing"]["processed_frames"],
        "generated_events": result["processing"]["generated_events"],
        "persisted_event_count": result["persistence"][
            "persisted_event_count"
        ],
        "verified_evidence_count": result["persistence"][
            "verified_evidence_count"
        ],
        "runtime_errors": result["processing"]["runtime_errors"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
