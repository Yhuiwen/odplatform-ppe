"""Verify the completed lean run after its business process has exited."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schemas.events import EventQuery
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from services.event_query_service import EventQueryService


def validate(root: Path) -> dict:
    summary = json.loads((root / "outputs/summary.json").read_text(encoding="utf-8"))
    cycle_count = frame_count = event_count = deliveries = failures = 0
    with (root / "outputs/cycles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            cycle = json.loads(line)
            cycle_count += 1
            assert cycle["cycle_index"] == cycle_count
            assert cycle["final_state"] == "completed" and cycle["frames_processed"] == 47
            assert cycle["end_elapsed_s"] >= cycle["start_elapsed_s"]
            frame_count += cycle["frames_processed"]
            event_count += cycle["events"]
            deliveries += cycle["alerts_delivered"]
            failures += cycle["alerts_failed"]
    database = Database(root / "database/events.sqlite3")
    events = EventRepository(database)
    query = EventQueryService(events, SnapshotRepository(database), SnapshotStorage(root / "snapshots"))
    ids: set[str] = set()
    referenced = verified = 0
    first = middle = last = None
    total = events.query(EventQuery(limit=1)).total_count
    for offset in range(0, total, 500):
        page = events.query(EventQuery(limit=500, offset=offset))
        for event in page.items:
            assert event.id not in ids, f"duplicate event ID: {event.id}"
            ids.add(event.id)
            if first is None:
                first = event.id
            if len(ids) == max(1, total // 2):
                middle = event.id
            last = event.id
            assert event.snapshot is not None, f"missing snapshot: {event.id}"
            referenced += 1
            evidence = query.evidence(event.id)
            assert evidence is not None and evidence.verified, f"invalid evidence: {event.id}"
            verified += 1
    files = sum(1 for _ in (root / "snapshots").rglob("*.jpg"))
    with (root / "logs/events.jsonl").open(encoding="utf-8") as handle:
        jsonl_count = sum(1 for line in handle if line.strip())
    checks = {
        "duration_at_least_requested": summary["elapsed_seconds"] >= summary["requested_seconds"],
        "cycles_completed": cycle_count == summary["completed_cycles"] and cycle_count > 0,
        "all_47_frame_eof_cycles": frame_count == cycle_count * 47 == summary["frames"],
        "event_counts": event_count == len(ids) == total == jsonl_count == summary["events"],
        "snapshot_metadata_files_hash_dimensions": referenced == verified == files == total,
        "console_web_alerts": deliveries == summary["alerts_delivered"] == total * 2 and failures == summary["alerts_failed"] == 0,
        "worker_and_source_lifecycle": summary["worker_exited"] and summary["final_status"]["state"] == "completed" and summary["final_action"] == "completed_current_cycle",
        "sampler_exited": summary["sampler_exit_code"] == 0 and summary["sampler_samples"] >= 2,
        "no_business_failure": summary["failure"] is None,
    }
    result = {
        "run_root": str(root), "cycles": cycle_count, "frames": frame_count,
        "events": total, "snapshot_metadata": referenced,
        "verified_snapshots": verified, "snapshot_files": files,
        "alert_success": deliveries, "alert_failure": failures,
        "first_event_id": first, "middle_event_id": middle, "last_event_id": last,
        "checks": checks, "pass": all(checks.values()),
    }
    (root / "outputs/validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not result["pass"]:
        raise AssertionError(checks)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    result = validate(args.run_root.resolve())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
