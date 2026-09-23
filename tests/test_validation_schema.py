from __future__ import annotations

import json

import pytest

from core.schemas.validation import (
    ImageValidationRecord,
    InferenceValidationReport,
    VideoValidationRecord,
)


MODEL_SHA256 = "1" * 64


def test_image_validation_record_serialization() -> None:
    record = ImageValidationRecord(
        source_label="external:image-001.jpg",
        model_sha256=MODEL_SHA256,
        load_success=True,
        width=1280,
        height=720,
        detection_count=3,
        class_counts={"person": 2, "hardhat": 1},
        confidences=(0.91, 0.84, 0.77),
        latency_ms=42.5,
    )

    payload = json.loads(json.dumps(record.to_dict()))

    assert payload == {
        "source_label": "external:image-001.jpg",
        "model_sha256": MODEL_SHA256,
        "status": "success",
        "load_success": True,
        "width": 1280,
        "height": 720,
        "detection_count": 3,
        "class_counts": {"person": 2, "hardhat": 1},
        "confidences": [0.91, 0.84, 0.77],
        "latency_ms": 42.5,
        "error_code": None,
    }


def test_video_validation_record_serialization() -> None:
    record = VideoValidationRecord(
        source_label="external:video-001.mp4",
        model_sha256=MODEL_SHA256,
        source_fps=25.0,
        declared_frame_count=100,
        processed_frames=100,
        processing_time_seconds=20.0,
        total_detections=50,
        frames_with_detections=40,
        class_counts={"person": 30, "hardhat": 20},
    )

    payload = json.loads(json.dumps(record.to_dict()))

    assert payload["status"] == "success"
    assert payload["processing_fps"] == 5.0
    assert payload["frames_with_detections"] == 40
    assert payload["class_counts"] == {"person": 30, "hardhat": 20}


def test_inference_validation_report_serialization() -> None:
    image_record = ImageValidationRecord(
        source_label="external:image-001.jpg",
        model_sha256=MODEL_SHA256,
        load_success=True,
        width=640,
        height=480,
        detection_count=0,
        class_counts={},
        confidences=(),
        latency_ms=12.0,
    )
    report = InferenceValidationReport(
        validation_id="P4C-1",
        model_sha256=MODEL_SHA256,
        runtime_id="INF-RUNTIME-001",
        image_records=(image_record,),
    )

    payload = json.loads(json.dumps(report.to_dict()))

    assert payload["validation_id"] == "P4C-1"
    assert payload["runtime_id"] == "INF-RUNTIME-001"
    assert payload["image_records"][0]["detection_count"] == 0
    assert payload["video_records"] == []


def test_validation_schema_rejects_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="class counts must sum"):
        ImageValidationRecord(
            source_label="external:image-002.jpg",
            model_sha256=MODEL_SHA256,
            load_success=True,
            width=640,
            height=480,
            detection_count=2,
            class_counts={"person": 1},
            confidences=(0.9, 0.8),
            latency_ms=10.0,
        )
