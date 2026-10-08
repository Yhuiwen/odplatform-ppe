"""Materialize per-frame P9-C timing rows from captured service samples."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELD_NAMES = {
    "infer_frame": "inference_ms",
    "update": "tracking_ms",
    "associate": "association_ms",
    "evaluate": "compliance_ms",
    "process": "event_ms",
    "ingest": "database_ms",
    "capture": "snapshot_ms",
    "dispatch_event": "alert_ms",
    "frame_pipeline": "frame_pipeline_ms",
}


def main() -> int:
    for run_root in sorted((ROOT / "artifacts/p9c").iterdir()):
        source = run_root / "outputs/full_chain.json"
        if not source.is_file():
            continue
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not payload.get("stage_samples"):
            continue
        rows: dict[tuple[int, int], dict] = {}
        reads: dict[int, list[float]] = {}
        for sample in payload["stage_samples"]:
            cycle = sample.get("cycle", 1)
            if sample["stage"] == "source_read":
                reads.setdefault(cycle, []).append(sample["ms"])
            if sample["stage"] not in FIELD_NAMES or sample["frame_id"] is None:
                continue
            key = (cycle, sample["frame_id"])
            row = rows.setdefault(key, {
                "cycle": cycle,
                "frame_id": sample["frame_id"],
                **{name: None for name in ("source_read_ms", *FIELD_NAMES.values())},
            })
            field = FIELD_NAMES[sample["stage"]]
            row[field] = (row[field] or 0.0) + sample["ms"]
        for (cycle, frame_id), row in rows.items():
            if frame_id < len(reads.get(cycle, [])):
                row["source_read_ms"] = reads[cycle][frame_id]
        target = run_root / "performance/frame-timing.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for _, row in sorted(rows.items())), encoding="utf-8")
        print(run_root.name, len(rows), target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
