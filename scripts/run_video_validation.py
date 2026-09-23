"""Run one Phase 4C-2 MP4 validation against the frozen checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.inference.detector import InferenceError
from core.schemas.validation import (
    InferenceValidationReport,
    VideoValidationRecord,
)
from core.video.reader import VideoError, VideoReader
from services.inference_service import InferenceService
from services.video_inference_service import VideoInferenceService
from utils.config_loader import load_config


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one authorized Phase 4C-2 MP4 validation."
    )
    parser.add_argument(
        "--config",
        default="configs/video_validation.yaml",
        help="Video validation configuration path",
    )
    return parser


def _project_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _configuration(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    validation = config.get("validation")
    if not isinstance(validation, dict):
        raise ValueError("Validation configuration requires a 'validation' mapping")
    if validation.get("mode") != "video_only":
        raise ValueError("Phase 4C-2 validation mode must be video_only")
    if validation.get("execution_enabled") is not True:
        raise ValueError("Phase 4C-2 validation execution must be enabled")
    for field in ("inference", "input", "output"):
        if not isinstance(validation.get(field), dict):
            raise ValueError(f"Validation configuration requires a '{field}' mapping")
    return validation


def _validate_frozen_contract(validation: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    declared = validation["inference"]
    inference_config = _project_path(str(declared["config"]))
    frozen = load_config(inference_config)["inference"]

    expected = {
        "checkpoint": frozen["model"]["path"],
        "checkpoint_sha256": frozen["model"]["sha256"],
        "device": frozen["device"]["device"],
        "confidence_threshold": frozen["detection"]["conf_threshold"],
        "iou_threshold": frozen["detection"]["iou_threshold"],
        "imgsz": frozen["preprocessing"]["imgsz"],
    }
    for field, expected_value in expected.items():
        if declared.get(field) != expected_value:
            raise ValueError(
                f"Validation {field} must match the frozen inference contract"
            )
    if frozen.get("execution_enabled") is not False:
        raise ValueError("configs/inference.yaml must remain execution-disabled")
    if frozen["device"].get("policy") != "cpu_only":
        raise ValueError("Frozen video validation requires the CPU-only policy")
    return frozen, inference_config


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config_path = _project_path(args.config)

    try:
        validation = _configuration(config_path)
        frozen, inference_config = _validate_frozen_contract(validation)
        input_config = validation["input"]
        output_config = validation["output"]

        video_path = _project_path(str(input_config["source"]))
        output_dir = _project_path(str(output_config["directory"]))
        video_result_path = output_dir / str(output_config["video_result"])
        frame_summary_path = output_dir / str(output_config["frame_summary"])
        report_path = output_dir / str(output_config["report"])

        VideoReader.validate_source(video_path)
        video_sha256 = _sha256(video_path)
        if video_sha256 != str(input_config["video_sha256"]):
            raise ValueError("External validation video SHA256 mismatch")
        if video_path.stat().st_size != int(input_config["video_size_bytes"]):
            raise ValueError("External validation video size mismatch")

        inference_service = InferenceService(
            config_path=inference_config,
            execution_enabled=True,
        )
        checkpoint_path = inference_service.detector.model_path
        checkpoint_sha256 = _sha256(checkpoint_path)
        if checkpoint_sha256 != frozen["model"]["sha256"]:
            raise ValueError("Frozen checkpoint SHA256 mismatch")
        if checkpoint_path.stat().st_size != int(frozen["model"]["size_bytes"]):
            raise ValueError("Frozen checkpoint size mismatch")

        video_service = VideoInferenceService(
            inference_service=inference_service,
        )
        started = perf_counter()
        result = video_service.infer_video(video_path)
        processing_time_seconds = perf_counter() - started

        detections = [
            detection
            for frame in result.frames
            for detection in frame.detections
        ]
        counts = Counter(detection.class_name for detection in detections)
        class_counts = {
            class_name: counts[class_name]
            for class_name in inference_service.detector.class_names
            if counts[class_name]
        }
        frames_with_detections = sum(
            1 for frame in result.frames if frame.detections
        )
        frame_summary = [
            {
                "frame_id": frame.frame_id,
                "timestamp": frame.timestamp,
                "detection_count": frame.detection_count,
                "class_counts": dict(
                    Counter(
                        detection.class_name
                        for detection in frame.detections
                    )
                ),
            }
            for frame in result.frames
        ]

        record = VideoValidationRecord(
            source_label=str(input_config["source_label"]),
            model_sha256=checkpoint_sha256,
            source_fps=result.metadata.fps,
            declared_frame_count=result.metadata.frame_count,
            processed_frames=result.processed_frames,
            processing_time_seconds=processing_time_seconds,
            total_detections=len(detections),
            frames_with_detections=frames_with_detections,
            class_counts=class_counts,
        )
        report = InferenceValidationReport(
            validation_id=str(validation["id"]),
            model_sha256=checkpoint_sha256,
            runtime_id=inference_service.detector.runtime_id,
            video_records=(record,),
        )

        video_payload = {
            "validation_id": str(validation["id"]),
            "mode": "video_only",
            "status": "success",
            "source_label": str(input_config["source_label"]),
            "source_provider": str(input_config["provider"]),
            "source_url": str(input_config["source_url"]),
            "source_license": str(input_config["license"]),
            "source_derivation": str(input_config["derivation"]),
            "video_sha256": video_sha256,
            "video_size_bytes": video_path.stat().st_size,
            "checkpoint_path": frozen["model"]["path"],
            "checkpoint_sha256": checkpoint_sha256,
            "runtime_id": inference_service.detector.runtime_id,
            "device": frozen["device"]["device"],
            "processing_time_seconds": processing_time_seconds,
            "processing_fps": record.processing_fps,
            "total_detections": len(detections),
            "frames_with_detections": frames_with_detections,
            "class_counts": class_counts,
            "video": result.metadata.to_dict(),
            "frame_results": [
                frame.to_dict() for frame in result.frames
            ],
        }
        frame_payload = {
            "validation_id": str(validation["id"]),
            "video": result.metadata.to_dict(),
            "frames": frame_summary,
        }
        report_payload = report.to_dict()
        report_payload.update(
            {
                "mode": "video_only",
                "checkpoint_path": frozen["model"]["path"],
                "processing_time_seconds": processing_time_seconds,
                "processing_fps": record.processing_fps,
            }
        )

        _write_json(video_result_path, video_payload)
        _write_json(frame_summary_path, frame_payload)
        _write_json(report_path, report_payload)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "validation_id": report.validation_id,
                    "processed_frames": result.processed_frames,
                    "total_detections": len(detections),
                    "video_result": str(
                        video_result_path.relative_to(PROJECT_ROOT)
                    ),
                    "frame_summary": str(
                        frame_summary_path.relative_to(PROJECT_ROOT)
                    ),
                    "report": str(report_path.relative_to(PROJECT_ROOT)),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        code = (
            exc.code
            if isinstance(exc, (InferenceError, VideoError))
            else "validation_error"
        )
        message = str(exc)

    print(
        json.dumps(
            {
                "status": "error",
                "error": code,
                "message": message,
            },
            ensure_ascii=False,
        )
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
