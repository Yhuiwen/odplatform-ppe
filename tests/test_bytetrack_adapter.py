from dataclasses import dataclass

import pytest

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult
from core.tracking.bytetrack_adapter import (
    ByteTrackBackendError,
    ByteTrackMatch,
    ByteTrackPersonTrackingAdapter,
    InvalidTrackingClassError,
    TrackingExecutionDisabledError,
    TrackingFrameContextError,
)
from core.tracking.interfaces import PersonTrackingAdapter


@dataclass
class ScriptedBackend:
    outputs: list[tuple[ByteTrackMatch, ...]]
    calls: list[tuple[int, ...]] = None
    reset_calls: int = 0

    def __post_init__(self) -> None:
        self.calls = []

    def update(self, detections) -> tuple[ByteTrackMatch, ...]:
        self.calls.append(
            tuple(detection.frame_id for detection in detections)
        )
        if not self.outputs:
            return tuple(
                ByteTrackMatch(detection_index=index, track_id=index + 1)
                for index in range(len(detections))
            )
        return self.outputs.pop(0)

    def reset(self) -> None:
        self.reset_calls += 1


def _person(
    frame_id: int,
    *,
    x1: float = 10.0,
    y1: float = 20.0,
    x2: float = 60.0,
    y2: float = 160.0,
    confidence: float = 0.9,
    class_id: int = 0,
    class_name: str = "person",
) -> DetectionResult:
    return DetectionResult(
        frame_id=frame_id,
        timestamp=frame_id / 10.0,
        source="video:fixture.mp4",
        detection=Detection(
            bbox=BoundingBox(x1, y1, x2, y2),
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
        ),
    )


def _adapter(
    backend: ScriptedBackend,
    *,
    execution_enabled: bool = True,
) -> ByteTrackPersonTrackingAdapter:
    return ByteTrackPersonTrackingAdapter(
        execution_enabled=execution_enabled,
        backend=backend,
    )


def _update(
    adapter: ByteTrackPersonTrackingAdapter,
    detections: list[DetectionResult],
    frame_id: int,
):
    return adapter.update(
        detections,
        frame_id=frame_id,
        timestamp=frame_id / 10.0,
        source="video:fixture.mp4",
    )


def test_single_person_keeps_continuous_track_id() -> None:
    backend = ScriptedBackend(
        [
            (ByteTrackMatch(detection_index=0, track_id=7),),
            (ByteTrackMatch(detection_index=0, track_id=7),),
            (ByteTrackMatch(detection_index=0, track_id=7),),
        ]
    )
    adapter = _adapter(backend)

    frames = [
        _update(adapter, [_person(frame_id)], frame_id)
        for frame_id in range(3)
    ]

    assert [frame[0].track_id for frame in frames] == [7, 7, 7]
    assert [frame[0].frame_id for frame in frames] == [0, 1, 2]


def test_multiple_persons_are_mapped_to_their_detection_indexes() -> None:
    backend = ScriptedBackend(
        [
            (
                ByteTrackMatch(detection_index=1, track_id=22),
                ByteTrackMatch(detection_index=0, track_id=11),
            )
        ]
    )
    adapter = _adapter(backend)
    detections = [
        _person(0, x1=10.0, x2=50.0),
        _person(0, x1=100.0, x2=150.0),
    ]

    tracks = _update(adapter, detections, 0)

    assert [(track.track_id, track.bbox.x1) for track in tracks] == [
        (22, 100.0),
        (11, 10.0),
    ]


def test_person_can_leave_and_reenter_with_stable_track_id() -> None:
    backend = ScriptedBackend(
        [
            (ByteTrackMatch(detection_index=0, track_id=5),),
            (),
            (ByteTrackMatch(detection_index=0, track_id=5),),
        ]
    )
    adapter = _adapter(backend)

    assert _update(adapter, [_person(0)], 0)[0].track_id == 5
    assert _update(adapter, [], 1) == ()
    assert _update(adapter, [_person(2)], 2)[0].track_id == 5
    assert backend.calls == [(0,), (), (2,)]


def test_missing_frame_still_updates_backend_state() -> None:
    backend = ScriptedBackend([(), ()])
    adapter = _adapter(backend)

    assert _update(adapter, [], 10) == ()
    assert _update(adapter, [], 11) == ()
    assert backend.calls == [(), ()]


def test_non_person_detection_is_rejected_before_backend() -> None:
    backend = ScriptedBackend([()])
    adapter = _adapter(backend)
    hardhat = _person(
        0,
        class_id=1,
        class_name="hardhat",
    )

    with pytest.raises(InvalidTrackingClassError, match="person class_id=0"):
        _update(adapter, [hardhat], 0)
    assert backend.calls == []


def test_frame_context_mismatch_is_rejected() -> None:
    backend = ScriptedBackend([()])
    adapter = _adapter(backend)

    with pytest.raises(TrackingFrameContextError, match="does not match"):
        _update(adapter, [_person(1)], 0)
    assert backend.calls == []


def test_low_confidence_person_detection_is_not_sent_to_backend() -> None:
    backend = ScriptedBackend([()])
    adapter = _adapter(backend)

    assert _update(adapter, [_person(0, confidence=0.1)], 0) == ()
    assert backend.calls == [()]


def test_execution_disabled_fails_closed() -> None:
    backend = ScriptedBackend([()])
    adapter = _adapter(backend, execution_enabled=False)

    with pytest.raises(TrackingExecutionDisabledError):
        _update(adapter, [], 0)
    assert backend.calls == []


def test_backend_duplicate_match_fails_closed() -> None:
    backend = ScriptedBackend(
        [
            (
                ByteTrackMatch(detection_index=0, track_id=1),
                ByteTrackMatch(detection_index=0, track_id=2),
            )
        ]
    )
    adapter = _adapter(backend)

    with pytest.raises(ByteTrackBackendError, match="duplicate"):
        _update(adapter, [_person(0)], 0)


def test_adapter_conforms_to_frozen_protocol_and_reset_delegates() -> None:
    backend = ScriptedBackend([()])
    adapter = _adapter(backend)

    assert isinstance(adapter, PersonTrackingAdapter)
    adapter.reset()

    assert backend.reset_calls == 1
