from dataclasses import dataclass

from core.association.ppe_person_association import (
    PPEPersonAssociationAdapter,
)
from core.detection.schemas import BoundingBox, Detection
from core.schemas.association import (
    AssociationMethod,
    AssociationResult,
    AssociationStatus,
)
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult
from core.tracking.bytetrack_adapter import (
    ByteTrackMatch,
    ByteTrackPersonTrackingAdapter,
)


SOURCE = "video:p5-3-synthetic.mp4"


@dataclass
class ScriptedBackend:
    outputs: list[tuple[ByteTrackMatch, ...]]
    calls: list[tuple[int, ...]] | None = None

    def __post_init__(self) -> None:
        self.calls = []

    def update(self, detections) -> tuple[ByteTrackMatch, ...]:
        self.calls.append(
            tuple(detection.class_id for detection in detections)
        )
        return self.outputs.pop(0)

    def reset(self) -> None:
        return None


def _detection(
    frame_id: int,
    *,
    class_id: int,
    class_name: str,
    bbox: tuple[float, float, float, float],
    confidence: float = 0.9,
) -> DetectionResult:
    return DetectionResult(
        frame_id=frame_id,
        timestamp=frame_id / 10.0,
        source=SOURCE,
        detection=Detection(
            bbox=BoundingBox(*bbox),
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
        ),
    )


def _person(
    frame_id: int,
    bbox: tuple[float, float, float, float],
    *,
    confidence: float = 0.9,
) -> DetectionResult:
    return _detection(
        frame_id,
        class_id=0,
        class_name="person",
        bbox=bbox,
        confidence=confidence,
    )


def _run_frame(
    tracker: ByteTrackPersonTrackingAdapter,
    association: PPEPersonAssociationAdapter,
    *,
    frame_id: int,
    people: list[DetectionResult],
    ppe: list[DetectionResult],
) -> AssociationResult:
    tracks = tracker.update(
        people,
        frame_id=frame_id,
        timestamp=frame_id / 10.0,
        source=SOURCE,
    )
    return association.associate(
        tracks,
        ppe,
        frame_id=frame_id,
        timestamp=frame_id / 10.0,
        source=SOURCE,
    )


def test_single_person_with_ppe_traverses_the_full_pipeline() -> None:
    backend = ScriptedBackend(
        [
            (ByteTrackMatch(detection_index=0, track_id=7),),
            (ByteTrackMatch(detection_index=0, track_id=7),),
        ]
    )
    tracker = ByteTrackPersonTrackingAdapter(
        execution_enabled=True,
        backend=backend,
    )
    association = PPEPersonAssociationAdapter(execution_enabled=True)

    first = _run_frame(
        tracker,
        association,
        frame_id=0,
        people=[_person(0, (0.0, 0.0, 100.0, 200.0))],
        ppe=[
            _detection(
                0,
                class_id=1,
                class_name="hardhat",
                bbox=(20.0, 10.0, 50.0, 40.0),
            ),
            _detection(
                0,
                class_id=3,
                class_name="vest",
                bbox=(10.0, 70.0, 90.0, 170.0),
            ),
        ],
    )
    second = _run_frame(
        tracker,
        association,
        frame_id=1,
        people=[_person(1, (1.0, 1.0, 101.0, 201.0))],
        ppe=[
            _detection(
                1,
                class_id=1,
                class_name="hardhat",
                bbox=(21.0, 11.0, 51.0, 41.0),
            )
        ],
    )

    assert isinstance(first, AssociationResult)
    assert isinstance(second, AssociationResult)
    assert isinstance(first.tracks[0], TrackResult)
    assert [result.tracks[0].track_id for result in (first, second)] == [7, 7]
    assert [item.status for item in first.associations] == [
        AssociationStatus.ASSOCIATED,
        AssociationStatus.ASSOCIATED,
    ]
    assert [item.track_id for item in first.associations] == [7, 7]
    assert first.associations[0].method is AssociationMethod.CONTAINMENT
    assert backend.calls == [(0,), (0,)]


