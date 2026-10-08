"""Fast deterministic checks for the non-production M/N controls."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult
from diagnostics.p9c3b_precomputed_tracking import (
    PrecomputedTrackingAdapter, load_track_fixture, track_template,
)
from scripts.run_p9b_full_chain import diagnostic_cycle_pause, run
from scripts.run_p9c3b_inference_only import assert_cycle_matches


def person(frame_id=0, timestamp=1.0, source="mp4:test"):
    return DetectionResult(frame_id, timestamp, source,
                           Detection(BoundingBox(1, 2, 3, 4), 0, "person", 0.8))


def fixture():
    detection = person()
    template = track_template(TrackResult(7, detection), [detection])
    return {
        "schema": "p9c3b-real-tracks-v1", "diagnostic_only": True,
        "detection_fixture_sha256": "det", "tracker_config_sha256": "cfg",
        "ultralytics_version": "8.4.157", "lap_version": "0.5.13",
        "total_frames": 47, "total_tracks": 1,
        "frames": [{"ordinal": i, "tracks": [template] if i == 0 else []} for i in range(47)],
    }


def test_track_fixture_identity_and_count(tmp_path):
    path = tmp_path / "tracks.json"
    data = fixture()
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded = load_track_fixture(path, detection_sha256="det", tracker_config_sha256="cfg",
                                ultralytics_version="8.4.157", lap_version="0.5.13")
    assert loaded["total_tracks"] == 1
    with pytest.raises(ValueError, match="detection_fixture_sha256"):
        load_track_fixture(path, detection_sha256="other", tracker_config_sha256="cfg",
                           ultralytics_version="8.4.157", lap_version="0.5.13")
    data["frames"].pop()
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="47 frames"):
        load_track_fixture(path, detection_sha256="det", tracker_config_sha256="cfg",
                           ultralytics_version="8.4.157", lap_version="0.5.13")


def test_precomputed_tracker_uses_current_context_and_resets():
    adapter = PrecomputedTrackingAdapter(fixture())
    with pytest.raises(ValueError, match="cursor"):
        adapter.update([person()], frame_id=0, timestamp=1.0, source="mp4:test")
    adapter.reset()
    current = person(timestamp=9.5, source="mp4:current")
    tracks = adapter.update([current], frame_id=0, timestamp=9.5, source="mp4:current")
    assert len(tracks) == 1
    assert tracks[0].track_id == 7
    assert tracks[0].detection is current
    assert (tracks[0].timestamp, tracks[0].source) == (9.5, "mp4:current")
    with pytest.raises(ValueError, match="cursor"):
        adapter.update([current], frame_id=0, timestamp=9.5, source="mp4:current")
    adapter.reset()
    assert adapter._cursor == 0 and adapter._session_count == 2


def test_wrong_track_detection_fails_closed():
    adapter = PrecomputedTrackingAdapter(fixture())
    adapter.reset()
    with pytest.raises(ValueError, match="bbox"):
        adapter.update([DetectionResult(0, 1.0, "mp4:test",
                    Detection(BoundingBox(5, 2, 7, 4), 0, "person", 0.8))],
                    frame_id=0, timestamp=1.0, source="mp4:test")


def test_m_cycle_semantics_and_pacing():
    results = [[person(frame_id=0)]] + [[] for _ in range(46)]
    from diagnostics.p9c3a_precomputed import detection_template
    detection_fixture = {"total_frames": 47, "total_detections": 1,
                         "frames": [{"detections": [detection_template(person())] if i == 0 else []}
                                    for i in range(47)]}
    assert_cycle_matches(results, detection_fixture)
    assert diagnostic_cycle_pause(cycle_elapsed=4.7, target_period=8, remaining_duration=10) == 3.3
    assert diagnostic_cycle_pause(cycle_elapsed=1, target_period=8, remaining_duration=2) == 2


def test_diagnostics_are_not_production_defaults():
    import inspect
    from services.monitoring_service import MonitoringService
    assert inspect.signature(run).parameters["diagnostic_tracker"].default is None
    assert "PrecomputedTrackingAdapter" not in inspect.getsource(MonitoringService)
