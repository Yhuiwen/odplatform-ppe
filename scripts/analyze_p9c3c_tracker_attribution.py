"""Summarize P/Q/R tracker-only five-second samples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_p9c3_attribution import slope, slope_per_cycle, slope_per_frame


def summarize(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) < 2:
        raise ValueError("tracker probe has too few rows")
    windows = []
    for low, high in ((0, 10), (2, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60)):
        selected = [row for row in rows if low * 60 <= row["elapsed_s"] < high * 60]
        if selected:
            def metric(key):
                values = [row[key] / 1024**2 for row in selected]
                return {"mean": mean(values), "median": median(values),
                        "min": min(values), "max": max(values)}
            windows.append({"minutes": f"{low}-{high}", "n": len(selected),
                            "rss_mib": metric("rss"), "traced_mib": metric("traced_current"),
                            "cycles_first_last": [selected[0]["cycle"], selected[-1]["cycle"]]})
    output = {
        "samples": len(rows), "elapsed_s": rows[-1]["elapsed_s"],
        "cycles": rows[-1]["cycle"], "updates": rows[-1]["frames"],
        "track_outputs": rows[-1]["track_outputs"],
        "tracker_instances": rows[-1]["tracker_instances"],
        "rss_mib_per_min_2to20": slope(rows, "rss"),
        "rss_mib_per_cycle_2to20": slope_per_cycle(rows, "rss"),
        "rss_mib_per_update_2to20": slope_per_frame(rows, "rss"),
        "traced_mib_per_min_2to20": slope(rows, "traced_current"),
        "traced_mib_per_cycle_2to20": slope_per_cycle(rows, "traced_current"),
        "rss_mib_per_min_10to20": slope(rows, "rss", start=600),
        "rss_mib_per_min_20to60": slope(rows, "rss", start=1200),
        "rss_mib_per_min_30to60": slope(rows, "rss", start=1800),
        "windows": windows, "first": rows[0], "last": rows[-1],
        "warm_ranges": {
            key: [min(row[key] for row in rows if row["elapsed_s"] >= 120),
                  max(row[key] for row in rows if row["elapsed_s"] >= 120)]
            for key in ("threads", "handles", "open_files", "tracked", "lost", "removed", "gc_objects")
        },
    }
    (path.parent / "analysis.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("probe", type=Path)
    args = parser.parse_args()
    result = summarize(args.probe)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"windows", "first", "last"}}, indent=2))


if __name__ == "__main__":
    main()
