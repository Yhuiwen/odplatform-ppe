"""Fast checks for the non-production P9-C.3a control."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult
from diagnostics.p9c3a_precomputed import (
    PrecomputedInferenceService, detection_template, fixture_from_results,
    load_fixture, sha256,
)
from scripts.compare_p9c3a_semantics import semantic_signature


def fixture_files(tmp_path):
    paths = [tmp_path / name for name in ("video.mp4", "best.pt", "inference.yaml", "requirements.txt")]
    for path in paths:
        path.write_bytes(path.name.encode())
    frames = [SimpleNamespace(frame_id=i) for i in range(47)]
    result = DetectionResult(
        frame_id=0, timestamp=0.0, source="mp4:test",
        detection=Detection(BoundingBox(1, 2, 3, 4), 0, "person", 0.75),
    )
    rows = [[result]] + [[] for _ in range(46)]
    fixture = fixture_from_results(
        frames=frames, results_by_frame=rows, source_path=paths[0],
        checkpoint_path=paths[1], config_path=paths[2], lock_path=paths[3],
        generated_at="2026-09-26T00:00:00Z", runtime="3.12.1",
    )
    file = tmp_path / "fixture.json"
    file.write_text(json.dumps(fixture), encoding="utf-8")
    return paths, file, fixture


def test_fixture_loader_checks_frame_count_and_frozen_hashes(tmp_path):
    paths, file, fixture = fixture_files(tmp_path)
    loaded = load_fixture(file, expected_mp4_sha256=sha256(paths[0]),
                          expected_checkpoint_sha256=sha256(paths[1]),
                          expected_config_sha256=sha256(paths[2]),
                          expected_lock_sha256=sha256(paths[3]))
    assert loaded["total_frames"] == 47
    assert loaded["total_detections"] == 1
    assert sha256(file)
    with pytest.raises(ValueError, match="source_mp4_sha256"):
        load_fixture(file, expected_mp4_sha256="wrong",
                     expected_checkpoint_sha256=sha256(paths[1]),
                     expected_config_sha256=sha256(paths[2]),
                     expected_lock_sha256=sha256(paths[3]))
    fixture["frames"].pop()
    file.write_text(json.dumps(fixture), encoding="utf-8")
    with pytest.raises(ValueError, match="47 frames"):
        load_fixture(file, expected_mp4_sha256=sha256(paths[0]),
                     expected_checkpoint_sha256=sha256(paths[1]),
                     expected_config_sha256=sha256(paths[2]),
                     expected_lock_sha256=sha256(paths[3]))


def test_adapter_reconstructs_current_context_and_preserves_detection(tmp_path):
    _, _, fixture = fixture_files(tmp_path)
    service = PrecomputedInferenceService(fixture)
    frame = SimpleNamespace(frame_id=0, timestamp=9.25)
    result = service.infer_frame(frame, source="mp4:current")
    assert len(result) == 1
    assert (result[0].frame_id, result[0].timestamp, result[0].source) == (0, 9.25, "mp4:current")
    assert detection_template(result[0]) == fixture["frames"][0]["detections"][0]
    assert service.infer_frame(SimpleNamespace(frame_id=1, timestamp=8.0), source="mp4:current") == []
    with pytest.raises(ValueError, match="no frame"):
        service.infer_frame(SimpleNamespace(frame_id=47, timestamp=0), source="mp4:current")


def test_one_cycle_semantic_signature_ignores_timing_and_event_uuid(tmp_path):
    root = tmp_path / "run"
    (root / "outputs").mkdir(parents=True)
    (root / "metrics").mkdir()
    summary = {
        "total_frames": 1, "detection_classes": {"person": 1},
        "track_ids_by_frame": {"0": [1]}, "track_details_by_frame": {"0": []},
        "associations": [], "association_candidates": [],
        "compliance_findings": {}, "candidate_findings": {},
        "events": [{"event_id": "arbitrary", "event_type": "PPE_UNKNOWN", "track_id": 1,
                    "frame_id": 0, "source_timestamp": 0.0, "confidence": 0.0,
                    "snapshot_sha256": "same"}],
        "sqlite_count": 1, "total_snapshots": 1, "alert_success": 2,
    }
    (root / "outputs/full_chain.json").write_text(json.dumps(summary), encoding="utf-8")
    (root / "metrics/frames.jsonl").write_text(json.dumps({"detections": 1, "tracks": 1,
                                                               "associations": 0, "elapsed_ms": 999}), encoding="utf-8")
    signature = semantic_signature(root)
    assert signature["detection_total"] == 1
    assert signature["events"][0]["event_type"] == "PPE_UNKNOWN"
    assert "event_id" not in signature["events"][0]


def test_pacing_is_diagnostic_only():
    from scripts.run_p9b_full_chain import diagnostic_cycle_pause
    assert diagnostic_cycle_pause(cycle_elapsed=0.5, target_period=8.0, remaining_duration=20) == 7.5
    assert diagnostic_cycle_pause(cycle_elapsed=9, target_period=8.0, remaining_duration=20) == 0
    assert diagnostic_cycle_pause(cycle_elapsed=0.5, target_period=8.0, remaining_duration=2) == 2
