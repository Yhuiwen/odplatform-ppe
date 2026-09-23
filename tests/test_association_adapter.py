import pytest

from core.adapters.association_adapter import (
    AssociationAdapter,
    AssociationAdapterError,
)
from core.detection.schemas import BoundingBox, Detection
from core.schemas.association import (
    AssociationMethod,
    AssociationResult,
    AssociationStatus,
    PPEAssociation,
)
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult


SOURCE = "offline:phase6-fixture"


def _detection(
    *,
    class_id: int,
    class_name: str,
    bbox: tuple[float, float, float, float],
    confidence: float = 0.9,
) -> DetectionResult:
    return DetectionResult(
        frame_id=2,
        timestamp=0.5,
        source=SOURCE,
        detection=Detection(
            bbox=BoundingBox(*bbox),
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
        ),
    )


def _result() -> AssociationResult:
    person = TrackResult(
        track_id=7,
        detection=_detection(
            class_id=0,
            class_name="person",
            bbox=(0.0, 0.0, 100.0, 200.0),
        ),
    )
    association = PPEAssociation(
        ppe=_detection(
            class_id=2,
            class_name="no_hardhat",
            bbox=(20.0, 10.0, 50.0, 40.0),
        ),
        status=AssociationStatus.ASSOCIATED,
        track_id=7,
        person=person,
        method=AssociationMethod.CONTAINMENT,
        containment_ratio=1.0,
        iou=0.1,
    )
    return AssociationResult(
        frame_id=2,
        timestamp=0.5,
        source=SOURCE,
        tracks=(person,),
        associations=(association,),
    )


def test_adapter_preserves_frozen_association_identity() -> None:
    result = _result()

    adapted = AssociationAdapter().adapt(result)

    assert adapted.frame_id == result.frame_id
    assert adapted.timestamp == result.timestamp
    assert adapted.tracks == result.tracks
    assert adapted.associations == result.associations
    assert adapted.to_dict()["tracks"] == [result.tracks[0].to_dict()]


def test_adapter_does_not_mutate_phase5_result() -> None:
    result = _result()
    before = result.to_dict()

    AssociationAdapter().adapt(result)

    assert result.to_dict() == before


def test_adapter_rejects_non_association_input() -> None:
    with pytest.raises(AssociationAdapterError, match="AssociationResult"):
        AssociationAdapter().adapt({"frame_id": 0})  # type: ignore[arg-type]
