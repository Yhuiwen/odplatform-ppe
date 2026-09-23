from examples.phase6_demo import run_demo

from utils.paths import PROJECT_ROOT


FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "phase6_association_sample.json"


def test_offline_phase6_demo_emits_expected_event_types(tmp_path) -> None:
    output = tmp_path / "events.jsonl"

    events = run_demo(FIXTURE, output)

    assert {(event.track_id, event.event_type.value) for event in events} == {
        (1, "NO_HELMET"),
        (1, "NO_VEST"),
        (3, "PPE_UNKNOWN"),
    }
    assert output.is_file()
    assert len(output.read_text(encoding="utf-8").splitlines()) == 3


def test_demo_fixture_matches_frozen_association_contract() -> None:
    content = FIXTURE.read_text(encoding="utf-8")

    assert '"frame_id"' in content
    assert '"status": "associated"' in content
    assert '"class_name": "person"' in content
