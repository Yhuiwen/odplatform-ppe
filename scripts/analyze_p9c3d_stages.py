"""Window and stage-sequence analysis for P9-C.3d diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_p9c3_attribution import slope, slope_per_cycle

STAGES = ("S0", "S1", "S2", "S3", "S4")


def first_divergence(stage_decisions: dict[str, bool]) -> str | None:
    """Return the first evidence-adjudicated material jump, in stage order."""
    unknown = set(stage_decisions) - set(STAGES)
    if unknown:
        raise ValueError(f"unknown stages: {sorted(unknown)}")
    return next((stage for stage in STAGES if stage_decisions.get(stage) is True), None)


def summarize(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) < 2:
        raise ValueError("stage probe has too few samples")
    windows = []
    for low, high in ((0, 2), (2, 5), (5, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60)):
        selected = [row for row in rows if low * 60 <= row["elapsed_s"] < high * 60]
        if selected:
            def metric(field):
                data = [row[field] / 1024**2 for row in selected]
                return {"mean": mean(data), "median": median(data),
                        "min": min(data), "max": max(data)}
            windows.append({"minutes": f"{low}-{high}", "n": len(selected),
                            "rss_mib": metric("rss"),
                            "traced_mib": metric("traced_current"),
                            "cycles": [selected[0]["cycle"], selected[-1]["cycle"]],
                            "events": [selected[0]["events"], selected[-1]["events"]]})
    warm = [row for row in rows if row["elapsed_s"] >= 120]
    output = {
        "samples": len(rows), "elapsed_s": rows[-1]["elapsed_s"],
        "cycles": rows[-1]["cycle"], "frames": rows[-1]["frames"],
        "events": rows[-1]["events"],
        "rss_mib_per_min_2on": slope(rows, "rss"),
        "rss_mib_per_cycle_2on": slope_per_cycle(rows, "rss"),
        "rss_mib_per_min_5on": slope(rows, "rss", start=300),
        "rss_mib_per_min_10on": slope(rows, "rss", start=600),
        "traced_mib_per_min_2on": slope(rows, "traced_current"),
        "windows": windows,
        "warm_ranges": {
            field: [min(row[field] for row in warm), max(row[field] for row in warm)]
            for field in ("threads", "handles", "open_files", "source_live", "recent_events",
                          "event_active", "event_recovery", "temporal_states")
        } if warm else {},
        "gc_type_ranges": {
            field: [min(row["gc_types"][field] for row in warm),
                    max(row["gc_types"][field] for row in warm)]
            for field in ("MonitoringStatus", "Thread", "CountingCachedSource", "ndarray")
        } if warm else {},
        "first": rows[0], "last": rows[-1],
    }
    (path.parent / "analysis.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("probe", type=Path)
    args = parser.parse_args()
    report = summarize(args.probe)
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {"windows", "first", "last"}}, indent=2))


if __name__ == "__main__":
    main()
