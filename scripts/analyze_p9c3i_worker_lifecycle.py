"""Offline resource windows for P9-C.3i worker/session controls."""

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
        ends = [json.loads(line)["end_elapsed_s"] for line in handle]
    warm = [r for r in samples if 120 <= r["elapsed_s"] < 1200]
    late = [r for r in samples if 600 <= r["elapsed_s"] < 1200]
    per_cycle = regression([(bisect_right(ends, r["elapsed_s"]), r["rss_mib"])
                            for r in warm])
    result = {
        "cell": summary["cell"], "root": root.as_posix(),
        "cycles": summary["cycles_completed"], "frames": summary["frames"],
        "detections": summary["detections"],
        "threads_created": summary["threads_created"],
        "threads_joined": summary["threads_joined"],
        "samples": len(samples),
        "windows": [window(samples, a, b) for a, b in ((2, 5), (5, 10), (10, 20))],
        "rss_2_20_mib_per_min": regression([(r["elapsed_s"] / 60, r["rss_mib"])
                                             for r in warm]),
        "rss_2_20_mib_per_cycle": per_cycle,
        "rss_2_20_mib_per_frame": per_cycle / 47 if per_cycle is not None else None,
        "rss_10_20_mib_per_min": regression([(r["elapsed_s"] / 60, r["rss_mib"])
                                              for r in late]),
    }
    (root / "outputs/resource-analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    print(json.dumps(analyze(parser.parse_args().root.resolve()), indent=2))
