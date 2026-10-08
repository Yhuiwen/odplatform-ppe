from core.events.event_engine import EventEngine
from core.rules.compliance_engine import RuleDomainSettings, RuleSettings
from core.schemas.compliance import (
    ComplianceEventType,
    ComplianceFinding,
    ComplianceResult,
    ComplianceState,
)


HELMET = RuleDomainSettings(
    enabled=True,
    required=True,
    positive_classes=("hardhat",),
    violation_classes=("no_hardhat",),
)
VEST = RuleDomainSettings(
    enabled=True,
    required=True,
    positive_classes=("vest",),
    violation_classes=("no_vest",),
)


def _settings(*, cooldown_seconds: float = 30.0) -> RuleSettings:
    return RuleSettings(
        min_consecutive_frames=5,
        min_duration_seconds=1.0,
        recovery_frames=5,
        cooldown_seconds=cooldown_seconds,
        helmet=HELMET,
        vest=VEST,
    )


def _result(
    frame_id: int,
    *,
    event_type: ComplianceEventType = ComplianceEventType.NO_HELMET,
    state: ComplianceState = ComplianceState.VIOLATION,
    track_id: int = 1,
) -> ComplianceResult:
    return ComplianceResult(
        frame_id=frame_id,
        timestamp=float(frame_id),
        findings=(
            ComplianceFinding(
                track_id=track_id,
                event_type=event_type,
                state=state,
                confidence=0.9,
                timestamp=float(frame_id),
                evidence=(f"state={state.value}",),
            ),
        ),
    )


def test_event_is_created_once_per_active_violation_cycle() -> None:
    engine = EventEngine(settings=_settings())
    emitted = []
    for frame_id in range(7):
        emitted.extend(engine.process(_result(frame_id)))

    assert len(emitted) == 1
    assert emitted[0].track_id == 1
    assert emitted[0].event_type is ComplianceEventType.NO_HELMET
    assert emitted[0].timestamp == 4.0


def test_different_tracks_are_isolated() -> None:
    engine = EventEngine(settings=_settings())
    emitted = []
    for frame_id in range(5):
        emitted.extend(
            engine.process(
                ComplianceResult(
                    frame_id=frame_id,
                    timestamp=float(frame_id),
                    findings=(
                        _result(frame_id, track_id=1).findings[0],
                        _result(frame_id, track_id=2).findings[0],
                    ),
                )
            )
        )

    assert {(event.track_id, event.event_type) for event in emitted} == {
        (1, ComplianceEventType.NO_HELMET),
        (2, ComplianceEventType.NO_HELMET),
    }


def test_recovery_and_cooldown_allow_a_new_cycle() -> None:
    engine = EventEngine(settings=_settings(cooldown_seconds=10.0))
    emitted = []

    for frame_id in range(5):
        emitted.extend(engine.process(_result(frame_id)))
    assert len(emitted) == 1
    assert emitted[0].timestamp == 4.0

    for frame_id in range(5, 10):
        assert engine.process(
            _result(frame_id, state=ComplianceState.COMPLIANT)
        ) == ()

    for frame_id in range(10, 15):
        assert engine.process(_result(frame_id)) == ()

    for frame_id in range(15, 20):
        assert engine.process(
            _result(frame_id, state=ComplianceState.COMPLIANT)
        ) == ()

    for frame_id in range(20, 25):
        emitted.extend(engine.process(_result(frame_id)))

    assert len(emitted) == 2
    assert emitted[1].timestamp == 24.0
    assert emitted[0].event_id != emitted[1].event_id


def test_unknown_event_requires_temporal_confirmation() -> None:
    engine = EventEngine(settings=_settings())
    emitted = []
    for frame_id in range(5):
        emitted.extend(
            engine.process(
                _result(
                    frame_id,
                    event_type=ComplianceEventType.PPE_UNKNOWN,
                    state=ComplianceState.UNKNOWN,
                )
            )
        )

    assert len(emitted) == 1
    assert emitted[0].event_type is ComplianceEventType.PPE_UNKNOWN


def test_vest_violation_survives_brief_conflicting_evidence() -> None:
    engine = EventEngine(settings=_settings())
    emitted = []
    states = (
        [ComplianceState.VIOLATION] * 28
        + [ComplianceState.COMPLIANT] * 2
        + [ComplianceState.UNKNOWN] * 8
        + [ComplianceState.VIOLATION] * 5
    )
    for frame_id, state in enumerate(states):
        event_type = (
            ComplianceEventType.PPE_UNKNOWN
            if state is ComplianceState.UNKNOWN
            else ComplianceEventType.NO_VEST
        )
        finding = ComplianceFinding(
            track_id=4,
            event_type=event_type,
            state=state,
            confidence=0.7,
            timestamp=frame_id / 30,
            evidence=(
                "vest=conflicting_evidence"
                if state is ComplianceState.UNKNOWN
                else "vest=no_vest"
                if state is ComplianceState.VIOLATION
                else "vest=vest",
            ),
        )
        emitted.extend(
            engine.process(
                ComplianceResult(
                    frame_id=frame_id,
                    timestamp=frame_id / 30,
                    findings=(finding,),
                )
            )
        )

    vest_events = [
        event for event in emitted
        if event.event_type is ComplianceEventType.NO_VEST
    ]
    assert len(vest_events) == 1
    assert vest_events[0].timestamp >= 1.0
    assert any(
        item.startswith("vest_evidence_ratio=")
        for item in vest_events[0].evidence
    )


def test_vest_compliance_resets_candidate_and_prevents_false_event() -> None:
    engine = EventEngine(settings=_settings())
    emitted = []
    states = (
        [ComplianceState.VIOLATION] * 8
        + [ComplianceState.COMPLIANT] * 12
        + [ComplianceState.VIOLATION] * 4
    )
    for frame_id, state in enumerate(states):
        finding = ComplianceFinding(
            track_id=2,
            event_type=ComplianceEventType.NO_VEST,
            state=state,
            confidence=0.8,
            timestamp=frame_id / 30,
            evidence=(
                "vest=no_vest"
                if state is ComplianceState.VIOLATION
                else "vest=vest",
            ),
        )
        emitted.extend(
            engine.process(
                ComplianceResult(
                    frame_id=frame_id,
                    timestamp=frame_id / 30,
                    findings=(finding,),
                )
            )
        )
    assert not any(event.event_type is ComplianceEventType.NO_VEST for event in emitted)


def test_frozen_thirty_second_cooldown_after_five_frame_recovery() -> None:
    engine = EventEngine(settings=_settings())
    first = [event for frame in range(5) for event in engine.process(_result(frame))]
    assert len(first) == 1
    assert all(engine.process(_result(frame)) == () for frame in range(5, 8))
    assert all(
        engine.process(_result(frame, state=ComplianceState.COMPLIANT)) == ()
        for frame in range(8, 13)
    )
    assert all(engine.process(_result(frame)) == () for frame in range(13, 18))
    assert all(
        engine.process(_result(frame, state=ComplianceState.COMPLIANT)) == ()
        for frame in range(18, 23)
    )
    later = [event for frame in range(53, 58) for event in engine.process(_result(frame))]
    assert len(later) == 1
    assert later[0].event_id != first[0].event_id
