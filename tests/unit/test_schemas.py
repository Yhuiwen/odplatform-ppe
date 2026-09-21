import pytest

from core.detection.schemas import (
    BoundingBox,
    Detection,
    DetectionClass,
    FrameMeta,
)


def test_locked_detection_class_order() -> None:
    assert [item.name for item in DetectionClass] == [
        "PERSON",
        "HARDHAT",
        "NO_HARDHAT",
        "VEST",
        "NO_VEST",
    ]
    assert [item.value for item in DetectionClass] == [0, 1, 2, 3, 4]


def test_detection_schema_accepts_valid_values() -> None:
    bbox = BoundingBox(1.0, 2.0, 11.0, 22.0)
    detection = Detection(bbox, 1, "hardhat", 0.9)
    frame = FrameMeta(0, 0.0, 1920, 1080, "unit-test")
    assert bbox.width == 10.0
    assert bbox.height == 20.0
    assert bbox.area == 200.0
    assert detection.class_name == "hardhat"
    assert frame.source == "unit-test"


def test_invalid_schema_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="Bounding box"):
        BoundingBox(10.0, 10.0, 5.0, 20.0)

    bbox = BoundingBox(1.0, 2.0, 3.0, 4.0)
    with pytest.raises(ValueError, match="confidence"):
        Detection(bbox, 0, "person", 1.1)

    with pytest.raises(ValueError, match="dimensions"):
        FrameMeta(0, 0.0, 0, 1080, "unit-test")
