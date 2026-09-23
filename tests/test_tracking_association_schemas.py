import json

import pytest

from core.detection.schemas import BoundingBox, Detection
from core.schemas.association import (
    AssociationMethod,
    AssociationResult,
    AssociationStatus,
    PPEAssociation,
)
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult


def _detection(
    *,
    class_id: int,
    class_name: str,
    bbox: tuple[float, float, float, float],
    confidence: float = 0.9,
) -> DetectionResult:
    return DetectionResult(
        frame_id=3,
        timestamp=0.5,
        source="video:fixture.mp4",
        detection=Detection(
            bbox=BoundingBox(*bbox),
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
        ),
    )


def test_track_result_only_wraps_person_and_serializes() -> None:
    track = TrackResult(
        track_id=7,
        detection=_detection(
            class_id=0,
            class_name="person",
            bbox=(10.0, 10.0, 100.0, 200.0),
        ),
    )

    assert json.loads(json.dumps(track.to_dict())) == {
        "track_id": 7,
        "frame_id": 3,
        "timestamp": 0.5,
        "source": "video:fixture.mp4",
        "class_id": 0,
        "class_name": "person",
        "confidence": 0.9,
        "bbox": {"x1": 10.0, "y1": 10.0, "x2": 100.0, "y2": 200.0},
    }


def test_track_result_rejects_non_person_detection() -> None:
    with pytest.raises(ValueError, match="person"):
        TrackResult(
            track_id=1,
            detection=_detection(
                class_id=1,
                class_name="hardhat",
                bbox=(20.0, 20.0, 40.0, 50.0),
            ),
        )


def test_associated_ppe_serializes_with_track_identity() -> None:
    person = _detection(
        class_id=0,
        class_name="person",
        bbox=(10.0, 10.0, 100.0, 200.0),
    )
    track = TrackResult(track_id=4, detection=person)
    association = PPEAssociation(
        ppe=_detection(
            class_id=1,
            class_name="hardhat",
            bbox=(30.0, 20.0, 60.0, 50.0),
        ),
        status=AssociationStatus.ASSOCIATED,
        track_id=4,
        person=track,
        method=AssociationMethod.CONTAINMENT,
        containment_ratio=1.0,
        iou=0.12,
    )

    payload = association.to_dict()

    assert payload["status"] == "associated"
    assert payload["track_id"] == 4
    assert payload["method"] == "containment"
    assert payload["class_name"] == "hardhat"


def test_uncertain_ppe_must_remain_unknown_without_person() -> None:
    association = PPEAssociation(
        ppe=_detection(
            class_id=3,
            class_name="vest",
            bbox=(20.0, 40.0, 80.0, 100.0),
        ),
        status=AssociationStatus.UNKNOWN,
        containment_ratio=0.75,
        iou=0.2,
    )

    assert association.to_dict()["status"] == "unknown"
    assert association.to_dict()["track_id"] is None
    assert association.to_dict()["method"] is None

    with pytest.raises(ValueError, match="cannot carry a person"):
        PPEAssociation(
            ppe=association.ppe,
            status=AssociationStatus.UNKNOWN,
            track_id=1,
        )


def test_association_result_validates_track_references_and_counts() -> None:
    person = _detection(
        class_id=0,
        class_name="person",
        bbox=(10.0, 10.0, 100.0, 200.0),
    )
    track = TrackResult(track_id=2, detection=person)
    assigned = PPEAssociation(
        ppe=_detection(
            class_id=2,
            class_name="no_hardhat",
            bbox=(35.0, 15.0, 60.0, 40.0),
        ),
        status=AssociationStatus.ASSOCIATED,
        track_id=2,
        person=track,
        method=AssociationMethod.CONTAINMENT,
        containment_ratio=1.0,
        iou=0.08,
    )
    unknown = PPEAssociation(
        ppe=_detection(
            class_id=4,
            class_name="no_vest",
            bbox=(500.0, 500.0, 550.0, 600.0),
        ),
        status=AssociationStatus.UNKNOWN,
    )

    result = AssociationResult(
        frame_id=3,
        timestamp=0.5,
        source="video:fixture.mp4",
        tracks=(track,),
        associations=(assigned, unknown),
    )

    assert result.track_count == 1
    assert result.association_count == 2
    assert result.unknown_count == 1
    assert result.associations_for_track(2) == (assigned,)
    assert json.loads(json.dumps(result.to_dict()))["unknown_count"] == 1


def test_association_result_rejects_unknown_track_reference() -> None:
    person = _detection(
        class_id=0,
        class_name="person",
        bbox=(10.0, 10.0, 100.0, 200.0),
    )
    foreign_track = TrackResult(track_id=9, detection=person)
    association = PPEAssociation(
        ppe=_detection(
            class_id=1,
            class_name="hardhat",
            bbox=(30.0, 20.0, 60.0, 50.0),
        ),
        status=AssociationStatus.ASSOCIATED,
        track_id=99,
        person=TrackResult(
            track_id=99,
            detection=person,
        ),
        method=AssociationMethod.IOU,
        iou=0.4,
    )

    with pytest.raises(ValueError, match="reference a result track"):
        AssociationResult(
            frame_id=3,
            timestamp=0.5,
            source="video:fixture.mp4",
            tracks=(foreign_track,),
            associations=(association,),
        )
