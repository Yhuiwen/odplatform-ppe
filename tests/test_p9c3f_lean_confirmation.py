"""Fast deterministic guards for the lean confirmation harness."""

from __future__ import annotations

import io
import json
from pathlib import Path

from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from scripts.analyze_p9c3f_lean_resources import classify_window_shape, slope
from scripts.run_p9c3f_lean_full_graph import build_lean_graph, cycle_summary, stream_cycle
from scripts.sample_p9c3f_process import FIELDS
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringService, MonitoringState


def test_lean_graph_uses_formal_components(tmp_path: Path) -> None:
    graph = build_lean_graph(tmp_path)
    assert isinstance(graph, MonitoringService)
    assert isinstance(graph.inference_service, InferenceService)
    assert isinstance(graph.tracker, ByteTrackPersonTrackingAdapter)
    assert isinstance(graph.association_adapter, PPEPersonAssociationAdapter)
    assert all("Observed" not in type(value).__name__ for value in vars(graph).values())


def test_lean_launcher_omits_fixture_and_heavy_diagnostics() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts/run_p9c3f_lean_full_graph.py").read_text(encoding="utf-8")
    for forbidden in ("DetectionFixture", "TrackFixture", "ObservedMonitoringService", "BoundedRecorder", "tracemalloc", "gc.collect"):
        assert forbidden not in source


def test_sampler_schema_is_external_and_minimal() -> None:
    assert FIELDS == ("timestamp_utc", "elapsed_s", "rss_bytes", "vms_bytes", "private_bytes", "cpu_percent", "threads", "handles", "open_files")


def test_sampler_streams_without_history_container() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts/sample_p9c3f_process.py").read_text(encoding="utf-8")
    assert 'output.open("w", newline="", encoding="utf-8")' in source
    assert "writer.writerow(row)" in source and "handle.flush()" in source
    assert "rows.append" not in source and "samples.append" not in source


def test_cycle_summary_contains_only_approved_fields() -> None:
    class Status:
        frames_processed = 47
        detections = 77
        tracks = 66
        associations = 1
        events_generated = 1
        alerts_delivered = 2
        alerts_failed = 0
        state = MonitoringState.COMPLETED
    result = cycle_summary(1, 0.0, 5.0, Status())
    assert set(result) == {"cycle_index", "start_elapsed_s", "end_elapsed_s", "frames_processed", "detections", "tracks", "associations", "events", "alerts_delivered", "alerts_failed", "final_state"}


def test_cycle_writer_appends_one_json_line() -> None:
    handle = io.StringIO()
    stream_cycle(handle, {"cycle_index": 1, "frames_processed": 47})
    assert json.loads(handle.getvalue()) == {"cycle_index": 1, "frames_processed": 47}
    assert handle.getvalue().count("\n") == 1


def test_window_slope_on_synthetic_linear_samples() -> None:
    rows = [{"elapsed_s": minute * 60, "rss_mib": 400 + minute * 0.5} for minute in range(60)]
    assert slope(rows, 10, 60) == 0.5
    assert slope(rows, 20, 60) == 0.5
    assert slope(rows, 30, 60) == 0.5


def test_shape_candidates() -> None:
    assert classify_window_shape([400, 410, 420, 430, 440]) == "SUSPICIOUS_CONTINUED_GROWTH"
    assert classify_window_shape([400, 410, 420, 419, 418]) == "BOUNDED_HIGH_WATER"
    assert classify_window_shape([400, 401, 400, 401, 400]) == "STABLE_PLATEAU"
    assert classify_window_shape([400]) == "INCONCLUSIVE"
