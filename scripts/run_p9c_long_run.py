"""Bounded-observer long run through the existing MonitoringService graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schemas.events import EventQuery
from core.schemas.video import SourceType
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from services.event_query_service import EventQueryService
from scripts.run_p9b_full_chain import run


def validate(root: Path, result: dict, source: str) -> dict:
    database = Database(root / "database/events.sqlite3")
    events = EventRepository(database)
    snapshots = SnapshotRepository(database)
    query = EventQueryService(events, snapshots, SnapshotStorage(root / "snapshots"))
    ids: set[str] = set()
    referenced = 0
    verified = 0
    page_index = 0
    first_id = None
    middle_id = None
    last_id = None
    count = result["sqlite_count"]
    while True:
        page = events.query(EventQuery(limit=500, offset=page_index * 500))
        if not page.items:
            break
        for event in page.items:
            if event.id in ids:
                raise AssertionError(f"duplicate event ID: {event.id}")
            ids.add(event.id)
            if len(ids) == 1:
                first_id = event.id
            if len(ids) == max(1, count // 2):
                middle_id = event.id
            last_id = event.id
            if event.snapshot is not None:
                referenced += 1
                evidence = query.evidence(event.id)
                if evidence is not None and evidence.verified:
                    verified += 1
                else:
                    raise AssertionError(f"unverified evidence: {event.id}")
        page_index += 1
    files = list((root / "snapshots").rglob("*.jpg"))
    cycle_log = root / "metrics/cycles.jsonl"
    cycles = [json.loads(line) for line in cycle_log.read_text(encoding="utf-8").splitlines()]
    timeline = [json.loads(line) for line in (root / "metrics/timeline.jsonl").read_text(encoding="utf-8").splitlines()]
    completed = sum(item["status"]["state"] == "completed" for item in cycles)
    frames_from_cycles = sum(item["status"]["frames_processed"] for item in cycles)
    opens = sum(item["name"] == "source_open_end" for item in timeline)
    closes = sum(item["name"] == "source_close_end" for item in timeline)
    exits = sum(item["name"] == "worker_exit" for item in timeline)
    stop_returns = [item for item in timeline if item["name"] == "stop_returned"]
    expected_alerts = count * 2  # This headless full-chain graph uses Console + Web.
    checks = {
        "sqlite_count_matches_events": count == len(ids) == result["total_events"],
        "snapshot_metadata_and_files": referenced == verified == len(files) == count == result["total_snapshots"],
        "console_web_alerts": result["alert_success"] == expected_alerts and result["alert_failure"] == 0,
        "frame_count_matches_cycles": frames_from_cycles == result["total_frames"],
        "source_open_close_worker_exit": opens == closes == exits == len(cycles),
        "all_workers_exited": all(item["worker_exited"] for item in cycles),
    }
    if source == "mp4":
        checks["all_47_frame_eof_cycles"] = all(item["status"]["state"] == "completed" and item["status"]["frames_processed"] == 47 for item in cycles)
    else:
        checks["usb_stop_and_restart"] = len(cycles) == 2 and all(item["status"]["state"] == "stopped" and item["status"]["frames_processed"] > 0 for item in cycles)
        checks["usb_stop_returns_without_timeout"] = len(stop_returns) == 2 and all(item.get("error_code") is None for item in stop_returns)
    output = {
        "source": source,
        "run_id": result["run_id"],
        "cycles": len(cycles),
        "completed_cycles": completed,
        "frames": frames_from_cycles,
        "events": count,
        "snapshot_metadata": referenced,
        "verified_snapshots": verified,
        "snapshot_files": len(files),
        "alert_success": result["alert_success"],
        "alert_failure": result["alert_failure"],
        "first_event_id": first_id,
        "middle_event_id": middle_id,
        "last_event_id": last_id,
        "checks": checks,
        "pass": all(checks.values()),
    }
    target = root / "outputs/validation.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("usb", "mp4"), required=True)
    parser.add_argument("--seconds", type=float, default=3600.0)
    parser.add_argument("--restart-seconds", type=float, default=40.0)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--video", default="artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4")
    args = parser.parse_args()
    source_type = SourceType.USB_CAMERA if args.source == "usb" else SourceType.MP4
    location = args.camera_index if args.source == "usb" else str((ROOT / args.video).resolve())
    result = run(
        source_type=source_type,
        location=location,
        seconds=args.seconds,
        cycles=2 if args.source == "usb" and args.restart_seconds else 1,
        min_duration=args.seconds if args.source == "mp4" else 0.0,
        restart_seconds=args.restart_seconds if args.source == "usb" else 0.0,
        diagnose_stop=args.source == "usb",
        metrics=True,
        bounded=True,
        artifact_kind="p9c2",
    )
    root = ROOT / result["run_root"]
    output = validate(root, result, args.source)
    print(json.dumps({"run_root": result["run_root"], "pass": output["pass"], "frames": output["frames"], "events": output["events"], "checks": output["checks"]}, ensure_ascii=False), flush=True)
    return 0 if output["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
