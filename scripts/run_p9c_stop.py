"""Quantify existing USB stop boundaries without changing stop behavior."""

from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schemas.video import SourceType
from scripts.run_p9b_full_chain import run


def marker(timeline: list[dict], name: str) -> dict | None:
    return next((item for item in timeline if item["name"] == name), None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=("A_warm_steady", "B_after_read", "C_warm_inference", "D_cold_inference"))
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()
    scenarios = (
        ("A_warm_steady", "warm_steady", 20),
        ("B_after_read", "after_read", 20),
        ("C_warm_inference", "warm_infer", 20),
        ("D_cold_inference", "cold_infer", 0),
    )
    results = []
    for name, trigger, min_frames in scenarios:
        if args.scenario and name != args.scenario:
            continue
        for repetition in range(1, args.repeat + 1):
            result = run(
                source_type=SourceType.USB_CAMERA,
                location=0,
                seconds=40,
                diagnose_stop=True,
                artifact_kind="p9c",
                stop_trigger=trigger,
                stop_after_frames=min_frames,
            )
            timeline = result["stop_timeline"]
            requested = marker(timeline, "stop_requested")
            returned = marker(timeline, "stop_returned")
            worker_exit = marker(timeline, "worker_exit")
            close_end = marker(timeline, "source_close_end")
            row = {
                "scenario": name,
                "repetition": repetition,
                "run_id": result["run_id"],
                "state": result["status"]["state"],
                "error_code": result["status"]["error_code"],
                "frames_processed": result["status"]["frames_processed"],
                "requested_stage": requested.get("current_operation") if requested else None,
                "stop_return_ms": (returned["at_ns"] - requested["at_ns"]) / 1_000_000 if requested and returned else None,
                "worker_exit_ms": (worker_exit["at_ns"] - requested["at_ns"]) / 1_000_000 if requested and worker_exit else None,
                "camera_close_ms": (close_end["at_ns"] - requested["at_ns"]) / 1_000_000 if requested and close_end else None,
                "worker_exited": result["cycles"][-1]["worker_exited"],
            }
            results.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    suffix = f"-{args.scenario}" if args.scenario else ""
    target = ROOT / f"artifacts/p9c/stop-boundary{suffix}.json"
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
