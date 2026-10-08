"""Fast contracts for the diagnostic N-harness bridge; no long-run test."""

from __future__ import annotations

import inspect
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from diagnostics.p9c3d_stages import stage_components
from scripts.analyze_p9c3e_harness_bridge import analyze_probe, compare_semantics
from scripts.run_p9b_full_chain import BoundedRecorder, RollingStreamList
from scripts.run_p9c3e_harness_bridge import BridgeProbe, recorder_cardinalities, run_bridge


def test_bridge_reuses_historical_run_with_precomputed_inputs(monkeypatch):
    import scripts.run_p9c3e_harness_bridge as bridge
    seen = {}
    monkeypatch.setattr(bridge, "cached_mp4_frames", lambda: ("metadata", ("frame",)))
    monkeypatch.setattr(bridge, "load_fixtures", lambda: ("detection", "track"))
    monkeypatch.setattr(bridge, "PrecomputedInferenceService", lambda value: ("precomputed_detection", value))
    monkeypatch.setattr(bridge, "PrecomputedTrackingAdapter", lambda value: ("precomputed_track", value))

    def fake_run(**kwargs):
        seen.update(kwargs)
        return {"run_root": "artifacts/p9c3/fake", "observer_counts": {"cycles": 1},
                "total_frames": 47, "total_events": 1, "sqlite_count": 1,
                "total_snapshots": 1, "alert_success": 2, "elapsed_seconds": 1.0}

    monkeypatch.setattr(bridge, "run", fake_run)
    result = run_bridge(seconds=1200, smoke=False)
    assert result["events"] == 1
    assert seen["metrics"] is seen["bounded"] is True
    assert seen["diagnostic_inference_service"] == ("precomputed_detection", "detection")
    assert seen["diagnostic_tracker"] == ("precomputed_track", "track")
    assert seen["diagnostic_cycle_period_seconds"] == 8.0
    assert isinstance(seen["diagnostic_probe"], BridgeProbe)


def test_s4_and_bridge_business_type_contract():
    from scripts.run_p9c3d_downstream_stages import load_fixtures
    detection, tracks = load_fixtures()
    s4 = stage_components("S4", detection_fixture=detection, track_fixture=tracks)
    assert type(s4["inference_service"]).__name__ == "PrecomputedInferenceService"
    assert type(s4["tracker"]).__name__ == "PrecomputedTrackingAdapter"
    assert type(s4["association_adapter"]).__name__ == "PPEPersonAssociationAdapter"
    assert type(s4["compliance_service"]).__name__ == "ComplianceService"


def test_recorder_and_rolling_logs_are_capped_and_streamed(tmp_path):
    recorder = BoundedRecorder(tmp_path, limit=3)
    for index in range(10):
        recorder.track_ids[index] = [index]
        recorder.associations.append({"frame_id": index})
        recorder.timeline.append({"index": index})
    cardinalities = recorder_cardinalities(recorder)
    assert cardinalities["track_ids"]["length"] == 3
    assert cardinalities["associations"] == {"length": 3, "cap": 3, "lines_written": 10}
    assert cardinalities["timeline"]["length"] == 3
    recorder.close()
    assert len((tmp_path / "metrics/associations.jsonl").read_text().splitlines()) == 10
    assert len((tmp_path / "metrics/timeline.jsonl").read_text().splitlines()) == 10


def test_probe_line_counter_reads_only_new_bytes(tmp_path):
    path = tmp_path / "events.jsonl"
    probe = BridgeProbe()
    path.write_bytes(b"a\nb\n")
    assert probe.streamed_lines(path) == 2
    with path.open("ab") as handle:
        handle.write(b"c\n")
    assert probe.streamed_lines(path) == 3


def test_recorder_has_no_image_or_frame_history(tmp_path):
    recorder = BoundedRecorder(tmp_path)
    try:
        assert not hasattr(recorder, "frames")
        assert not hasattr(recorder, "images")
        assert all("frame" not in name or name == "frame_summaries"
                   for name in recorder_cardinalities(recorder))
        assert "append_many" not in inspect.getsource(BridgeProbe.sample)
    finally:
        recorder.close()


def _semantic_root(root: Path, *, harness: str, event_type="PPE_UNKNOWN"):
    (root / "database").mkdir(parents=True)
    connection = sqlite3.connect(root / "database/events.sqlite3")
    connection.execute("CREATE TABLE events (track_id INT,event_type TEXT,confidence REAL,source_timestamp REAL,frame_id INT,bbox_json TEXT)")
    connection.execute("CREATE TABLE snapshots (sha256 TEXT,width INT,height INT,captured_at TEXT)")
    connection.execute("INSERT INTO events VALUES (1,?,?,1.001,24,?)",
                       (event_type, 0.0, json.dumps({"x1": 1})))
    connection.execute("INSERT INTO snapshots VALUES ('abc',1280,720,'now')")
    connection.commit()
    connection.close()
    status = {"detections": 77, "tracks": 66, "associations": 1,
              "unknown_associations": 1, "alerts_delivered": 2, "alerts_failed": 0}
    summary = {"compliance_findings": {"PPE_UNKNOWN:unknown": 66},
               "candidate_findings": {"PPE_UNKNOWN": 66}}
    if harness == "H":
        summary.update(status=status, total_frames=47, alert_success=2, alert_failure=0)
        path = root / "outputs/full_chain.json"
    else:
        summary.update(final_status=status, frames=47)
        path = root / "attribution/summary.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(summary), encoding="utf-8")


def test_semantic_gate_detects_business_difference(tmp_path):
    s4, h = tmp_path / "s4", tmp_path / "h"
    _semantic_root(s4, harness="S4")
    _semantic_root(h, harness="H")
    assert compare_semantics(s4, h)["pass"] is True
    connection = sqlite3.connect(h / "database/events.sqlite3")
    connection.execute("UPDATE events SET event_type='NO_HELMET'")
    connection.commit()
    connection.close()
    result = compare_semantics(s4, h)
    assert result["pass"] is False and "events" in result["differences"]


def test_window_analysis_uses_cycle_and_event_normalization(tmp_path):
    path = tmp_path / "probe.jsonl"
    rows = [{"elapsed_s": minute * 60, "cycle": minute * 7,
             "frames": minute * 329, "events": minute * 7,
             "sqlite_rows": minute * 7, "snapshots": minute * 7,
             "alert_deliveries": minute * 14,
             "rss": (180 + minute * 0.14) * 2**20,
             "traced_current": minute * 10000,
             "threads": 2, "handles": 10, "open_files": 1,
             "alert_console_completed": minute * 7,
             "alert_web_completed": minute * 7,
             "web_history": min(200, minute * 7),
             "monitor_recent_events": 1}
            for minute in range(21)]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    result = analyze_probe(path)
    assert result["windows"]["10-20"]["samples"] == 10
    assert result["rss_mib_per_cycle_2on"] == pytest.approx(0.02)
    assert result["rss_mib_per_event_2on"] == pytest.approx(0.02)


def test_bridge_remains_outside_production_defaults():
    from services.monitoring_service import MonitoringService
    source = inspect.getsource(MonitoringService)
    assert "BridgeProbe" not in source
    assert "BoundedRecorder" not in source
