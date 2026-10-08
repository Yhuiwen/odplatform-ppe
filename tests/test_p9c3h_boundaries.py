"""Fast structural and analysis guards for P9-C.3h diagnostic controls."""

from pathlib import Path

import pytest

from scripts.analyze_p9c3h_boundaries import adjacent_differences
from scripts.run_p9c3h_boundaries import build_graph, start_sampler
from scripts.run_p9c3f_lean_full_graph import start_sampler as original_sampler
from scripts.run_p9c3g_lean_matrix import build_matrix_graph


@pytest.mark.parametrize("stage", ["H0", "H1", "H2", "H3", "H4", "H5", "RP"])
def test_staged_graph_uses_common_upstream(stage, tmp_path):
    service, taps = build_graph(stage, tmp_path, lambda _: None, {"frames": []})
    assert type(service.inference_service).__name__ == "InferenceService"
    assert type(service.tracker).__name__ == "PrecomputedTrackingAdapter"
    assert taps == {}
    assert type(service).__name__ == "MonitoringService"


def test_stage_boundaries(tmp_path):
    graph = lambda stage: build_graph(stage, tmp_path / stage, lambda _: None,
                                      {"frames": []})[0]
    h0, h1, h2, h3, h4, h5 = (graph(x) for x in ("H0", "H1", "H2", "H3", "H4", "H5"))
    assert type(h0.association_adapter).__name__ == "EmptyAssociation"
    assert type(h0.compliance_service).__name__ == "EmptyCompliance"
    assert type(h1.association_adapter).__name__ == "PPEPersonAssociationAdapter"
    assert type(h1.compliance_service).__name__ == "ComplianceService"
    assert type(h1.event_service).__name__ == "EmptyEvents"
    assert type(h2.event_service).__name__ == "EventService"
    assert type(h2.ingest_service).__name__ == "DiagnosticIngest"
    assert type(h3.ingest_service).__name__ == "EventIngestService"
    assert type(h3.snapshot_service).__name__ == "DiagnosticSnapshot"
    assert type(h4.snapshot_service).__name__ == "SnapshotService"
    assert type(h4.alert_service).__name__ == "DiagnosticAlerts"
    assert type(h5.alert_service).__name__ == "AlertService"
    assert all(type(s.event_service.store).__name__ == "JSONEventStore"
               for s in (h2, h3, h4, h5))


def test_semantic_taps_only_for_smoke(tmp_path):
    service, taps = build_graph("H2", tmp_path, lambda _: None,
                                {"frames": []}, semantic=True)
    assert set(taps) == {"association", "compliance"}
    assert service.association_adapter is taps["association"]


def test_analyzer_has_no_threshold():
    assert adjacent_differences({"H0": 0.01, "H1": 0.02,
                                 "H2": 0.10, "RP": 0.11}) == {
        "H0_to_H1": pytest.approx(0.01),
        "H1_to_H2": pytest.approx(0.08),
        "H2_to_RP": pytest.approx(0.01),
    }


def test_no_heavy_observer_imports():
    runner = (Path(__file__).resolve().parents[1] /
              "scripts/run_p9c3h_boundaries.py").read_text(encoding="utf-8")
    for forbidden in ("tracemalloc", "gc.get_objects", "BoundedRecorder", "ObservedInference"):
        assert forbidden not in runner


def test_external_sampler_is_unchanged():
    assert start_sampler is original_sampler


def test_rp_baseline_wiring_equivalence(tmp_path):
    fixture = {"frames": []}
    staged, _ = build_graph("RP", tmp_path / "h", lambda _: None, fixture)
    original = build_matrix_graph("RP", tmp_path / "g", lambda _: None, None, fixture)
    for name in ("inference_service", "tracker", "association_adapter",
                 "compliance_service", "event_service", "ingest_service",
                 "snapshot_service", "alert_service"):
        assert type(getattr(staged, name)) is type(getattr(original, name))
    assert type(staged.event_service.store) is type(original.event_service.store)
    assert type(staged.event_service.engine) is type(original.event_service.engine)
    assert len(staged.alert_service.adapters) == len(original.alert_service.adapters)


