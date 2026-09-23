from dataclasses import dataclass

import pytest

from core.association.interfaces import PPEAssociationAdapter
from core.association.ppe_person_association import (
    AssociationExecutionDisabledError,
    AssociationFrameContextError,
    InvalidAssociationClassError,
    PPEPersonAssociationAdapter,
)
from core.detection.schemas import BoundingBox, Detection
from core.schemas.association import AssociationMethod, AssociationStatus
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult


SOURCE = "video:association-fixture.mp4"
TIMESTAMP = 0.5


def _detection(
    *,
    class_id: int,
    class_name: str,
    bbox: tuple[float, float, float, float],
    confidence: float = 0.9,
) -> DetectionResult:
    return DetectionResult(
        frame_id=5,
        timestamp=TIMESTAMP,
        source=SOURCE,
        detection=Detection(
            bbox=BoundingBox(*bbox),
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
        ),
    )


def _track(
    track_id: int,
    bbox: tuple[float, float, float, float],
    *,
    confidence: float = 0.9,
) -> TrackResult:
    return TrackResult(
        track_id=track_id,
        detection=_detection(
            class_id=0,
            class_name="person",
            bbox=bbox,
            confidence=confidence,
        ),
    )


def _associate(
    tracks: list[TrackResult],
    ppe_detections: list[DetectionResult],
    *,
    adapter: PPEPersonAssociationAdapter | None = None,
):
    active_adapter = adapter or PPEPersonAssociationAdapter()
    return active_adapter.associate(
        tracks,
        ppe_detections,
        frame_id=5,
        timestamp=TIMESTAMP,
        source=SOURCE,
    )


def test_single_person_helmet_is_associated_by_containment() -> None:
    person = _track(1, (0.0, 0.0, 100.0, 200.0))
    helmet = _detection(
        class_id=1,
        class_name="hardhat",
        bbox=(20.0, 10.0, 50.0, 40.0),
    )

    result = _associate([person], [helmet])

    assert result.track_count == 1
    assert result.association_count == 1
    association = result.associations[0]
    assert association.status is AssociationStatus.ASSOCIATED
    assert association.track_id == 1
    assert association.method is AssociationMethod.CONTAINMENT
    assert association.containment_ratio == 1.0


def test_single_person_vest_is_associated() -> None:
    person = _track(3, (0.0, 0.0, 100.0, 200.0))
    vest = _detection(
        class_id=3,
        class_name="vest",
        bbox=(10.0, 70.0, 90.0, 170.0),
    )

    association = _associate([person], [vest]).associations[0]

    assert association.status is AssociationStatus.ASSOCIATED
    assert association.track_id == 3
    assert association.ppe.class_name == "vest"


def test_multiple_people_receive_their_own_ppe_detections() -> None:
    first = _track(11, (0.0, 0.0, 100.0, 200.0))
    second = _track(22, (200.0, 0.0, 300.0, 200.0))
    helmet = _detection(
        class_id=1,
        class_name="hardhat",
        bbox=(20.0, 10.0, 50.0, 40.0),
    )
    vest = _detection(
        class_id=3,
        class_name="vest",
        bbox=(220.0, 80.0, 280.0, 160.0),
    )

    result = _associate([first, second], [helmet, vest])

    assert [item.track_id for item in result.associations] == [11, 22]
    assert [item.status for item in result.associations] == [
        AssociationStatus.ASSOCIATED,
        AssociationStatus.ASSOCIATED,
    ]


def test_wrong_candidate_is_rejected_as_unknown() -> None:
    person = _track(7, (0.0, 0.0, 100.0, 200.0))
    helmet = _detection(
        class_id=1,
        class_name="hardhat",
        bbox=(300.0, 300.0, 340.0, 340.0),
    )

    association = _associate([person], [helmet]).associations[0]

    assert association.status is AssociationStatus.UNKNOWN
    assert association.track_id is None
    assert association.person is None
    assert association.method is None
    assert association.containment_ratio == 0.0
    assert association.iou == 0.0


