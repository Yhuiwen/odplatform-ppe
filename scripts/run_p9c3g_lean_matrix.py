"""Unified lean PP/PR/RP/RR cached-frame full-business interaction matrix."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.events.event_engine import EventEngine
from core.schemas.video import SourceType
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from diagnostics.p9c3a_precomputed import PrecomputedInferenceService, load_fixture, sha256
from diagnostics.p9c3b_precomputed_tracking import PrecomputedTrackingAdapter, load_track_fixture
from diagnostics.p9c3g_cached_source import CachedSourceFactory, load_cached_frames
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.json_event_store import JSONEventStore
from infra.storage.snapshot_storage import SnapshotStorage
from scripts.run_p9c3f_lean_full_graph import cycle_summary, start_sampler, stream_cycle
from services.alert_service import AlertService
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService
from services.event_service import EventService
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringService, MonitoringSourceRequest, MonitoringState
from services.snapshot_service import SnapshotService

VIDEO = ROOT / "artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4"
DETECTION_PATH = ROOT / "artifacts/p9c3/p9c3a-real-detections.json"
TRACK_PATH = ROOT / "artifacts/p9c3/p9c3b-real-tracks.json"
CELLS = ("PP", "PR", "RP", "RR")


def load_verified_fixtures(cell: str) -> tuple[dict | None, dict | None]:
    if cell not in CELLS:
        raise ValueError("cell must be PP, PR, RP or RR")
    detection = None
    track = None
    if cell in {"PP", "PR"}:
        detection = load_fixture(
            DETECTION_PATH, expected_mp4_sha256=sha256(VIDEO),
            expected_checkpoint_sha256=sha256(ROOT / "models/checkpoints/EXP-001/best.pt"),
            expected_config_sha256=sha256(ROOT / "configs/inference.yaml"),
            expected_lock_sha256=sha256(ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"),
        )
    if cell in {"PP", "RP"}:
        track = load_track_fixture(
            TRACK_PATH, detection_sha256=sha256(DETECTION_PATH),
            tracker_config_sha256=sha256(ROOT / "configs/tracker.yaml"),
            ultralytics_version=version("ultralytics"), lap_version=version("lap"),
        )
    return detection, track


def build_matrix_graph(cell: str, root: Path, source_factory: CachedSourceFactory,
                       detection_fixture: dict | None, track_fixture: dict | None) -> MonitoringService:
    """Only inference/tracker vary; all downstream objects are formal and shared in type."""
    if cell not in CELLS:
        raise ValueError("unknown matrix cell")
    if cell in {"PP", "PR"} and detection_fixture is None:
        raise ValueError("precomputed detection fixture required")
    if cell in {"PP", "RP"} and track_fixture is None:
        raise ValueError("precomputed track fixture required")
    database = Database(root / "database/events.sqlite3")
    events = EventRepository(database)
    snapshots = SnapshotRepository(database)
    storage = SnapshotStorage(root / "snapshots")
    inference = (PrecomputedInferenceService(detection_fixture) if cell in {"PP", "PR"}
                 else InferenceService(config_path="configs/inference.yaml", execution_enabled=True))
    tracker = (PrecomputedTrackingAdapter(track_fixture) if cell in {"PP", "RP"}
               else ByteTrackPersonTrackingAdapter())
    return MonitoringService(
        inference_service=inference,
        tracker=tracker,
        association_adapter=PPEPersonAssociationAdapter(),
        compliance_service=ComplianceService(),
        event_service=EventService(engine=EventEngine(),
                                   store=JSONEventStore(root / "logs/events.jsonl")),
        ingest_service=EventIngestService(events),
        snapshot_service=SnapshotService(events, snapshots, storage),
        alert_service=AlertService((ConsoleAlertAdapter(sink=lambda _line: None),
                                    WebAlertAdapter())),
        event_loader=events.get,
        source_factory=source_factory,
    )


def run(cell: str, *, seconds: float = 1200.0, smoke: bool = False,
        period: float = 8.0) -> dict:
    if cell not in CELLS or seconds <= 0 or period <= 0:
        raise ValueError("invalid matrix run")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3g" / f"{cell.lower()}-{run_id}"
    for name in ("database", "snapshots", "logs", "resources", "outputs"):
        (root / name).mkdir(parents=True, exist_ok=False)
    metadata, frames = load_cached_frames(VIDEO)
    factory = CachedSourceFactory(metadata, frames)
    detection, track = load_verified_fixtures(cell)
    service = build_matrix_graph(cell, root, factory, detection, track)
    request = MonitoringSourceRequest(source_type=SourceType.MP4, location=str(VIDEO))
    sampler, sampler_output, stop_file = start_sampler(root)
    print(json.dumps({"cell": cell, "run_root": root.relative_to(ROOT).as_posix(),
                      "business_pid": os.getpid(), "sampler_pid": sampler.pid}), flush=True)
    started = monotonic()
    counters = {"completed_cycles": 0, "frames": 0, "detections": 0,
                "tracks": 0, "associations": 0, "unknown_associations": 0,
                "events": 0, "alerts_delivered": 0, "alerts_failed": 0}
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
                counters["frames"] += status.frames_processed
                counters["detections"] += status.detections
                counters["tracks"] += status.tracks
                counters["associations"] += status.associations
                counters["unknown_associations"] += status.unknown_associations
                counters["events"] += status.events_generated
                counters["alerts_delivered"] += status.alerts_delivered
                counters["alerts_failed"] += status.alerts_failed
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
    elapsed = monotonic() - started
    summary = {
        "cell": cell, "mode": "smoke" if smoke else "formal",
        "run_root": root.relative_to(ROOT).as_posix(),
        "requested_seconds": seconds, "elapsed_seconds": elapsed,
        "period_seconds": period, **counters,
        "source_created": factory.created,
        "final_status": service.status().to_dict(),
        "worker_exited": service.wait(timeout=0),
        "failure": failure,
        "sampler_exit_code": sampler.returncode,
        "sampler_samples": max(0, sum(1 for _ in sampler_output.open(encoding="utf-8")) - 1),
        "db_bytes_end": (root / "database/events.sqlite3").stat().st_size,
        "snapshot_bytes_end": sum(p.stat().st_size for p in (root / "snapshots").rglob("*") if p.is_file()),
        "frozen_sha256": {"video": sha256(VIDEO), "detection": sha256(DETECTION_PATH),
                          "track": sha256(TRACK_PATH)},
    }
    (root / "outputs/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"final_status", "frozen_sha256"}}), flush=True)
    if failure or sampler.returncode != 0 or not summary["worker_exited"]:
        raise RuntimeError(f"matrix run failed: {failure}, sampler={sampler.returncode}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", choices=CELLS, required=True)
    parser.add_argument("--seconds", type=float, default=1200.0)
    parser.add_argument("--period", type=float, default=8.0)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    run(args.cell, seconds=args.seconds, period=args.period, smoke=args.smoke)


if __name__ == "__main__":
    main()
