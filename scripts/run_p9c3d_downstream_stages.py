"""Diagnostic-only staged MonitoringService lifecycle attribution."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import threading
import tracemalloc
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import psutil

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from diagnostics.p9c3a_precomputed import load_fixture, sha256
from diagnostics.p9c3b_precomputed_tracking import load_track_fixture
from diagnostics.p9c3d_stages import (
    NoAlert, NoSnapshot, SourceFactory, UnusedIngest, stage_components,
)
from scripts.run_p9b_full_chain import diagnostic_cycle_pause
from scripts.run_p9c3_memory_attribution import VIDEO, cached_mp4_frames
from services.monitoring_service import (
    MonitoringService, MonitoringSourceRequest, MonitoringState, MonitoringStatus,
)
from core.schemas.video import SourceType
from core.schemas.events import EventQuery


def load_fixtures():
    detection_path = ROOT / "artifacts/p9c3/p9c3a-real-detections.json"
    detection = load_fixture(
        detection_path, expected_mp4_sha256=sha256(VIDEO),
        expected_checkpoint_sha256=sha256(ROOT / "models/checkpoints/EXP-001/best.pt"),
        expected_config_sha256=sha256(ROOT / "configs/inference.yaml"),
        expected_lock_sha256=sha256(ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"),
    )
    track = load_track_fixture(
        ROOT / "artifacts/p9c3/p9c3b-real-tracks.json",
        detection_sha256=sha256(detection_path),
        tracker_config_sha256=sha256(ROOT / "configs/tracker.yaml"),
        ultralytics_version=version("ultralytics"), lap_version=version("lap"),
    )
    return detection, track


class ComplianceTap:
    """One-cycle semantic gate only; never used in formal S-stage screens."""

    def __init__(self, target):
        self.target = target
        self.findings = Counter()
        self.candidates = Counter()

    def evaluate(self, association):
        result = self.target.evaluate(association)
        self.findings.update(f"{item.event_type.value}:{item.state.value}"
                             for item in result.findings)
        self.candidates.update(item.event_type.value
                               for item in result.candidate_findings)
        return result


def build_stage(stage: str, root: Path, source_factory: SourceFactory,
                detection=None, track=None, *, real_tracker=False, semantic=False):
    parts = stage_components(stage, detection_fixture=detection,
                             track_fixture=track, real_tracker=real_tracker)
    compliance_tap = ComplianceTap(parts["compliance_service"]) if semantic else None
    if compliance_tap is not None:
        parts["compliance_service"] = compliance_tap
    database = events = None
    if stage in {"S3", "S4"}:
        from infra.database.database import Database
        from infra.database.repository import EventRepository
        from services.event_ingest_service import EventIngestService
        database = Database(root / "database/events.sqlite3")
        events = EventRepository(database)
        ingest = EventIngestService(events)
    else:
        ingest = UnusedIngest()
    if stage == "S4":
        from infra.alerts.console import ConsoleAlertAdapter
        from infra.alerts.web import WebAlertAdapter
        from infra.database.snapshot_repository import SnapshotRepository
        from infra.storage.snapshot_storage import SnapshotStorage
        from services.alert_service import AlertService
        from services.snapshot_service import SnapshotService
        snapshots = SnapshotService(events, SnapshotRepository(database),
                                    SnapshotStorage(root / "snapshots"))
        alerts = AlertService((ConsoleAlertAdapter(sink=lambda line: None), WebAlertAdapter()))
    else:
        snapshots, alerts = NoSnapshot(), NoAlert()
    service = MonitoringService(
        **parts, ingest_service=ingest, snapshot_service=snapshots,
        alert_service=alerts, source_factory=source_factory,
        event_loader=events.get if events is not None else None,
    )
    return service, {"database": database, "events": events,
                     "snapshots": snapshots, "alerts": alerts,
                     "compliance_tap": compliance_tap}


def gc_counts() -> dict:
    names = {"MonitoringStatus", "Thread", "CountingCachedSource", "ndarray"}
    counts = {name: 0 for name in names}
    for obj in gc.get_objects():
        name = type(obj).__name__
        if name in counts:
            counts[name] += 1
    return counts


class Probe:
    def __init__(self, root, service, factory, counters, resources, image_ids):
        self.root, self.service, self.factory = root, service, factory
        self.counters, self.resources, self.image_ids = counters, resources, image_ids
        self.stop = threading.Event()
        self.process = psutil.Process(os.getpid())
        self.start = perf_counter()
        (root / "attribution").mkdir(exist_ok=True)
        self.out = (root / "attribution/probe.jsonl").open("w", encoding="utf-8")
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def sample(self):
        status = self.service.status()
        mem = self.process.memory_info()
        traced, peak = tracemalloc.get_traced_memory()
        event_service = self.service.event_service
        engine = getattr(event_service, "engine", None)
        temporal = getattr(engine, "temporal_filter", None)
        row = {
            "elapsed_s": perf_counter() - self.start,
            "cycle": self.counters["cycles"], "frames": self.counters["frames"],
            "events": self.counters["events"],
            "worker_created": self.counters["worker_created"],
            "worker_exited": self.counters["worker_exited"],
            "source_created": self.factory.counters["created"],
            "source_open": self.factory.counters["opens"],
            "source_close": self.factory.counters["closes"],
            "source_live": len(self.factory.live),
            "rss": mem.rss, "vms": mem.vms,
            "private": getattr(mem, "private", None),
            "threads": self.process.num_threads(), "handles": self.process.num_handles(),
            "open_files": len(self.process.open_files()),
            "traced_current": traced, "traced_peak": peak,
            "gc_objects": len(gc.get_objects()), "gc_counts": gc.get_count(),
            "gc_types": gc_counts(),
            "recent_events": len(status.recent_events),
            "latest_frame_present": status.latest_frame is not None,
            "latest_frame_cached": status.latest_frame is None or id(status.latest_frame) in self.image_ids,
            "worker_reference_alive": bool(self.service._thread and self.service._thread.is_alive()),
            "event_active": len(getattr(engine, "_active", ())),
            "event_recovery": len(getattr(engine, "_recovery_counts", ())),
            "temporal_states": len(getattr(temporal, "_states", ())),
            "tracker_cursor": getattr(self.service.tracker, "_cursor", None),
        }
        self.out.write(json.dumps(row) + "\n")
        self.out.flush()

    def _loop(self):
        while not self.stop.is_set():
            self.sample()
            self.stop.wait(5)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=6)
        self.sample()
        self.out.close()


def run(stage: str, seconds: float, *, real_tracker=False, period=8.0,
        semantic=False):
    if stage not in {"S0", "S1", "S2", "S3", "S4"} or seconds <= 0:
        raise ValueError("invalid P9-C.3d diagnostic run")
    if real_tracker and stage == "S0":
        raise ValueError("real tracker pair requires a downstream stage")
    metadata, frames = cached_mp4_frames()
    detection, track = load_fixtures() if stage != "S0" else (None, None)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3d" / run_id
    root.mkdir(parents=True)
    factory = SourceFactory(metadata, frames)
    service, resources = build_stage(stage, root, factory, detection, track,
                                     real_tracker=real_tracker, semantic=semantic)
    request = MonitoringSourceRequest(source_type=SourceType.MP4, location=str(VIDEO))
    counters = {"cycles": 0, "frames": 0, "events": 0,
                "worker_created": 0, "worker_exited": 0}
    image_ids = {id(frame.image) for frame in frames}
    tracemalloc.start(1)
    with Probe(root, service, factory, counters, resources, image_ids) as probe:
        start = probe.start
        while perf_counter() - start < seconds:
            cycle_start = perf_counter()
            service.start(request)
            counters["worker_created"] += 1
            if not service.wait(timeout=180):
                service.stop()
                raise AssertionError("MonitoringService cycle exceeded 180 seconds")
            counters["worker_exited"] += 1
            status = service.status()
            if status.state is not MonitoringState.COMPLETED or status.frames_processed != 47:
                raise AssertionError(f"incomplete {stage} cycle: {status.state}, {status.frames_processed}")
            counters["cycles"] += 1
            counters["frames"] += status.frames_processed
            counters["events"] += status.events_generated
            if factory.counters["created"] != counters["cycles"] or factory.counters["closes"] != counters["cycles"]:
                raise AssertionError("source lifecycle count mismatch")
            remaining = seconds - (perf_counter() - start)
            if remaining > 0:
                probe.stop.wait(diagnostic_cycle_pause(
                    cycle_elapsed=perf_counter() - cycle_start,
                    target_period=period, remaining_duration=remaining,
                ))
        final_status = service.status()
        final_objects = gc_counts()
    summary = {
        "stage": stage, "real_tracker": real_tracker,
        "run_root": root.relative_to(ROOT).as_posix(),
        "elapsed_seconds": perf_counter() - start,
        **counters, "sources": factory.counters,
        "sources_live_at_exit": len(factory.live),
        "final_status": final_status.to_dict(),
        "final_objects": final_objects,
        "event_confirmed_total": getattr(service.event_service, "confirmed_count", 0),
        "compliance_findings": (dict(resources["compliance_tap"].findings)
                                if resources["compliance_tap"] else None),
        "candidate_findings": (dict(resources["compliance_tap"].candidates)
                               if resources["compliance_tap"] else None),
        "sqlite_rows": resources["events"].query(EventQuery()).total_count if resources["events"] is not None else 0,
        "fixture_sha256": sha256(ROOT / "artifacts/p9c3/p9c3a-real-detections.json"),
        "track_fixture_sha256": sha256(ROOT / "artifacts/p9c3/p9c3b-real-tracks.json"),
    }
    (root / "attribution/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("S0", "S1", "S2", "S3", "S4"), required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--period", type=float, default=8)
    parser.add_argument("--real-tracker", action="store_true")
    parser.add_argument("--semantic-gate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.stage, args.seconds, real_tracker=args.real_tracker,
                         period=args.period, semantic=args.semantic_gate)))


if __name__ == "__main__":
    main()
