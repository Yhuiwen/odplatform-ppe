"""Run one Phase 4C-1 image validation against the frozen checkpoint."""

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

from PIL import Image

from core.inference.detector import InferenceError
from core.schemas.validation import (
    ImageValidationRecord,
    InferenceValidationReport,
)
from services.inference_service import InferenceService
from utils.config_loader import load_config


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one authorized Phase 4C-1 image validation."
    )
    parser.add_argument(
        "--config",
        default="configs/validation.yaml",
        help="Validation configuration path",
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
    if validation.get("mode") != "image_only":
        raise ValueError("Phase 4C-1 validation mode must be image_only")
    if validation.get("execution_enabled") is not True:
        raise ValueError("Phase 4C-1 validation execution must be enabled")

    for field in ("input", "output"):
        if not isinstance(validation.get(field), dict):
            raise ValueError(f"Validation configuration requires a '{field}' mapping")
    return validation


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config_path = _project_path(args.config)

    try:
        validation = _configuration(config_path)
        input_config = validation["input"]
        output_config = validation["output"]
        inference_config = _project_path(str(validation["inference_config"]))
        image_path = _project_path(str(input_config["source"]))
        output_dir = _project_path(str(output_config["directory"]))
        image_result_path = output_dir / str(output_config["image_result"])
        report_path = output_dir / str(output_config["report"])

        if not image_path.is_file():
            raise ValueError(f"External validation image does not exist: {image_path}")

        with Image.open(image_path) as image:
            width, height = image.size
            image_format = image.format

        image_sha256 = _sha256(image_path)
        service = InferenceService(
            config_path=inference_config,
            execution_enabled=bool(validation["execution_enabled"]),
        )
        checkpoint_path = service.detector.model_path
        checkpoint_sha256 = _sha256(checkpoint_path)

        first_start = perf_counter()
        service.infer_image(image_path)
        cold_start_ms = (perf_counter() - first_start) * 1000.0

        inference_start = perf_counter()
        detections = service.infer_image(image_path)
        inference_ms = (perf_counter() - inference_start) * 1000.0

        counts = Counter(result.class_name for result in detections)
        class_counts = {
            class_name: counts[class_name]
            for class_name in service.detector.class_names
            if counts[class_name]
        }
        record = ImageValidationRecord(
            source_label=str(input_config["source_label"]),
            model_sha256=checkpoint_sha256,
            load_success=True,
            width=width,
            height=height,
            detection_count=len(detections),
            class_counts=class_counts,
            confidences=tuple(result.confidence for result in detections),
            latency_ms=inference_ms,
        )
        report = InferenceValidationReport(
            validation_id=str(validation["id"]),
            model_sha256=checkpoint_sha256,
            runtime_id=service.detector.runtime_id,
            image_records=(record,),
        )

        image_payload = {
            "validation_id": str(validation["id"]),
            "mode": "image_only",
            "status": "success",
            "source_label": str(input_config["source_label"]),
            "source_provider": str(input_config["provider"]),
            "source_url": str(input_config["source_url"]),
            "source_license": str(input_config["license"]),
            "image_sha256": image_sha256,
            "image_size_bytes": image_path.stat().st_size,
            "image_format": image_format,
            "width": width,
            "height": height,
            "checkpoint_path": "models/checkpoints/EXP-001/best.pt",
            "checkpoint_sha256": checkpoint_sha256,
            "runtime_id": service.detector.runtime_id,
            "model_load_success": True,
            "cold_start_ms": cold_start_ms,
            "cold_start_scope": "model_load_plus_first_inference",
            "warm_inference_ms": inference_ms,
            "detections": [result.to_dict() for result in detections],
        }
        report_payload = report.to_dict()
        report_payload.update(
            {
                "mode": "image_only",
                "video_validation": "DEFERRED_NOT_AUTHORIZED",
                "checkpoint_path": "models/checkpoints/EXP-001/best.pt",
                "cold_start_ms": cold_start_ms,
                "warm_inference_ms": inference_ms,
            }
        )

        _write_json(image_result_path, image_payload)
        _write_json(report_path, report_payload)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "validation_id": report.validation_id,
                    "detections": len(detections),
                    "image_result": str(image_result_path.relative_to(PROJECT_ROOT)),
                    "report": str(report_path.relative_to(PROJECT_ROOT)),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        code = exc.code if isinstance(exc, InferenceError) else "validation_error"
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
