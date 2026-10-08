"""Post-exit integrity checks for staged P9-C.3h controls."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def validate(root: Path) -> dict:
    summary = json.loads((root / "outputs/summary.json").read_text(encoding="utf-8"))
    stage, cycles = summary["stage"], summary["completed_cycles"]
    rows = [json.loads(line) for line in (root / "outputs/cycles.jsonl").read_text(
        encoding="utf-8").splitlines()]
    errors = []
    if cycles < 1 or len(rows) != cycles or summary["source_created"] != cycles:
        errors.append("cycle/source mismatch")
    if summary["frames"] != cycles * 47 or summary["detections"] != cycles * 77:
        errors.append("frame/detection mismatch")
    if summary["tracks"] != cycles * 66:
        errors.append("track mismatch")
    if not summary["worker_exited"] or summary["sampler_exit_code"] != 0:
        errors.append("worker/sampler exit failure")
    if stage == "H0":
        expected_assoc = expected_events = 0
    elif stage == "H1":
        expected_assoc, expected_events = cycles, 0
    else:
        expected_assoc = expected_events = cycles
    if summary["associations"] != expected_assoc or summary["unknown_associations"] != expected_assoc:
        errors.append("association mismatch")
    if summary["events"] != expected_events or summary["event_lines"] != expected_events:
        errors.append("event mismatch")
    db_rows = 0
    db_path = root / "database/events.sqlite3"
    if db_path.exists():
        with sqlite3.connect(db_path) as connection:
            db_rows = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    if db_rows != (cycles if stage in {"H3", "H4", "H5", "RP"} else 0):
        errors.append("SQLite mismatch")
    snapshot_count = sum(p.is_file() for p in (root / "snapshots").rglob("*.jpg"))
    if snapshot_count != (cycles if stage in {"H4", "H5", "RP"} else 0):
        errors.append("snapshot mismatch")
    if summary["alerts_delivered"] != (cycles * 2 if stage in {"H5", "RP"} else 0):
        errors.append("alert mismatch")
    if summary["alerts_failed"]:
        errors.append("failed alerts")
    result = {"pass": not errors, "stage": stage, "cycles": cycles,
              "frames": summary["frames"], "events": summary["events"],
              "sqlite_rows": db_rows, "snapshot_files": snapshot_count,
              "alerts_delivered": summary["alerts_delivered"], "errors": errors}
    (root / "outputs/validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if errors:
        raise AssertionError(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    print(json.dumps(validate(parser.parse_args().root.resolve())))
