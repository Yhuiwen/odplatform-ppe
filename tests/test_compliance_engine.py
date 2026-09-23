from dataclasses import replace

import pytest

from core.detection.schemas import BoundingBox, Detection
from core.rules.compliance_engine import (
    ComplianceEngine,
    ComplianceExecutionDisabledError,
    load_rule_settings,
)
from core.rules.temporal_filter import TemporalViolationFilter
from core.schemas.association import (
    AssociationMethod,
    AssociationStatus,
    PPEAssociation,
)
from core.schemas.compliance import (
    ComplianceEventType,
    ComplianceInput,
    ComplianceState,
)
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult


def _person(frame_id: int, track_id: int = 1) -> TrackResult:
    detection = Detection(
        bbox=BoundingBox(0.0, 0.0, 100.0, 200.0),
        class_id=0,
        class_name="person",
        confidence=0.95,
    )
    return TrackResult(
        track_id=track_id,
        detection=DetectionResult(
            frame_id=frame_id,
            timestamp=float(frame_id),
            source="offline:phase6-fixture",
            detection=detection,
        ),
    )


def _association(
    frame_id: int,
    person: TrackResult,
    *,
    class_id: int,
    class_name: str,
    confidence: float = 0.9,
    status: AssociationStatus = AssociationStatus.ASSOCIATED,
) -> PPEAssociation:
    detection = Detection(
        bbox=BoundingBox(20.0, 10.0, 50.0, 40.0),
        class_id=class_id,
        class_name=class_name,
        confidence=confidence,
    )
    ppe = DetectionResult(
        frame_id=frame_id,
        timestamp=float(frame_id),
        source="offline:phase6-fixture",
        detection=detection,
    )
    if status is AssociationStatus.UNKNOWN:
        return PPEAssociation(ppe=ppe, status=status)
    return PPEAssociation(
        ppe=ppe,
        status=status,
        track_id=person.track_id,
        person=person,
        method=AssociationMethod.CONTAINMENT,
        containment_ratio=1.0,
        iou=0.1,
    )


def _input(
    frame_id: int,
    associations: list[PPEAssociation],
) -> ComplianceInput:
    person = _person(frame_id)
    return ComplianceInput(
        frame_id=frame_id,
        timestamp=float(frame_id),
        tracks=(person,),
        associations=tuple(associations),
    )


def _finding(result, event_type: ComplianceEventType):
    return next(
        finding
        for finding in result.findings
        if finding.event_type is event_type
    )


def test_no_hardhat_is_conservatively_classified_as_violation() -> None:
    person = _person(0)
    result = ComplianceEngine().evaluate(
        _input(
            0,
            [
                _association(
                    0,
                    person,
                    class_id=2,
                    class_name="no_hardhat",
                )
            ],
        )
    )

    finding = _finding(result, ComplianceEventType.NO_HELMET)
    assert finding.state is ComplianceState.VIOLATION
    assert finding.confidence == 0.9


def test_no_vest_is_conservatively_classified_as_violation() -> None:
    person = _person(0)
    result = ComplianceEngine().evaluate(
        _input(
            0,
            [
                _association(
                    0,
                    person,
                    class_id=4,
                    class_name="no_vest",
                )
            ],
        )
    )

    finding = _finding(result, ComplianceEventType.NO_VEST)
    assert finding.state is ComplianceState.VIOLATION


def test_missing_ppe_is_unknown_not_compliant() -> None:
    result = ComplianceEngine().evaluate(_input(0, []))

    finding = _finding(result, ComplianceEventType.PPE_UNKNOWN)
    assert finding.state is ComplianceState.UNKNOWN
    assert finding.confidence == 0.0
    assert any("missing_evidence" in item for item in finding.evidence)


def test_conflicting_helmet_evidence_is_unknown() -> None:
    person = _person(0)
    result = ComplianceEngine().evaluate(
        _input(
            0,
            [
                _association(
                    0,
                    person,
                    class_id=1,
                    class_name="hardhat",
                ),
                _association(
                    0,
                    person,
                    class_id=2,
                    class_name="no_hardhat",
                ),
            ],
        )
    )

    finding = _finding(result, ComplianceEventType.PPE_UNKNOWN)
    assert any("conflicting_evidence" in item for item in finding.evidence)


