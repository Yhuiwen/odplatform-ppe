"""Measure the official MonitoringService path without changing its decisions."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.schemas.video import SourceType
from scripts.run_p9b_full_chain import ROOT, run


def _stats(values: list[float]) -> dict | None:
    if not values:
        return None
    ordered = sorted(values)
    def percentile(p: float) -> float:
        rank = (len(ordered) - 1) * p
        lower = int(rank)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)
    return {"count": len(values), "mean": statistics.mean(values), "min": ordered[0], "max": ordered[-1], "p50": percentile(0.5), "p95": percentile(0.95), "p99": percentile(0.99)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("mp4", "usb"), required=True)
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--min-duration", type=float, default=0.0)
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--video", default="artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4")
    args = parser.parse_args()
    source_type = SourceType.MP4 if args.source == "mp4" else SourceType.USB_CAMERA
    location = str((ROOT / args.video).resolve()) if args.source == "mp4" else args.camera_index
    result = run(source_type=source_type, location=location, seconds=args.seconds, cycles=args.cycles, metrics=True, artifact_kind="p9c", min_duration=args.min_duration)
    by_stage: dict[str, list[float]] = {}
    for sample in result["stage_samples"]:
        by_stage.setdefault(sample["stage"], []).append(sample["ms"])
    frame_rows: dict[tuple[int, int], dict] = {}
    field_names = {"infer_frame": "inference_ms", "update": "tracking_ms", "associate": "association_ms", "evaluate": "compliance_ms", "process": "event_ms", "ingest": "database_ms", "capture": "snapshot_ms", "dispatch_event": "alert_ms", "frame_pipeline": "frame_pipeline_ms"}
    read_by_cycle: dict[int, list[float]] = {}
    for sample in result["stage_samples"]:
        cycle = sample.get("cycle", 1)
        if sample["stage"] == "source_read":
            read_by_cycle.setdefault(cycle, []).append(sample["ms"])
        if sample["stage"] not in field_names or sample["frame_id"] is None:
            continue
        key = (cycle, sample["frame_id"])
        row = frame_rows.setdefault(key, {"cycle": cycle, "frame_id": sample["frame_id"], **{name: None for name in ("source_read_ms", *field_names.values())}})
        field = field_names[sample["stage"]]
        row[field] = (row[field] or 0.0) + sample["ms"]
    for (cycle, frame_id), row in frame_rows.items():
        reads = read_by_cycle.get(cycle, [])
        if frame_id < len(reads):
            row["source_read_ms"] = reads[frame_id]
    resources = result["resource_samples"]
    profile = {
        "run_id": result["run_id"],
        "source": args.source,
        "elapsed_seconds": result["elapsed_seconds"],
        "cycles": result["cycles"],
        "stage_statistics_ms": {stage: _stats(values) for stage, values in by_stage.items()},
        "cold_first_inference_ms": by_stage.get("infer_frame", [None])[0],
        "steady_inference_ms": _stats(by_stage.get("infer_frame", [])[1:]),
        "cpu_percent": _stats([item["cpu_percent"] for item in resources]),
        "rss_mib": _stats([item["rss_bytes"] / 1048576 for item in resources]),
        "threads": _stats([item["threads"] for item in resources]),
        "handles": _stats([item["handles"] for item in resources if item["handles"] is not None]),
        "resource_sample_count": len(resources),
        "frames": result["status"]["frames_processed"],
        "total_frames": sum(item["status"]["frames_processed"] for item in result["cycles"]),
        "effective_fps": sum(item["status"]["frames_processed"] for item in result["cycles"]) / result["elapsed_seconds"],
        "events": result["sqlite_count"],
        "alerts": len(result["web_alerts"]),
        "status": result["status"],
    }
    target = ROOT / result["run_root"] / "performance" / "profile.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    (target.parent / "frame-timing.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for _, row in sorted(frame_rows.items())), encoding="utf-8")
    print(json.dumps({"profile": str(target), "state": profile["status"]["state"], "frames": profile["frames"], "elapsed": profile["elapsed_seconds"]}, ensure_ascii=False))
    return 0 if profile["status"]["state"] in {"completed", "stopped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
