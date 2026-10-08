"""Fast controls for tracker-only diagnostic drivers."""

from __future__ import annotations

import inspect

import pytest

from scripts.run_p9b_full_chain import diagnostic_cycle_pause
from scripts.run_p9c3c_tracker_attribution import (
    drive_cycle, load_real_fixture, person_inputs, tracker_state,
)


def test_real_fixture_identity_and_count():
    fixture = load_real_fixture()
    assert fixture["total_frames"] == 47
    assert fixture["total_detections"] == 77
    assert sum(len(row[3]) for row in person_inputs(fixture, cycle=0, persistent=False)) == 76


def test_persistent_context_is_monotonic():
    fixture = load_real_fixture()
    first = list(person_inputs(fixture, cycle=0, persistent=True))
    second = list(person_inputs(fixture, cycle=1, persistent=True))
    assert first[0][0] == 0 and first[-1][0] == 46
    assert second[0][0] == 47 and second[-1][0] == 93
    assert first[-1][1] < second[0][1]
    assert all(item.frame_id == frame_id and item.timestamp == timestamp
               for frame_id, timestamp, _, detections in second for item in detections)


def test_persistent_update_driver():
    fixture = load_real_fixture()
    state = {"cycles": 0, "updates": 0, "track_outputs": 0, "tracker_instances": 0}
    tracker = drive_cycle("P", fixture, 0, None, state)
    assert state["updates"] == 47 and state["track_outputs"] >= 1
    assert tracker_state(tracker)["native_frame_id"] == 47
    tracker = drive_cycle("P", fixture, 1, tracker, state)
    assert state["updates"] == 94 and state["tracker_instances"] == 1
    assert tracker_state(tracker)["native_frame_id"] == 94


def test_lifecycle_only_driver():
    fixture = load_real_fixture()
    state = {"cycles": 0, "updates": 0, "track_outputs": 0, "tracker_instances": 0}
    assert drive_cycle("Q", fixture, 0, None, state) is None
    assert state == {"cycles": 0, "updates": 0, "track_outputs": 0, "tracker_instances": 1}


def test_session_driver_resets_tracker():
    fixture = load_real_fixture()
    state = {"cycles": 0, "updates": 0, "track_outputs": 0, "tracker_instances": 0}
    tracker = drive_cycle("R", fixture, 0, None, state)
    assert tracker_state(tracker)["native_tracker_live"] == 0
    tracker = drive_cycle("R", fixture, 1, tracker, state)
    assert state["updates"] == 94 and state["tracker_instances"] == 2
    assert tracker_state(tracker)["native_frame_id"] == 0


def test_cycle_pacing():
    assert diagnostic_cycle_pause(cycle_elapsed=1.0, target_period=8, remaining_duration=20) == 7
    assert diagnostic_cycle_pause(cycle_elapsed=9.0, target_period=8, remaining_duration=20) == 0


def test_tracker_state_probe_is_bounded_after_reset():
    fixture = load_real_fixture()
    state = {"cycles": 0, "updates": 0, "track_outputs": 0, "tracker_instances": 0}
    tracker = drive_cycle("P", fixture, 0, None, state)
    live = tracker_state(tracker)
    assert live["native_frame_id"] == 47
    assert max(live[key] for key in ("tracked", "lost", "removed")) < 47
    tracker.reset()
    assert tracker_state(tracker) == {"native_tracker_live": 0, "tracked": 0,
                                      "lost": 0, "removed": 0, "native_frame_id": 0}


def test_diagnostic_is_not_production_default():
    from services.monitoring_service import MonitoringService
    assert "run_p9c3c_tracker_attribution" not in inspect.getsource(MonitoringService)
    with pytest.raises(ValueError):
        list(person_inputs(load_real_fixture(), cycle=-1, persistent=True))
