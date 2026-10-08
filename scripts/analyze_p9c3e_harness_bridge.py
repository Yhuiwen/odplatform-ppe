"""Semantic gate and window analysis for P9-C.3e; reads artifacts only."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_p9c3_attribution import slope, slope_per_cycle, slope_per_event


def semantic_evidence(root: Path, *, harness: str) -> dict:
    summary_path = root / ("outputs/full_chain.json" if harness == "H" else "attribution/summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    status = summary["status"] if harness == "H" else summary["final_status"]
    connection = sqlite3.connect(root / "database/events.sqlite3")
    try:
        events = connection.execute(
            "SELECT track_id,event_type,confidence,source_timestamp,frame_id,bbox_json "
            "FROM events ORDER BY source_timestamp,frame_id"
        ).fetchall()
        snapshots = connection.execute(
            "SELECT sha256,width,height FROM snapshots ORDER BY captured_at"
        ).fetchall()
    finally:
        connection.close()
    return {
        "frames": summary["total_frames"] if harness == "H" else summary["frames"],
        "detections": status["detections"], "tracks": status["tracks"],
        "associations": status["associations"],
        "unknown_associations": status["unknown_associations"],
        "compliance_findings": summary["compliance_findings"],
        "candidate_findings": summary["candidate_findings"],
        "events": [(track, kind, confidence, timestamp, frame_id,
                    json.loads(bbox) if bbox else None)
                   for track, kind, confidence, timestamp, frame_id, bbox in events],
        "snapshots": snapshots,
        "alerts_delivered": summary["alert_success"] if harness == "H" else status["alerts_delivered"],
        "alerts_failed": summary["alert_failure"] if harness == "H" else status["alerts_failed"],
    }


def compare_semantics(s4_root: Path, h_root: Path) -> dict:
    s4 = semantic_evidence(s4_root, harness="S4")
    h = semantic_evidence(h_root, harness="H")
    differences = {key: {"S4": s4[key], "H": h[key]} for key in s4 if s4[key] != h[key]}
    return {"pass": not differences, "differences": differences,
            "S4": s4, "H": h}


def analyze_probe(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) < 2:
        raise ValueError("probe has too few samples")
    windows = {}
    for low, high in ((2, 5), (5, 10), (10, 20)):
        selected = [row for row in rows if low * 60 <= row["elapsed_s"] < high * 60]
        windows[f"{low}-{high}"] = {
            "samples": len(selected),
            "rss_mib_mean": mean(row["rss"] / 2**20 for row in selected) if selected else None,
            "traced_mib_mean": mean(row["traced_current"] / 2**20 for row in selected) if selected else None,
            "cycles": [selected[0]["cycle"], selected[-1]["cycle"]] if selected else None,
            "events": [selected[0]["events"], selected[-1]["events"]] if selected else None,
        }
    warm = [row for row in rows if row["elapsed_s"] >= 120]
    ranges = {key: [min(row[key] for row in warm), max(row[key] for row in warm)]
              for key in ("threads", "handles", "open_files", "alert_console_completed",
                          "alert_web_completed", "web_history", "monitor_recent_events")
              if warm and all(isinstance(row.get(key), (int, float)) for row in warm)}
    return {
        "samples": len(rows), "elapsed_s": rows[-1]["elapsed_s"],
        "cycles": rows[-1]["cycle"], "frames": rows[-1]["frames"],
        "events": rows[-1]["events"], "sqlite_rows": rows[-1].get("sqlite_rows"),
        "snapshots": rows[-1].get("snapshots"), "alerts": rows[-1].get("alert_deliveries"),
        "rss_mib_per_min_2on": slope(rows, "rss"),
        "rss_mib_per_cycle_2on": slope_per_cycle(rows, "rss"),
        "rss_mib_per_event_2on": slope_per_event(rows, "rss"),
        "rss_mib_per_min_5on": slope(rows, "rss", start=300),
        "rss_mib_per_min_10on": slope(rows, "rss", start=600),
        "traced_mib_per_min_2on": slope(rows, "traced_current"),
        "windows": windows, "warm_ranges": ranges,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic-s4", type=Path)
    parser.add_argument("--semantic-h", type=Path)
    parser.add_argument("--probe", type=Path)
    args = parser.parse_args()
    if args.semantic_s4 or args.semantic_h:
        if not (args.semantic_s4 and args.semantic_h):
            parser.error("both semantic roots are required")
        result = compare_semantics(args.semantic_s4, args.semantic_h)
        print(json.dumps(result, indent=2))
        if not result["pass"]:
            raise SystemExit(1)
    if args.probe:
        result = analyze_probe(args.probe)
        (args.probe.parent / "bridge-analysis.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
