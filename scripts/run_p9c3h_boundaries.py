"""Lean real-inference downstream boundary controls; diagnostic only."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.events.event_engine import EventEngine
from core.schemas.association import AssociationResult
from core.schemas.compliance import ComplianceResult
from core.schemas.events import EventStatus, PersistedEvent, format_utc_timestamp
from core.schemas.video import SourceType
from diagnostics.p9c3b_precomputed_tracking import PrecomputedTrackingAdapter
from diagnostics.p9c3g_cached_source import CachedSourceFactory, load_cached_frames
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.json_event_store import JSONEventStore
from infra.storage.snapshot_storage import SnapshotStorage
from scripts.run_p9c3f_lean_full_graph import cycle_summary, start_sampler, stream_cycle
from scripts.run_p9c3g_lean_matrix import VIDEO, load_verified_fixtures
from services.alert_service import AlertService
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService
from services.event_service import EventService
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringService, MonitoringSourceRequest, MonitoringState
from services.snapshot_service import SnapshotService

STAGES = ("H0", "H1", "H2", "H3", "H4", "H5", "RP")


class EmptyAssociation:
    def associate(self, tracks, ppe, *, frame_id, timestamp, source):
        return AssociationResult(frame_id=frame_id, timestamp=timestamp, source=source)


class EmptyCompliance:
    def evaluate(self, association):
        return ComplianceResult(frame_id=association.frame_id, timestamp=association.timestamp)


class EmptyEvents:
    def process(self, compliance):
        return ()


class DiagnosticIngest:
    """Return a transient valid projection without retaining business events."""

    def ingest(self, event, **_context):
        return PersistedEvent(id=event.event_id,
                              timestamp=format_utc_timestamp(datetime.now(timezone.utc)),
                              track_id=event.track_id, type=event.event_type,
                              confidence=event.confidence, snapshot=None,
                              status=EventStatus.OPEN)


class DiagnosticSnapshot:
    def capture(self, event_id, image):
        return SimpleNamespace(relative_path="diagnostic/no-snapshot")


class DiagnosticAlerts:
    def dispatch_event(self, event):
        return ()


class SemanticTap:
    """One-cycle gate only; never installed in timed controls."""

    def __init__(self, target, method):
        self.target, self.method = target, method
        self.records = []

    def associate(self, *args, **kwargs):
        result = self.target.associate(*args, **kwargs)
        if result.associations or result.unknown_count:
            self.records.append({"frame_id": result.frame_id,
                                 "associations": len(result.associations),
                                 "unknown": result.unknown_count})
        return result

    def evaluate(self, association):
        result = self.target.evaluate(association)
        if result.findings or result.candidate_findings:
            self.records.append({"frame_id": result.frame_id,
                                 "findings": [(x.event_type.value, x.state.value)
                                              for x in result.findings],
                                 "candidates": [x.event_type.value
                                                for x in result.candidate_findings]})
        return result


def build_graph(stage: str, root: Path, source_factory: CachedSourceFactory,
                track_fixture: dict, *, semantic: bool = False):
    if stage not in STAGES:
        raise ValueError("invalid downstream boundary")
    inference = InferenceService(config_path="configs/inference.yaml", execution_enabled=True)
    tracker = PrecomputedTrackingAdapter(track_fixture)
    association = EmptyAssociation() if stage == "H0" else PPEPersonAssociationAdapter()
    compliance = EmptyCompliance() if stage == "H0" else ComplianceService()
    taps = {}
    if semantic and stage != "H0":
        taps["association"] = SemanticTap(association, "associate")
        taps["compliance"] = SemanticTap(compliance, "evaluate")
        association, compliance = taps["association"], taps["compliance"]
    event_service = (EmptyEvents() if stage in {"H0", "H1"} else
                     EventService(engine=EventEngine(),
                                  store=JSONEventStore(root / "logs/events.jsonl")))
    database = events = None
    if stage in {"H3", "H4", "H5", "RP"}:
        database = Database(root / "database/events.sqlite3")
        events = EventRepository(database)
    ingest = EventIngestService(events) if events is not None else DiagnosticIngest()
    if stage in {"H4", "H5", "RP"}:
        snapshot = SnapshotService(events, SnapshotRepository(database),
                                   SnapshotStorage(root / "snapshots"))
    else:
        snapshot = DiagnosticSnapshot()
    alerts = (AlertService((ConsoleAlertAdapter(sink=lambda _line: None),
                            WebAlertAdapter())) if stage in {"H5", "RP"}
              else DiagnosticAlerts())
    service = MonitoringService(
        inference_service=inference, tracker=tracker,
        association_adapter=association, compliance_service=compliance,
        event_service=event_service, ingest_service=ingest,
        snapshot_service=snapshot, alert_service=alerts,
        event_loader=events.get if events is not None else None,
        source_factory=source_factory,
    )
    return service, taps


def run(stage: str, *, seconds: float = 600, period: float = 8,
        smoke: bool = False) -> dict:
    if stage not in STAGES or seconds <= 0 or period <= 0:
        raise ValueError("invalid control run")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3h" / f"{stage.lower()}-{run_id}"
    for name in ("database", "snapshots", "logs", "resources", "outputs"):
        (root / name).mkdir(parents=True, exist_ok=False)
    metadata, frames = load_cached_frames(VIDEO)
    factory = CachedSourceFactory(metadata, frames)
    _detection, track = load_verified_fixtures("RP")
    service, taps = build_graph(stage, root, factory, track, semantic=smoke)
    request = MonitoringSourceRequest(source_type=SourceType.MP4, location=str(VIDEO))
    sampler, sampler_output, stop_file = start_sampler(root)
    print(json.dumps({"stage": stage, "run_root": root.relative_to(ROOT).as_posix(),
                      "business_pid": os.getpid(), "sampler_pid": sampler.pid}), flush=True)
    started = monotonic()
    counters = {"completed_cycles": 0, "frames": 0, "detections": 0, "tracks": 0,
                "associations": 0, "unknown_associations": 0, "events": 0,
                "alerts_delivered": 0, "alerts_failed": 0}
    failure = None
    try:
        with (root / "outputs/cycles.jsonl").open("w", encoding="utf-8") as handle:
            while counters["completed_cycles"] == 0 or (not smoke and monotonic() - started < seconds):
                cycle_start = monotonic() - started
                service.start(request)
                if not service.wait(timeout=180):
                    service.stop()
                    failure = "cycle_timeout"
                    break
                status = service.status()
                if status.state is not MonitoringState.COMPLETED or status.frames_processed != 47:
                    failure = f"incomplete_cycle:{status.state.value}:{status.frames_processed}"
                    break
                counters["completed_cycles"] += 1
                for target, source in (("frames", "frames_processed"), ("detections", "detections"),
                                       ("tracks", "tracks"), ("associations", "associations"),
                                       ("unknown_associations", "unknown_associations"),
                                       ("events", "events_generated"),
                                       ("alerts_delivered", "alerts_delivered"),
                                       ("alerts_failed", "alerts_failed")):
                    counters[target] += getattr(status, source)
                stream_cycle(handle, cycle_summary(counters["completed_cycles"], cycle_start,
                                                   monotonic() - started, status))
                remaining = period - (monotonic() - started - cycle_start)
                if remaining > 0:
                    sleep(min(remaining, max(0, seconds - (monotonic() - started)) if not smoke else remaining))
                if smoke:
                    break
    finally:
        if not service.wait(timeout=0):
            service.stop()
        stop_file.write_text("stop\n", encoding="utf-8")
        sampler.wait(timeout=15)
    summary = {"stage": stage, "mode": "smoke" if smoke else "formal",
               "run_root": root.relative_to(ROOT).as_posix(),
               "elapsed_seconds": monotonic() - started, "period_seconds": period,
               **counters, "source_created": factory.created,
               "final_status": service.status().to_dict(),
               "worker_exited": service.wait(timeout=0), "failure": failure,
               "sampler_exit_code": sampler.returncode,
               "sampler_samples": max(0, sum(1 for _ in sampler_output.open(encoding="utf-8")) - 1),
               "semantic": {name: tap.records for name, tap in taps.items()},
               "event_lines": (sum(1 for _ in (root / "logs/events.jsonl").open(encoding="utf-8"))
                               if (root / "logs/events.jsonl").exists() else 0)}
    (root / "outputs/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"final_status", "semantic"}}), flush=True)
    if failure or sampler.returncode != 0 or not summary["worker_exited"]:
        raise RuntimeError(f"boundary run failed: {failure}, sampler={sampler.returncode}")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--period", type=float, default=8)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    run(args.stage, seconds=args.seconds, period=args.period, smoke=args.smoke)


if __name__ == "__main__":
    main()
