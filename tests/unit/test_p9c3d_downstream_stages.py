"""Fast deterministic checks for P9-C.3d diagnostic stage composition."""

from __future__ import annotations

import gc
import inspect
from types import SimpleNamespace

import pytest

from core.schemas.association import AssociationResult
from core.schemas.compliance import ComplianceResult
from diagnostics.p9c3d_stages import SourceFactory, stage_components
from scripts.analyze_p9c3d_stages import first_divergence
from scripts.run_p9b_full_chain import diagnostic_cycle_pause
from scripts.run_p9c3_memory_attribution import cached_mp4_frames
from scripts.run_p9c3d_downstream_stages import load_fixtures


def test_s0_returns_formal_empty_schemas():
    parts = stage_components("S0")
    frame = SimpleNamespace(frame_id=3, timestamp=0.25)
    assert parts["inference_service"].infer_frame(frame, source="mp4:test") == ()
    tracks = parts["tracker"].update((), frame_id=3, timestamp=0.25, source="mp4:test")
    association = parts["association_adapter"].associate(
        tracks, (), frame_id=3, timestamp=0.25, source="mp4:test")
    assert isinstance(association, AssociationResult)
    compliance = parts["compliance_service"].evaluate(association)
    assert isinstance(compliance, ComplianceResult)
    assert parts["event_service"].process(compliance) == ()


def test_cached_source_created_opened_closed_without_history():
    metadata, frames = cached_mp4_frames()
    factory = SourceFactory(metadata, frames)
    source = factory(None)
    assert source.open().source_id == metadata.source_id
    assert sum(source.read() is not None for _ in range(47)) == 47
    assert source.read() is None
    source.close()
    assert factory.counters == {"created": 1, "opens": 1, "closes": 1}
    assert len(factory.live) == 1
    del source
    assert len(factory.live) == 0


def test_stage_builder_uses_real_components_only_when_requested():
    detection, track = load_fixtures()
    s0 = stage_components("S0")
    s1 = stage_components("S1", detection_fixture=detection, track_fixture=track)
    s2 = stage_components("S2", detection_fixture=detection, track_fixture=track)
    s3 = stage_components("S3", detection_fixture=detection, track_fixture=track)
    s4 = stage_components("S4", detection_fixture=detection, track_fixture=track)
    assert type(s0["tracker"]).__name__ == "EmptyTracker"
    assert type(s1["association_adapter"]).__name__ == "PPEPersonAssociationAdapter"
    assert type(s1["event_service"]).__name__ == "EmptyEvents"
    assert s2["event_service"].emit is False
    assert s3["event_service"].emit is True
    assert s4["event_service"].emit is True
    with pytest.raises(ValueError):
        stage_components("S4")


def test_event_boundary_counts_without_emission():
    from diagnostics.p9c3d_stages import EngineEventBoundary
    boundary = EngineEventBoundary(emit=False)
    assert boundary.process(ComplianceResult(frame_id=0, timestamp=0.0)) == ()
    assert boundary.confirmed_count == 0
    boundary.reset()


def test_monitoring_source_and_worker_counters_are_explicit():
    source = inspect.getsource(__import__("scripts.run_p9c3d_downstream_stages", fromlist=["run"]).run)
    for field in ("worker_created", "worker_exited", "created", "closes"):
        assert field in source


def test_cycle_pacing():
    assert diagnostic_cycle_pause(cycle_elapsed=2, target_period=8, remaining_duration=30) == 6
    assert diagnostic_cycle_pause(cycle_elapsed=9, target_period=8, remaining_duration=30) == 0


def test_container_probe_reports_core_types():
    from scripts.run_p9c3d_downstream_stages import gc_counts
    counts = gc_counts()
    assert set(counts) == {"MonitoringStatus", "Thread", "CountingCachedSource", "ndarray"}
    assert all(isinstance(value, int) and value >= 0 for value in counts.values())


def test_first_divergence_uses_stage_order_and_rejects_unknown():
    assert first_divergence({"S4": True, "S2": True}) == "S2"
    assert first_divergence({"S1": False, "S2": False}) is None
    with pytest.raises(ValueError):
        first_divergence({"S5": True})


def test_diagnostics_not_production_defaults():
    from services.monitoring_service import MonitoringService
    source = inspect.getsource(MonitoringService)
    assert "p9c3d_stages" not in source
    assert "CountingCachedSource" not in source