def test_multiple_persons_receive_separate_pipeline_assignments() -> None:
    backend = ScriptedBackend(
        [
            (
                ByteTrackMatch(detection_index=0, track_id=11),
                ByteTrackMatch(detection_index=1, track_id=22),
            )
        ]
    )
    tracker = ByteTrackPersonTrackingAdapter(
        execution_enabled=True,
        backend=backend,
    )
    association = PPEPersonAssociationAdapter(execution_enabled=True)

    result = _run_frame(
        tracker,
        association,
        frame_id=0,
        people=[
            _person(0, (0.0, 0.0, 100.0, 200.0)),
            _person(0, (200.0, 0.0, 300.0, 200.0)),
        ],
        ppe=[
            _detection(
                0,
                class_id=1,
                class_name="hardhat",
                bbox=(20.0, 10.0, 50.0, 40.0),
            ),
            _detection(
                0,
                class_id=3,
                class_name="vest",
                bbox=(220.0, 80.0, 280.0, 160.0),
            ),
        ],
    )

    assert result.track_count == 2
    assert result.association_count == 2
    assert result.unknown_count == 0
    assert [item.track_id for item in result.associations] == [11, 22]
    assert [item.ppe.class_name for item in result.associations] == [
        "hardhat",
        "vest",
    ]


def test_missing_ppe_remains_absence_through_the_pipeline() -> None:
    backend = ScriptedBackend(
        [(ByteTrackMatch(detection_index=0, track_id=5),)]
    )
    tracker = ByteTrackPersonTrackingAdapter(
        execution_enabled=True,
        backend=backend,
    )
    association = PPEPersonAssociationAdapter(execution_enabled=True)

    result = _run_frame(
        tracker,
        association,
        frame_id=0,
        people=[_person(0, (0.0, 0.0, 100.0, 200.0))],
        ppe=[],
    )

    assert result.track_count == 1
    assert result.association_count == 0
    assert result.unknown_count == 0


def test_ambiguous_association_remains_unknown_through_the_pipeline() -> None:
    backend = ScriptedBackend(
        [
            (
                ByteTrackMatch(detection_index=0, track_id=1),
                ByteTrackMatch(detection_index=1, track_id=2),
            )
        ]
    )
    tracker = ByteTrackPersonTrackingAdapter(
        execution_enabled=True,
        backend=backend,
    )
    association = PPEPersonAssociationAdapter(execution_enabled=True)

    result = _run_frame(
        tracker,
        association,
        frame_id=0,
        people=[
            _person(0, (0.0, 0.0, 100.0, 200.0)),
            _person(0, (5.0, 0.0, 100.0, 200.0)),
        ],
        ppe=[
            _detection(
                0,
                class_id=1,
                class_name="hardhat",
                bbox=(0.0, 50.0, 100.0, 120.0),
            )
        ],
    )

    assert result.track_count == 2
    assert result.association_count == 1
    assert result.unknown_count == 1
    assert result.associations[0].status is AssociationStatus.UNKNOWN
    assert result.associations[0].track_id is None
    assert result.associations[0].person is None
    assert result.associations[0].method is None


def test_pipeline_sends_only_people_to_tracker_and_serializes() -> None:
    backend = ScriptedBackend(
        [(ByteTrackMatch(detection_index=0, track_id=9),)]
    )
    tracker = ByteTrackPersonTrackingAdapter(
        execution_enabled=True,
        backend=backend,
    )
    association = PPEPersonAssociationAdapter(execution_enabled=True)
    hardhat = _detection(
        0,
        class_id=1,
        class_name="hardhat",
        bbox=(20.0, 10.0, 50.0, 40.0),
    )

    result = _run_frame(
        tracker,
        association,
        frame_id=0,
        people=[_person(0, (0.0, 0.0, 100.0, 200.0))],
        ppe=[hardhat],
    )

    assert backend.calls == [(0,)]
    assert result.to_dict()["tracks"][0]["track_id"] == 9
    assert result.to_dict()["associations"][0]["class_name"] == "hardhat"
