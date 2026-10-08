"""Offline P9-C.3h resource analysis and first-divergence decision support."""

from __future__ import annotations

import argparse
import json
import sys
from bisect import bisect_right
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_p9c3f_lean_resources import read_samples
from scripts.analyze_p9c3g_matrix import regression, window


def analyze(root: Path) -> dict:
    summary = json.loads((root / "outputs/summary.json").read_text(encoding="utf-8"))
    samples = read_samples(root / "resources/external.csv")
    with (root / "outputs/cycles.jsonl").open(encoding="utf-8") as handle:
        cycle_ends = [json.loads(line)["end_elapsed_s"] for line in handle]
    duration = 20 if summary["elapsed_seconds"] >= 1150 else 10
    warm = [r for r in samples if 120 <= r["elapsed_s"] < duration * 60]
    screen = [r for r in samples if 120 <= r["elapsed_s"] < 600]
    late = [r for r in samples if (duration - 5) * 60 <= r["elapsed_s"] < duration * 60]
    result = {
        "stage": summary["stage"], "root": root.as_posix(),
        "duration_minutes": duration, "cycles": summary["completed_cycles"],
        "frames": summary["frames"], "events": summary["events"],
        "event_lines": summary["event_lines"], "samples": len(samples),
        "windows": [window(samples, a, b) for a, b in
                    ([(2, 5), (5, 10)] if duration == 10 else [(2, 5), (5, 10), (10, 20)])],
        "rss_mib_per_min": regression([(r["elapsed_s"] / 60, r["rss_mib"]) for r in warm]),
        "rss_mib_per_cycle": regression([(bisect_right(cycle_ends, r["elapsed_s"]), r["rss_mib"])
                                         for r in warm]),
        "rss_2_10_mib_per_min": regression([(r["elapsed_s"] / 60, r["rss_mib"]) for r in screen]),
        "rss_2_10_mib_per_cycle": regression([(bisect_right(cycle_ends, r["elapsed_s"]), r["rss_mib"])
                                              for r in screen]),
        "rss_5_10_mib_per_min": regression([(r["elapsed_s"] / 60, r["rss_mib"])
                                            for r in samples if 300 <= r["elapsed_s"] < 600]),
        "rss_late_mib_per_min": regression([(r["elapsed_s"] / 60, r["rss_mib"]) for r in late]),
        "worker_exited": summary["worker_exited"],
        "sampler_exit_code": summary["sampler_exit_code"],
        "source_created": summary["source_created"],
    }
    (root / "outputs/resource-analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def adjacent_differences(slopes: dict[str, float]) -> dict[str, float]:
    """Expose differences without a universal materiality threshold."""
    order = ("H0", "H1", "H2", "RP")
    return {f"{before}_to_{after}": slopes[after] - slopes[before]
            for before, after in zip(order, order[1:])
            if before in slopes and after in slopes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args()
    results = [analyze(p.resolve()) for p in args.roots]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
