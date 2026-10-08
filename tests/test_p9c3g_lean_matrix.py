"""Fast deterministic guards for the four-cell lean interaction matrix."""

from __future__ import annotations

from pathlib import Path

from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from diagnostics.p9c3a_precomputed import PrecomputedInferenceService, sha256
from diagnostics.p9c3b_precomputed_tracking import PrecomputedTrackingAdapter
from diagnostics.p9c3g_cached_source import CachedSourceFactory
from scripts.analyze_p9c3g_matrix import contrasts, regression, shape_candidate
from scripts.compare_p9c3g_smokes import signature
from scripts.run_p9c3g_lean_matrix import (DETECTION_PATH, TRACK_PATH, VIDEO,
                                            build_matrix_graph, load_verified_fixtures)
from scripts.sample_p9c3f_process import FIELDS
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringService


def graph(cell: str, tmp_path: Path):
    detection, track = load_verified_fixtures(cell)
    return build_matrix_graph(cell, tmp_path / cell, CachedSourceFactory(None, ()), detection, track)


def test_unified_builder_has_four_cells(tmp_path: Path) -> None:
    assert all(isinstance(graph(cell, tmp_path), MonitoringService) for cell in ("PP", "PR", "RP", "RR"))


def test_pp_wiring(tmp_path: Path) -> None:
    item = graph("PP", tmp_path)
    assert isinstance(item.inference_service, PrecomputedInferenceService)
    assert isinstance(item.tracker, PrecomputedTrackingAdapter)


def test_pr_wiring(tmp_path: Path) -> None:
    item = graph("PR", tmp_path)
    assert isinstance(item.inference_service, PrecomputedInferenceService)
    assert isinstance(item.tracker, ByteTrackPersonTrackingAdapter)


def test_rp_wiring(tmp_path: Path) -> None:
    item = graph("RP", tmp_path)
    assert isinstance(item.inference_service, InferenceService)
    assert isinstance(item.tracker, PrecomputedTrackingAdapter)


def test_rr_wiring(tmp_path: Path) -> None:
    item = graph("RR", tmp_path)
    assert isinstance(item.inference_service, InferenceService)
    assert isinstance(item.tracker, ByteTrackPersonTrackingAdapter)


def test_fixtures_match_current_frozen_model_and_track_config() -> None:
    detection, track = load_verified_fixtures("PP")
    assert detection["total_frames"] == track["total_frames"] == 47
    assert detection["total_detections"] == 77
    assert track["total_tracks"] == 66
    assert detection["source_mp4_sha256"] == sha256(VIDEO)
    assert track["detection_fixture_sha256"] == sha256(DETECTION_PATH)
    assert sha256(TRACK_PATH) == "0e42709fab781ba79eb135da09789212ff932e7ee412c33c0b571919f8ec76c1"


def test_all_four_share_formal_downstream_types(tmp_path: Path) -> None:
    items = [graph(cell, tmp_path) for cell in ("PP", "PR", "RP", "RR")]
    fields = ("association_adapter", "compliance_service", "event_service",
              "ingest_service", "snapshot_service", "alert_service")
    assert len({tuple(type(getattr(item, field)) for field in fields) for item in items}) == 1
    assert len({type(item.event_service.store) for item in items}) == 1


def test_no_heavy_observer_imports() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts/run_p9c3g_lean_matrix.py").read_text(encoding="utf-8")
    for forbidden in ("ObservedMonitoringService", "BoundedRecorder", "tracemalloc", "gc.get_objects", "TimedAlertAdapter"):
        assert forbidden not in source


def test_external_sampler_schema_reused() -> None:
    assert FIELDS == ("timestamp_utc", "elapsed_s", "rss_bytes", "vms_bytes",
                      "private_bytes", "cpu_percent", "threads", "handles", "open_files")


def test_matrix_analysis_contrasts_and_shape() -> None:
    rows = {cell: {"rss_slope_2_20_mib_per_cycle": value} for cell, value in
            {"PP": 0.01, "PR": 0.03, "RP": 0.02, "RR": 0.09}.items()}
    result = contrasts(rows)
    assert round(result["factorial_interaction_direction"], 8) == 0.05
    assert regression([(0, 1), (1, 3), (2, 5)]) == 2
    windows = [{"rss_mib": {"mean": value}} for value in (1, 2, 3)]
    assert shape_candidate(windows, 0.1) == "MONOTONIC_RISE"


def test_semantic_signature_excludes_clock_and_uuid() -> None:
    result = {key: 1 for key in ("cycles", "frames", "detections", "tracks",
                                 "associations", "unknown_associations", "events",
                                 "snapshot_files_verified", "alerts_delivered", "alerts_failed")}
    result.update({"semantic_events": [{"type": "PPE_UNKNOWN"}], "wall_clock": "now", "uuid": "random"})
    assert "uuid" not in signature(result) and "wall_clock" not in signature(result)
