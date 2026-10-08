"""Fast deterministic checks for attribution-only diagnostics."""

from __future__ import annotations

from types import SimpleNamespace
import json
import tracemalloc

from core.schemas.alerts import AlertMessage, AlertStatus
from core.schemas.compliance import ComplianceEventType
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from scripts.run_p9c3_memory_attribution import MemoryProbe, count_state, stateless_alerts
from scripts.analyze_p9c3_attribution import slope


def message(index: int) -> AlertMessage:
    return AlertMessage(
        event_id=f"EVT-{index:032x}", timestamp="2026-09-25T00:00:00Z",
        track_id=1, alert_type=ComplianceEventType.PPE_UNKNOWN,
        confidence=0.0, snapshot=None, message="diagnostic",
    )


def test_stateless_adapter_does_not_retain_event_ids() -> None:
    console, web = stateless_alerts()
    for index in range(10000):
        assert console.send(message(index)).status is AlertStatus.DELIVERED
        assert web.send(message(index)).status is AlertStatus.DELIVERED
    assert not hasattr(console, "_completed")
    assert not hasattr(web, "_completed")
    assert web.history() == ()


def test_container_counter_extracts_production_and_harness_state() -> None:
    console = ConsoleAlertAdapter(sink=lambda _: None)
    web = WebAlertAdapter(max_history=2)
    for index in range(3):
        console.send(message(index))
        web.send(message(index))
    temporal = SimpleNamespace(_states={})
    engine = SimpleNamespace(_active={}, _recovery_counts={}, _last_recovered={}, temporal_filter=temporal)
    event = SimpleNamespace(engine=engine)
    tracker = SimpleNamespace(_backend=None)
    service = SimpleNamespace(event_service=event, tracker=tracker,
                              status=lambda: SimpleNamespace(recent_events=(1, 2)))
    recorder = SimpleNamespace(cycle=3, events={}, timeline=[1], stage_samples=[1], frame_summaries=[1])
    counts = count_state(service, console, web, recorder)
    assert counts["alert_console_completed"] == 3
    assert counts["alert_web_completed"] == 3
    assert counts["web_history"] == 2
    assert counts["monitor_recent_events"] == 2
    assert counts["event_active"] == 0
    assert counts["tracker_active"] == "UNSUPPORTED"
    assert counts["harness_cycles"] == 3


def test_probe_slope_uses_warm_samples_only() -> None:
    rows = [
        {"elapsed_s": 0, "rss": 1000 * 1024**2},
        {"elapsed_s": 120, "rss": 100 * 1024**2},
        {"elapsed_s": 180, "rss": 102 * 1024**2},
        {"elapsed_s": 240, "rss": 104 * 1024**2},
    ]
    assert slope(rows, "rss") == 2.0


def test_memory_probe_streams_sample_without_retaining_rows(tmp_path) -> None:
    class Process:
        @staticmethod
        def memory_info():
            return SimpleNamespace(rss=123, vms=456, private=400)

        @staticmethod
        def num_threads():
            return 2

        @staticmethod
        def num_handles():
            return 3

        @staticmethod
        def open_files():
            return []

    if not tracemalloc.is_tracing():
        tracemalloc.start(1)
    probe = MemoryProbe(marks=())
    probe.attach(root=tmp_path, service=None, console=None, web=None, recorder=None)
    probe.sample(elapsed=1.0, cycle=4, process=Process())
    probe.finish(elapsed=1.0)
    row = json.loads((tmp_path / "attribution/probe.jsonl").read_text())
    assert row["cycle"] == 4
    assert row["rss"] == 123
    assert row["alert_console_completed"] == "UNSUPPORTED"
    assert probe.snapshots == {}
