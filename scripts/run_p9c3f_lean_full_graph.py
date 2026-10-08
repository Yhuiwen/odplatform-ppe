"""Real MP4 full graph with only cycle summaries and an external sampler."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
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
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.json_event_store import JSONEventStore
from infra.storage.snapshot_storage import SnapshotStorage
from services.alert_service import AlertService
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService
from services.event_service import EventService
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringService, MonitoringSourceRequest, MonitoringState
from services.snapshot_service import SnapshotService

VIDEO = ROOT / "artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4"


def build_lean_graph(root: Path) -> MonitoringService:
    """Construct only formal business components and isolated evidence paths."""
    database = Database(root / "database/events.sqlite3")
    events = EventRepository(database)
    snapshots = SnapshotRepository(database)
    storage = SnapshotStorage(root / "snapshots")
    return MonitoringService(
        inference_service=InferenceService(config_path="configs/inference.yaml", execution_enabled=True),
        tracker=ByteTrackPersonTrackingAdapter(),
        association_adapter=PPEPersonAssociationAdapter(),
        compliance_service=ComplianceService(),
        event_service=EventService(engine=EventEngine(),
                                   store=JSONEventStore(root / "logs/events.jsonl")),
        ingest_service=EventIngestService(events),
        snapshot_service=SnapshotService(events, snapshots, storage),
        alert_service=AlertService((ConsoleAlertAdapter(sink=lambda _line: None),
                                    WebAlertAdapter())),
        event_loader=events.get,
    )


def cycle_summary(index: int, start_elapsed: float, end_elapsed: float, status) -> dict:
    """One small completed-cycle record; no frame or business object history."""
    return {
        "cycle_index": index, "start_elapsed_s": start_elapsed,
        "end_elapsed_s": end_elapsed,
        "frames_processed": status.frames_processed,
        "detections": status.detections, "tracks": status.tracks,
        "associations": status.associations,
        "events": status.events_generated,
        "alerts_delivered": status.alerts_delivered,
        "alerts_failed": status.alerts_failed,
        "final_state": status.state.value,
    }


def stream_cycle(handle, record: dict) -> None:
    handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    handle.flush()


def disk_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) if root.exists() else 0


def start_sampler(root: Path, *, interval: float = 5.0) -> tuple[subprocess.Popen, Path, Path]:
    output = root / "resources/external.csv"
    stop_file = root / "resources/stop.marker"
    stderr_path = root / "resources/sampler.stderr.log"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(ROOT / "scripts/sample_p9c3f_process.py"),
               "--pid", str(os.getpid()), "--output", str(output),
               "--stop-file", str(stop_file), "--interval", str(interval)]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with stderr_path.open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL,
                                   stderr=stderr, creationflags=flags)
    deadline = monotonic() + 15
    while monotonic() < deadline:
        if output.exists() and output.stat().st_size > 100:
            return process, output, stop_file
        if process.poll() is not None:
            raise RuntimeError("external sampler exited before its first sample")
        sleep(0.05)
    raise RuntimeError("external sampler did not write its first sample")


def run(*, seconds: float, max_cycles: int | None = None, interval: float = 5.0) -> dict:
    if seconds < 0 or (seconds == 0 and not max_cycles):
        raise ValueError("positive duration or max_cycles required")
    if max_cycles is not None and max_cycles <= 0:
        raise ValueError("max_cycles must be positive")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3" / f"p9c3f-{run_id}"
    for name in ("database", "snapshots", "logs", "resources", "outputs"):
        (root / name).mkdir(parents=True, exist_ok=False)
    service = build_lean_graph(root)
    request = MonitoringSourceRequest(source_type=SourceType.MP4, location=str(VIDEO))
    db_start_bytes = (root / "database/events.sqlite3").stat().st_size if (root / "database/events.sqlite3").exists() else 0
    snapshot_start_bytes = disk_bytes(root / "snapshots")
    sampler, sampler_output, stop_file = start_sampler(root, interval=interval)
    print(json.dumps({"run_root": root.relative_to(ROOT).as_posix(),
                      "business_pid": os.getpid(), "sampler_pid": sampler.pid,
                      "sampler": str(sampler_output.relative_to(ROOT))}), flush=True)
    started = monotonic()
    counters = {"completed_cycles": 0, "frames": 0, "detections": 0,
                "tracks": 0, "associations": 0, "events": 0,
                "alerts_delivered": 0, "alerts_failed": 0}
    final_action = "completed_current_cycle"
    failure = None
    try:
        with (root / "outputs/cycles.jsonl").open("w", encoding="utf-8") as cycles:
            while (counters["completed_cycles"] < max_cycles if max_cycles is not None else monotonic() - started < seconds or counters["completed_cycles"] == 0):
                cycle_started = monotonic() - started
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
                counters["events"] += status.events_generated
                counters["alerts_delivered"] += status.alerts_delivered
                counters["alerts_failed"] += status.alerts_failed
                stream_cycle(cycles, cycle_summary(
                    counters["completed_cycles"], cycle_started,
                    monotonic() - started, status))
    finally:
        if not service.wait(timeout=0):
            service.stop()
            final_action = "graceful_stop_after_exception"
        stop_file.write_text("stop\n", encoding="utf-8")
        sampler.wait(timeout=15)
    elapsed = monotonic() - started
    final_status = service.status()
    summary = {
        "run_root": root.relative_to(ROOT).as_posix(),
        "requested_seconds": seconds, "elapsed_seconds": elapsed,
        "max_cycles": max_cycles, **counters,
        "final_status": final_status.to_dict(),
        "worker_exited": service.wait(timeout=0),
        "final_action": final_action,
        "failure": failure,
        "sampler_exit_code": sampler.returncode,
        "sampler_samples": max(0, sum(1 for _ in sampler_output.open(encoding="utf-8")) - 1),
        "db_bytes_start": db_start_bytes,
        "db_bytes_end": (root / "database/events.sqlite3").stat().st_size,
        "snapshot_bytes_start": snapshot_start_bytes,
        "snapshot_bytes_end": disk_bytes(root / "snapshots"),
    }
    (root / "outputs/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in {"final_status"}}, ensure_ascii=False), flush=True)
    if failure or sampler.returncode != 0 or not summary["worker_exited"]:
        raise RuntimeError(f"lean full graph failed: {failure}, sampler={sampler.returncode}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=3600)
    parser.add_argument("--max-cycles", type=int)
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    run(seconds=args.seconds, max_cycles=args.max_cycles, interval=args.interval)


if __name__ == "__main__":
    main()
