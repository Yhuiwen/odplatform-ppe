"""Post-process one matrix run and emit comparable business semantics."""

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
    cycles = frames = detections = tracks = associations = unknown = generated = delivered = failed = 0
    with (root / "outputs/cycles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            cycles += 1
            assert row["cycle_index"] == cycles
            assert row["final_state"] == "completed" and row["frames_processed"] == 47
            frames += row["frames_processed"]
            detections += row["detections"]
            tracks += row["tracks"]
            associations += row["associations"]
            generated += row["events"]
            delivered += row["alerts_delivered"]
            failed += row["alerts_failed"]
    database = Database(root / "database/events.sqlite3")
    events = EventRepository(database)
    snapshots = SnapshotRepository(database)
    query = EventQueryService(events, snapshots, SnapshotStorage(root / "snapshots"))
    total = events.query(EventQuery(limit=1)).total_count
    ids: set[str] = set()
    semantic_rows: list[dict] = []
    for offset in range(0, total, 500):
        for event in events.query(EventQuery(limit=500, offset=offset)).items:
            assert event.id not in ids
            ids.add(event.id)
            record = events.get_record(event.id)
            evidence = query.evidence(event.id)
            assert record is not None and evidence is not None and evidence.verified
            assert evidence.snapshot is not None
            if summary["mode"] == "smoke":
                semantic_rows.append({
                    "type": event.type.value,
                    "track_id": event.track_id,
                    "frame_id": record.frame_id,
                    "source_timestamp": record.source_timestamp,
                    "confidence": event.confidence,
                    "bbox": record.bbox,
                    "snapshot_sha256": evidence.snapshot.sha256,
                })
    files = sum(1 for _ in (root / "snapshots").rglob("*.jpg"))
    with (root / "logs/events.jsonl").open(encoding="utf-8") as handle:
        json_events = sum(1 for line in handle if line.strip())
    checks = {
        "cycle_count": cycles == summary["completed_cycles"] == summary["source_created"] and cycles > 0,
        "frame_count": frames == cycles * 47 == summary["frames"],
        "detection_track_association": detections == summary["detections"] and tracks == summary["tracks"] and associations == summary["associations"],
        "events_sqlite_jsonl": generated == summary["events"] == total == len(ids) == json_events,
        "snapshot_integrity": files == total,
        "alerts": delivered == summary["alerts_delivered"] == total * 2 and failed == summary["alerts_failed"] == 0,
        "lifecycle": summary["worker_exited"] and summary["final_status"]["state"] == "completed" and summary["sampler_exit_code"] == 0 and summary["failure"] is None,
        "duration": summary["mode"] == "smoke" or summary["elapsed_seconds"] >= summary["requested_seconds"],
    }
    result = {
        "cell": summary["cell"], "mode": summary["mode"], "run_root": str(root),
        "cycles": cycles, "frames": frames, "detections": detections,
        "tracks": tracks, "associations": associations,
        "unknown_associations": summary["unknown_associations"],
        "events": total, "snapshot_files_verified": files,
        "alerts_delivered": delivered, "alerts_failed": failed,
        "semantic_events": semantic_rows,
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
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}))


if __name__ == "__main__":
    main()