def test_explicit_positive_evidence_is_compliant() -> None:
    person = _person(0)
    result = ComplianceEngine().evaluate(
        _input(
            0,
            [
                _association(
                    0,
                    person,
                    class_id=1,
                    class_name="hardhat",
                ),
                _association(
                    0,
                    person,
                    class_id=3,
                    class_name="vest",
                ),
            ],
        )
    )

    assert _finding(result, ComplianceEventType.NO_HELMET).state is (
        ComplianceState.COMPLIANT
    )
    assert _finding(result, ComplianceEventType.NO_VEST).state is (
        ComplianceState.COMPLIANT
    )
    assert not result.candidate_findings


def test_single_frame_cannot_confirm_a_violation() -> None:
    person = _person(0)
    result = ComplianceEngine().evaluate(
        _input(
            0,
            [
                _association(
                    0,
                    person,
                    class_id=2,
                    class_name="no_hardhat",
                )
            ],
        )
    )

    confirmed = TemporalViolationFilter().update(result)

    assert confirmed == ()


def test_continuous_frames_and_duration_confirm_once() -> None:
    engine = ComplianceEngine()
    temporal = TemporalViolationFilter()
    confirmed = []
    for frame_id in range(5):
        person = _person(frame_id)
        result = engine.evaluate(
            _input(
                frame_id,
                [
                    _association(
                        frame_id,
                        person,
                        class_id=2,
                        class_name="no_hardhat",
                    )
                ],
            )
        )
        confirmed.extend(temporal.update(result))

    helmet_events = [
        finding
        for finding in confirmed
        if finding.event_type is ComplianceEventType.NO_HELMET
    ]
    assert len(helmet_events) == 1
    assert "temporal_frames=5" in helmet_events[0].evidence

    person = _person(5)
    sixth = engine.evaluate(
        _input(
            5,
            [
                _association(
                    5,
                    person,
                    class_id=2,
                    class_name="no_hardhat",
                )
            ],
        )
    )
    assert temporal.update(sixth) == ()


def test_duration_threshold_blocks_fast_frames() -> None:
    engine = ComplianceEngine()
    temporal = TemporalViolationFilter(
        settings=replace(load_rule_settings(), min_duration_seconds=5.0)
    )
    confirmed = []
    for frame_id in range(5):
        person = _person(frame_id)
        confirmed.extend(
            temporal.update(
                engine.evaluate(
                    _input(
                        frame_id,
                        [
                            _association(
                                frame_id,
                                person,
                                class_id=2,
                                class_name="no_hardhat",
                            )
                        ],
                    )
                )
            )
        )

    assert confirmed == []


def test_missing_candidate_frame_breaks_consecutive_confirmation() -> None:
    engine = ComplianceEngine()
    temporal = TemporalViolationFilter()
    confirmed = []

    for frame_id in range(4):
        person = _person(frame_id)
        confirmed.extend(
            temporal.update(
                engine.evaluate(
                    _input(
                        frame_id,
                        [
                            _association(
                                frame_id,
                                person,
                                class_id=2,
                                class_name="no_hardhat",
                            )
                        ],
                    )
                )
            )
        )

    assert confirmed == []
    person = _person(5)
    interrupted = engine.evaluate(
        ComplianceInput(
            frame_id=5,
            timestamp=5.0,
            tracks=(person,),
            associations=(
                _association(
                    5,
                    person,
                    class_id=1,
                    class_name="hardhat",
                ),
                _association(
                    5,
                    person,
                    class_id=3,
                    class_name="vest",
                ),
            ),
        )
    )
    assert temporal.update(interrupted) == ()

    person = _person(6)
    fifth_candidate_after_gap = engine.evaluate(
        _input(
            6,
            [
                _association(
                    6,
                    person,
                    class_id=2,
                    class_name="no_hardhat",
                )
            ],
        )
    )
    assert temporal.update(fifth_candidate_after_gap) == ()


def test_disabled_compliance_execution_fails_closed() -> None:
    engine = ComplianceEngine(execution_enabled=False)

    with pytest.raises(ComplianceExecutionDisabledError):
        engine.evaluate(_input(0, []))
