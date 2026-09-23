import json

from core.schemas.detection import Detection, DetectionResult
from core.detection.schemas import BoundingBox


def test_detection_result_creation_and_json_serialization() -> None:
    result = DetectionResult(
        frame_id=7,
        timestamp=1.25,
        source="image:fixture.jpg",
        detection=Detection(
            bbox=BoundingBox(10.0, 20.0, 50.0, 80.0),
            class_id=1,
            class_name="hardhat",
            confidence=0.91,
        ),
    )

    payload = result.to_dict()

    assert json.loads(json.dumps(payload)) == {
        "frame_id": 7,
        "timestamp": 1.25,
        "source": "image:fixture.jpg",
        "class_id": 1,
        "class_name": "hardhat",
        "confidence": 0.91,
        "bbox": {"x1": 10.0, "y1": 20.0, "x2": 50.0, "y2": 80.0},
    }


def test_detection_result_exposes_required_fields() -> None:
    result = DetectionResult(
        frame_id=0,
        timestamp=0.0,
        source="rtsp:test",
        detection=Detection(
            bbox=BoundingBox(0.0, 0.0, 10.0, 10.0),
            class_id=2,
            class_name="no_hardhat",
            confidence=0.8,
        ),
    )

    assert result.frame_id == 0
    assert result.timestamp == 0.0
    assert result.source == "rtsp:test"
    assert result.class_name == "no_hardhat"
    assert result.confidence == 0.8
    assert result.bbox.as_tuple() == (0.0, 0.0, 10.0, 10.0)