def test_ambiguous_candidates_remain_unknown() -> None:
    first = _track(1, (0.0, 0.0, 100.0, 200.0))
    second = _track(2, (5.0, 0.0, 100.0, 200.0))
    helmet = _detection(
        class_id=1,
        class_name="hardhat",
        bbox=(0.0, 50.0, 100.0, 120.0),
    )

    association = _associate([first, second], [helmet]).associations[0]

    assert association.status is AssociationStatus.UNKNOWN
    assert association.track_id is None
    assert association.containment_ratio == 1.0


def test_missing_ppe_does_not_synthesize_an_association() -> None:
    person = _track(1, (0.0, 0.0, 100.0, 200.0))

    result = _associate([person], [])

    assert result.track_count == 1
    assert result.association_count == 0
    assert result.unknown_count == 0


def test_empty_detection_returns_empty_result() -> None:
    result = _associate([], [])

    assert result.track_count == 0
    assert result.association_count == 0
    assert result.unknown_count == 0
    assert result.to_dict()["associations"] == []


def test_iou_only_association_uses_frozen_iou_threshold() -> None:
    person = _track(1, (0.0, 0.0, 100.0, 100.0))
    vest = _detection(
        class_id=3,
        class_name="vest",
        bbox=(50.0, 50.0, 150.0, 150.0),
    )

    association = _associate([person], [vest]).associations[0]

    assert association.status is AssociationStatus.ASSOCIATED
    assert association.method is AssociationMethod.IOU
    assert association.containment_ratio == pytest.approx(0.25)
    assert association.iou == pytest.approx(2500.0 / 17500.0)


def test_low_confidence_ppe_is_unknown() -> None:
    person = _track(1, (0.0, 0.0, 100.0, 200.0))
    helmet = _detection(
        class_id=1,
        class_name="hardhat",
        bbox=(20.0, 10.0, 50.0, 40.0),
        confidence=0.1,
    )

    association = _associate([person], [helmet]).associations[0]

    assert association.status is AssociationStatus.UNKNOWN
    assert association.track_id is None


def test_low_confidence_person_track_is_not_assigned() -> None:
    person = _track(1, (0.0, 0.0, 100.0, 200.0), confidence=0.1)
    helmet = _detection(
        class_id=1,
        class_name="hardhat",
        bbox=(20.0, 10.0, 50.0, 40.0),
    )

    association = _associate([person], [helmet]).associations[0]

    assert association.status is AssociationStatus.UNKNOWN
    assert association.track_id is None


def test_person_detection_cannot_enter_ppe_input() -> None:
    person_track = _track(1, (0.0, 0.0, 100.0, 200.0))
    person_detection = _detection(
        class_id=0,
        class_name="person",
        bbox=(20.0, 10.0, 50.0, 40.0),
    )

    with pytest.raises(InvalidAssociationClassError):
        _associate([person_track], [person_detection])


def test_mismatched_ppe_class_id_and_name_is_rejected() -> None:
    person_track = _track(1, (0.0, 0.0, 100.0, 200.0))
    invalid = _detection(
        class_id=2,
        class_name="hardhat",
        bbox=(20.0, 10.0, 50.0, 40.0),
    )

    with pytest.raises(InvalidAssociationClassError):
        _associate([person_track], [invalid])


def test_frame_context_mismatch_is_rejected() -> None:
    person = _track(1, (0.0, 0.0, 100.0, 200.0))
    helmet = _detection(
        class_id=1,
        class_name="hardhat",
        bbox=(20.0, 10.0, 50.0, 40.0),
    )
    adapter = PPEPersonAssociationAdapter()

    with pytest.raises(AssociationFrameContextError):
        adapter.associate(
            [person],
            [helmet],
            frame_id=6,
            timestamp=TIMESTAMP,
            source=SOURCE,
        )


def test_disabled_execution_fails_closed() -> None:
    adapter = PPEPersonAssociationAdapter(execution_enabled=False)

    with pytest.raises(AssociationExecutionDisabledError):
        _associate([], [], adapter=adapter)


def test_adapter_conforms_to_frozen_protocol() -> None:
    assert isinstance(PPEPersonAssociationAdapter(), PPEAssociationAdapter)
