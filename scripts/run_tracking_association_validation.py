"""Prepare or run the Phase 5-3 tracking/association validation.

The default configuration is execution-disabled. ``--preflight`` performs
static identity, hash, configuration and dependency checks without loading the
model or touching the checkpoint bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from collections import Counter
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.association.ppe_person_association import (  # noqa: E402
    PPEPersonAssociationAdapter,
)
from core.schemas.association import AssociationStatus  # noqa: E402
from core.tracking.bytetrack_adapter import (  # noqa: E402
    ByteTrackPersonTrackingAdapter,
)
from services.inference_service import InferenceService  # noqa: E402
from services.video_inference_service import VideoInferenceService  # noqa: E402
from utils.config_loader import load_config  # noqa: E402


class ValidationError(RuntimeError):
    """Validation failure with a stable machine-readable code."""

    code = "validation_error"


class ValidationExecutionDisabledError(ValidationError):
    code = "execution_disabled"


class ValidationRuntimeError(ValidationError):
    code = "runtime_unavailable"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare or run the P5-3 tracking/association validation."
    )
    parser.add_argument(
        "--config",
        default="configs/p5_3_validation.yaml",
        help="P5-3 validation configuration path",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Validate frozen identities and runtime availability only",
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
        raise ValidationError(
            "Validation configuration requires a 'validation' mapping"
        )
    if validation.get("id") != "P5-3":
        raise ValidationError("Validation id must be P5-3")
    if validation.get("mode") != "tracking_association_video":
        raise ValidationError(
            "Validation mode must be tracking_association_video"
        )
    if not isinstance(validation.get("execution_enabled"), bool):
        raise ValidationError("execution_enabled must be boolean")
    for field in ("components", "model", "input", "output"):
        if not isinstance(validation.get(field), dict):
            raise ValidationError(
                f"Validation configuration requires a '{field}' mapping"
            )
    return validation


def _validate_frozen_contract(
    validation: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    components = validation["components"]
    paths = {
        name: _project_path(str(components[name]))
        for name in (
            "inference_config",
            "tracker_config",
            "association_config",
        )
    }
    inference = load_config(paths["inference_config"]).get("inference")
    tracker = load_config(paths["tracker_config"]).get("tracker")
    association = load_config(paths["association_config"]).get("association")
    if not all(
        isinstance(value, dict)
        for value in (inference, tracker, association)
    ):
        raise ValidationError("Frozen component configuration is invalid")

    if inference.get("execution_enabled") is not False:
        raise ValidationError(
            "configs/inference.yaml must remain execution-disabled"
        )
    if inference.get("device", {}).get("policy") != "cpu_only":
        raise ValidationError(
            "P5-3 validation requires the frozen CPU-only policy"
        )
    if tracker.get("execution_enabled") is not True:
        raise ValidationError("Frozen tracker adapter must be enabled")
    if association.get("execution_enabled") is not True:
        raise ValidationError("Frozen association adapter must be enabled")

    model = validation["model"]
    frozen_model = inference.get("model", {})
    if model.get("checkpoint") != frozen_model.get("path"):
        raise ValidationError("Validation checkpoint path is not frozen")
    if model.get("checkpoint_sha256") != frozen_model.get("sha256"):
        raise ValidationError("Validation checkpoint SHA256 is not frozen")

    runtime = inference.get("runtime", {})
    tracker_implementation = tracker.get("implementation", {})
    if tracker_implementation.get("version") != runtime.get("ultralytics"):
        raise ValidationError(
            "Tracker and inference Ultralytics versions must match"
        )

    configs = {
        "inference": inference,
        "tracker": tracker,
        "association": association,
    }
    return configs, paths


def _verify_assets(
    validation: dict[str, Any],
    configs: dict[str, dict[str, Any]],
) -> tuple[Path, Path, str, str]:
    model = validation["model"]
    checkpoint_path = _project_path(str(model["checkpoint"]))
    if not checkpoint_path.is_file():
        raise ValidationError("Frozen checkpoint does not exist")
    checkpoint_sha256 = _sha256(checkpoint_path)
    if checkpoint_sha256 != str(model["checkpoint_sha256"]):
        raise ValidationError("Frozen checkpoint SHA256 mismatch")
    expected_size = int(configs["inference"]["model"]["size_bytes"])
    if checkpoint_path.stat().st_size != expected_size:
        raise ValidationError("Frozen checkpoint size mismatch")

    input_config = validation["input"]
    video_path = _project_path(str(input_config["source"]))
    if not video_path.is_file():
        raise ValidationError("Validated input video does not exist")
    video_sha256 = _sha256(video_path)
    if video_sha256 != str(input_config["video_sha256"]):
        raise ValidationError("Validated input video SHA256 mismatch")
    if video_path.stat().st_size != int(input_config["video_size_bytes"]):
        raise ValidationError("Validated input video size mismatch")

    return checkpoint_path, video_path, checkpoint_sha256, video_sha256


def _dependency_status(
    configs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    runtime = configs["inference"]["runtime"]
    expected = {
        "python": str(runtime["python"]),
        "torch": str(runtime["torch"]),
        "torchvision": str(runtime["torchvision"]),
        "ultralytics": str(runtime["ultralytics"]),
    }
    observed: dict[str, str | None] = {
        "python": platform.python_version(),
        "torch": None,
        "torchvision": None,
        "ultralytics": None,
    }

    if importlib.util.find_spec("torch") is not None:
        import torch

        observed["torch"] = str(torch.__version__)
    for package in ("torchvision", "ultralytics"):
        if importlib.util.find_spec(package) is None:
            continue
        try:
            observed[package] = version(package)
        except PackageNotFoundError:
            observed[package] = None

    mismatches = [
        name
        for name in expected
        if observed.get(name) != expected[name]
    ]
    return {
        "ready": not mismatches,
        "expected": expected,
        "observed": observed,
        "mismatches": mismatches,
    }


def preflight(config_path: Path) -> dict[str, Any]:
    """Run static readiness checks without loading the model or video."""

    validation = _configuration(config_path)
    configs, _ = _validate_frozen_contract(validation)
    checkpoint_path, video_path, checkpoint_sha256, video_sha256 = (
        _verify_assets(validation, configs)
    )
    dependencies = _dependency_status(configs)
    status = (
        "READY_FOR_AUTHORIZED_EXECUTION"
        if dependencies["ready"]
        else "BLOCKED_RUNTIME_DEPENDENCIES"
    )
    return {
        "validation_id": validation["id"],
        "validation_status": validation["status"],
        "execution_enabled": validation["execution_enabled"],
        "status": status,
        "checkpoint_path": str(checkpoint_path.relative_to(PROJECT_ROOT)),
        "checkpoint_sha256": checkpoint_sha256,
        "video_path": str(video_path.relative_to(PROJECT_ROOT)),
        "video_sha256": video_sha256,
        "dependencies": dependencies,
        "model_loaded": False,
        "inference_executed": False,
    }


def _runtime_fingerprint(
    configs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    dependencies = _dependency_status(configs)
    if not dependencies["ready"]:
        raise ValidationRuntimeError(
            "Frozen runtime dependency mismatch: "
            + ", ".join(dependencies["mismatches"])
        )

    import torch

    return {
        "runtime_id": str(configs["inference"]["runtime"]["id"]),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch": str(torch.__version__),
        "torch_cuda": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "ultralytics": version("ultralytics"),
        "device": "cpu",
        "device_policy": "cpu_only",
        "cuda_used": False,
    }


def _run_validation(
    validation: dict[str, Any],
    configs: dict[str, dict[str, Any]],
    config_paths: dict[str, Path],
    checkpoint_path: Path,
    video_path: Path,
    checkpoint_sha256: str,
    video_sha256: str,
) -> dict[str, Any]:
    if validation["execution_enabled"] is not True:
        raise ValidationExecutionDisabledError(
            "P5-3 real runtime validation is not authorized"
        )

    runtime = _runtime_fingerprint(configs)
    inference_service = InferenceService(
        config_path=config_paths["inference_config"],
        execution_enabled=True,
    )
    tracker = ByteTrackPersonTrackingAdapter(
        config_path=config_paths["tracker_config"],
        execution_enabled=True,
    )
    association = PPEPersonAssociationAdapter(
        config_path=config_paths["association_config"],
        execution_enabled=True,
    )
    video_service = VideoInferenceService(
        inference_service=inference_service,
    )

    started = perf_counter()
    video_result = video_service.infer_video(video_path)
    preprocess_inference_seconds = perf_counter() - started

    frame_summary: list[dict[str, Any]] = []
    association_results = []
    unique_track_ids: set[int] = set()
    max_tracks_per_frame = 0
    person_detection_count = 0
    ppe_detection_count = 0

    for frame in video_result.frames:
        person_detections = [
            item for item in frame.detections if item.class_id == 0
        ]
        ppe_detections = [
            item for item in frame.detections if item.class_id in (1, 2, 3, 4)
        ]
        tracks = tracker.update(
            person_detections,
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            source=video_result.metadata.source,
        )
        result = association.associate(
            tracks,
            ppe_detections,
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            source=video_result.metadata.source,
        )
        association_results.append(result)
        unique_track_ids.update(track.track_id for track in tracks)
        max_tracks_per_frame = max(max_tracks_per_frame, len(tracks))
        person_detection_count += len(person_detections)
        ppe_detection_count += len(ppe_detections)
        frame_summary.append(
            {
                "frame_id": frame.frame_id,
                "timestamp": frame.timestamp,
                "person_detections": len(person_detections),
                "ppe_detections": len(ppe_detections),
                "track_count": result.track_count,
                "association_count": result.association_count,
                "associated_count": (
                    result.association_count - result.unknown_count
                ),
                "unknown_count": result.unknown_count,
                "track_ids": [track.track_id for track in tracks],
                "associations": [
                    item.to_dict() for item in result.associations
                ],
            }
        )

    association_records = [
        item
        for result in association_results
        for item in result.associations
    ]
    associated_records = [
        item
        for item in association_records
        if item.status is AssociationStatus.ASSOCIATED
    ]
    unknown_records = [
        item
        for item in association_records
        if item.status is AssociationStatus.UNKNOWN
    ]
    ppe_class_counts = Counter(
        item.ppe.class_name for item in association_records
    )
    associated_class_counts = Counter(
        item.ppe.class_name for item in associated_records
    )
    unknown_class_counts = Counter(
        item.ppe.class_name for item in unknown_records
    )

    return {
        "validation_id": validation["id"],
        "mode": validation["mode"],
        "status": "success",
        "checkpoint_path": str(checkpoint_path.relative_to(PROJECT_ROOT)),
        "checkpoint_sha256": checkpoint_sha256,
        "video_path": str(video_path.relative_to(PROJECT_ROOT)),
        "video_sha256": video_sha256,
        "runtime": runtime,
        "video": video_result.metadata.to_dict(),
        "processing_time_seconds": preprocess_inference_seconds,
        "processing_fps": (
            video_result.processed_frames / preprocess_inference_seconds
            if preprocess_inference_seconds > 0
            else None
        ),
        "track_statistics": {
            "track_observations": sum(
                result.track_count for result in association_results
            ),
            "unique_track_ids": sorted(unique_track_ids),
            "unique_track_count": len(unique_track_ids),
            "max_tracks_per_frame": max_tracks_per_frame,
        },
        "detection_statistics": {
            "person_detections": person_detection_count,
            "ppe_detections": ppe_detection_count,
        },
        "association_statistics": {
            "association_count": len(association_records),
            "associated_count": len(associated_records),
            "unknown_count": len(unknown_records),
            "ppe_class_counts": dict(ppe_class_counts),
            "associated_class_counts": dict(associated_class_counts),
            "unknown_class_counts": dict(unknown_class_counts),
        },
        "frame_summary": frame_summary,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config_path = _project_path(args.config)

    try:
        if args.preflight:
            payload = preflight(config_path)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        validation = _configuration(config_path)
        configs, config_paths = _validate_frozen_contract(validation)
        (
            checkpoint_path,
            video_path,
            checkpoint_sha256,
            video_sha256,
        ) = _verify_assets(validation, configs)
        payload = _run_validation(
            validation,
            configs,
            config_paths,
            checkpoint_path,
            video_path,
            checkpoint_sha256,
            video_sha256,
        )

        output = validation["output"]
        output_dir = _project_path(str(output["directory"]))
        result_path = output_dir / str(output["result"])
        frame_summary_path = output_dir / str(output["frame_summary"])
        report_path = output_dir / str(output["report"])
        frame_summary = payload.pop("frame_summary")
        _write_json(result_path, payload)
        _write_json(
            frame_summary_path,
            {
                "validation_id": validation["id"],
                "video": payload["video"],
                "frames": frame_summary,
            },
        )
        _write_json(report_path, payload)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "validation_id": validation["id"],
                    "processed_frames": payload["video"]["frame_count"],
                    "result": str(result_path.relative_to(PROJECT_ROOT)),
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
        code = getattr(exc, "code", "validation_error")
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": code,
                    "message": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
