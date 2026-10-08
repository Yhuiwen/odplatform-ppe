"""Compare one-cycle K and L business outputs, excluding runtime identities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def semantic_signature(run_root: Path) -> dict:
    summary = json.loads((run_root / "outputs/full_chain.json").read_text(encoding="utf-8"))
    frames = [json.loads(line) for line in (run_root / "metrics/frames.jsonl").read_text(encoding="utf-8").splitlines() if line]
    events = [
        {key: event[key] for key in ("event_type", "track_id", "frame_id", "source_timestamp", "confidence")}
        for event in summary["events"]
    ]
    return {
        "frames": summary["total_frames"],
        "detection_total": sum(row["detections"] for row in frames),
        "detections_by_frame": [row["detections"] for row in frames],
        "tracking_by_frame": [row["tracks"] for row in frames],
        "association_by_frame": [row["associations"] for row in frames],
        "detection_classes": summary["detection_classes"],
        "track_ids_by_frame": summary["track_ids_by_frame"],
        "track_details_by_frame": summary["track_details_by_frame"],
        "association_outputs": summary["associations"],
        "association_candidates": summary["association_candidates"],
        "compliance_findings": summary["compliance_findings"],
        "candidate_findings": summary["candidate_findings"],
        "events": events,
        "sqlite_rows": summary["sqlite_count"],
        "snapshot_count": summary["total_snapshots"],
        "snapshot_sha256": [event["snapshot_sha256"] for event in summary["events"]],
        "alert_deliveries": summary["alert_success"],
    }


def compare(k_root: Path, l_root: Path) -> dict:
    k, l = semantic_signature(k_root), semantic_signature(l_root)
    differing = [key for key in k if k[key] != l[key]]
    return {"result": "PASS" if not differing else "FAIL", "different_fields": differing,
            "k": k, "l": l}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("k_root", type=Path)
    parser.add_argument("l_root", type=Path)
    args = parser.parse_args()
    result = compare(args.k_root, args.l_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
