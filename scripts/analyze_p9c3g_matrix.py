"""Offline resource windows and directional factorial contrasts for P9-C.3g."""

from __future__ import annotations

import argparse
import json
import sys
from bisect import bisect_right
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_p9c3f_lean_resources import read_samples


def regression(points: list[tuple[float, float]]) -> float | None:
    if len(points) < 2:
        return None
    xbar = mean(x for x, _ in points)
    ybar = mean(y for _, y in points)
    denominator = sum((x - xbar) ** 2 for x, _ in points)
    return sum((x - xbar) * (y - ybar) for x, y in points) / denominator if denominator else None


def window(samples: list[dict], start_min: float, end_min: float) -> dict:
    rows = [row for row in samples if start_min * 60 <= row["elapsed_s"] < end_min * 60]
    def stats(field: str) -> dict | None:
        values = [row[field] for row in rows if row[field] is not None]
        return ({"mean": mean(values), "median": median(values),
                 "min": min(values), "max": max(values)} if values else None)
    return {"minutes": f"{start_min:g}-{end_min:g}", "samples": len(rows),
            **{field: stats(field) for field in ("rss_mib", "vms_mib", "private_mib",
                                                   "cpu_percent", "threads", "handles", "open_files")}}


def shape_candidate(windows: list[dict], late_slope: float | None) -> str:
    """Describe direction only; magnitude/dispersion require report review."""
    means = [item["rss_mib"]["mean"] for item in windows if item["rss_mib"]]
    if len(means) != 3 or late_slope is None:
        return "INCONCLUSIVE"
    if means[0] < means[1] < means[2] and late_slope > 0:
        return "MONOTONIC_RISE"
    if means[0] < means[1] and means[2] <= means[1] and late_slope <= 0:
        return "HIGH_WATER_CANDIDATE"
    if late_slope <= 0 and means[0] >= means[2]:
        return "NON_RISING"
    return "INCONCLUSIVE"


def analyze_run(root: Path) -> dict:
    summary = json.loads((root / "outputs/summary.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "outputs/validation.json").read_text(encoding="utf-8"))
    samples = read_samples(root / "resources/external.csv")
    with (root / "outputs/cycles.jsonl").open(encoding="utf-8") as handle:
        cycle_ends = [json.loads(line)["end_elapsed_s"] for line in handle]
    windows = [window(samples, a, b) for a, b in ((2, 5), (5, 10), (10, 20))]
    warm = [row for row in samples if 120 <= row["elapsed_s"] < 1200]
    late = [row for row in samples if 600 <= row["elapsed_s"] < 1200]
    per_minute = regression([(row["elapsed_s"] / 60, row["rss_mib"]) for row in warm])
    per_cycle = regression([(bisect_right(cycle_ends, row["elapsed_s"]), row["rss_mib"])
                            for row in warm])
    late_per_minute = regression([(row["elapsed_s"] / 60, row["rss_mib"]) for row in late])
    result = {
        "cell": summary["cell"], "run_root": str(root),
        "elapsed_seconds": summary["elapsed_seconds"],
        "cycles": validation["cycles"], "frames": validation["frames"],
        "events": validation["events"], "snapshot_files_verified": validation["snapshot_files_verified"],
        "alerts_delivered": validation["alerts_delivered"], "alerts_failed": validation["alerts_failed"],
        "samples": len(samples), "windows": windows,
        "rss_slope_2_20_mib_per_min": per_minute,
        "rss_slope_2_20_mib_per_cycle": per_cycle,
        "rss_slope_2_20_mib_per_event": per_cycle * summary["completed_cycles"] / summary["events"] if per_cycle is not None and summary["events"] else None,
        "rss_slope_10_20_mib_per_min": late_per_minute,
        "shape_candidate": shape_candidate(windows, late_per_minute),
        "validation_pass": validation["pass"],
    }
    (root / "outputs/resource-analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def contrasts(results: dict[str, dict]) -> dict:
    if set(results) != {"PP", "PR", "RP", "RR"}:
        raise ValueError("complete PP/PR/RP/RR matrix required")
    values = {cell: item["rss_slope_2_20_mib_per_cycle"] for cell, item in results.items()}
    if any(value is None for value in values.values()):
        raise ValueError("all cycle-normalized slopes required")
    pp, pr, rp, rr = (values[cell] for cell in ("PP", "PR", "RP", "RR"))
    return {
        "inference_with_precomputed_tracker": rp - pp,
        "inference_with_real_tracker": rr - pr,
        "tracker_with_precomputed_detection": pr - pp,
        "tracker_with_real_inference": rr - rp,
        "factorial_interaction_direction": rr - pr - rp + pp,
        "unit": "MiB per completed cycle; directional contrasts, not additive byte attribution",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_roots", nargs="+", type=Path)
    args = parser.parse_args()
    results = {item["cell"]: item for item in (analyze_run(path.resolve()) for path in args.run_roots)}
    output = {"cells": results, "contrasts": contrasts(results) if len(results) == 4 else None}
    target = ROOT / "artifacts/p9c3g/matrix-analysis.json"
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"cells": {key: {k: v for k, v in item.items() if k in
                                       {"cycles", "events", "rss_slope_2_20_mib_per_min",
                                        "rss_slope_2_20_mib_per_cycle", "rss_slope_10_20_mib_per_min",
                                        "shape_candidate"}} for key, item in results.items()},
                      "contrasts": output["contrasts"]}))


if __name__ == "__main__":
    main()
