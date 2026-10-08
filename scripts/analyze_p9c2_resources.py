"""Summarize five-second long-run samples without imposing pass thresholds."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def samples(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def describe(values: list[float]) -> dict | None:
    if not values:
        return None
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "first": values[0],
        "last": values[-1],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    root = args.run_root.resolve()
    rows = list(samples(root / "metrics/resources.jsonl"))
    assert rows, "resource stream is empty"
    windows = []
    for start in range(0, 3600, 600):
        subset = [row for row in rows if start <= row["elapsed_seconds"] < start + 600]
        windows.append({
            "minutes": f"{start // 60}-{(start + 600) // 60}",
            "rss_mib": describe([row["rss_bytes"] / 1048576 for row in subset]),
            "cpu_percent": describe([row["cpu_percent"] for row in subset]),
            "threads": describe([row["threads"] for row in subset]),
            "handles": describe([row["handles"] for row in subset if row["handles"] is not None]),
            "open_files": describe([row["open_files"] for row in subset if row.get("open_files") is not None]),
            "frames_first_last": [subset[0]["frames"], subset[-1]["frames"]] if subset else None,
            "events_first_last": [subset[0]["events"], subset[-1]["events"]] if subset else None,
        })
    warm = [row for row in rows if 600 <= row["elapsed_seconds"] < 3600]
    slope = statistics.linear_regression(
        [row["elapsed_seconds"] / 60 for row in warm],
        [row["rss_bytes"] / 1048576 for row in warm],
    ).slope if len(warm) > 1 else None
    disk = []
    for boundary in range(0, 3601, 300):
        near = min(rows, key=lambda row: abs(row["elapsed_seconds"] - boundary))
        disk.append({
            "target_minute": boundary // 60,
            "sample_elapsed_s": near["elapsed_seconds"],
            "events": near["events"],
            "snapshots": near.get("snapshots"),
            "database_bytes": near["database_bytes"],
            "snapshot_bytes": near["snapshot_bytes"],
        })
    timeline = list(samples(root / "metrics/timeline.jsonl"))
    stops = []
    for requested in (item for item in timeline if item["name"] == "stop_requested"):
        later = (item for item in timeline if item["at_ns"] >= requested["at_ns"])
        returned = next((item for item in later if item["name"] == "stop_returned"), None)
        later = (item for item in timeline if item["at_ns"] >= requested["at_ns"])
        worker_exit = next((item for item in later if item["name"] == "worker_exit"), None)
        later = (item for item in timeline if item["at_ns"] >= requested["at_ns"])
        close = next((item for item in later if item["name"] == "source_close_end"), None)
        stops.append({
            "cycle": requested.get("cycle"),
            "requested_stage": requested.get("current_operation"),
            "frames_at_request": requested.get("frames"),
            "stop_return_ms": (returned["at_ns"] - requested["at_ns"]) / 1e6 if returned else None,
            "worker_exit_ms": (worker_exit["at_ns"] - requested["at_ns"]) / 1e6 if worker_exit else None,
            "source_close_ms": (close["at_ns"] - requested["at_ns"]) / 1e6 if close else None,
            "error_code": returned.get("error_code") if returned else None,
        })
    result = {
        "run_root": str(root),
        "sample_count": len(rows),
        "sample_interval_target_seconds": 5,
        "rss_slope_10_to_60_mib_per_minute": slope,
        "rss_peak_mib": max(row["rss_bytes"] for row in rows) / 1048576,
        "rss_final_mib": rows[-1]["rss_bytes"] / 1048576,
        "windows": windows,
        "disk_every_5_minutes": disk,
        "stops": stops,
    }
    target = root / "outputs/resource-analysis.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run_root": str(root), "slope": slope, "rss_peak_mib": result["rss_peak_mib"], "rss_final_mib": result["rss_final_mib"], "stops": stops}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
