"""Offline analysis of the external five-second resource CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median

MIB = 1024 * 1024


def slope(samples: list[dict], start_min: float, end_min: float, field: str = "rss_mib") -> float | None:
    points = [(row["elapsed_s"] / 60, row[field]) for row in samples
              if start_min <= row["elapsed_s"] / 60 < end_min and row[field] is not None]
    if len(points) < 2:
        return None
    xbar = mean(point[0] for point in points)
    ybar = mean(point[1] for point in points)
    denominator = sum((x - xbar) ** 2 for x, _ in points)
    return sum((x - xbar) * (y - ybar) for x, y in points) / denominator if denominator else None


def read_samples(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    def optional(value: str) -> float | None:
        return float(value) if value else None
    return [{"elapsed_s": float(row["elapsed_s"]),
             "rss_mib": float(row["rss_bytes"]) / MIB,
             "vms_mib": float(row["vms_bytes"]) / MIB,
             "private_mib": optional(row["private_bytes"]) / MIB if row["private_bytes"] else None,
             "cpu_percent": float(row["cpu_percent"]),
             "threads": int(row["threads"]),
             "handles": int(row["handles"]) if row["handles"] else None,
             "open_files": int(row["open_files"]) if row["open_files"] else None}
            for row in rows]


def summarize(values: list[float | int | None]) -> dict | None:
    available = [value for value in values if value is not None]
    return ({"mean": mean(available), "median": median(available),
             "min": min(available), "max": max(available)} if available else None)


def classify_window_shape(means: list[float]) -> str:
    """Return a shape candidate; final decision also inspects slopes and raw range."""
    if len(means) != 5:
        return "INCONCLUSIVE"
    differences = [b - a for a, b in zip(means, means[1:])]
    if all(delta > 0 for delta in differences):
        return "SUSPICIOUS_CONTINUED_GROWTH"
    if differences[0] > 0 and differences[1] > 0 and differences[2] <= 0 and differences[3] <= 0:
        return "BOUNDED_HIGH_WATER"
    if differences[2] * differences[3] <= 0:
        return "STABLE_PLATEAU"
    return "INCONCLUSIVE"


def analyze(path: Path) -> dict:
    rows = read_samples(path)
    windows = []
    for start in range(0, 60, 10):
        subset = [row for row in rows if start * 60 <= row["elapsed_s"] < (start + 10) * 60]
        windows.append({"window_min": f"{start}-{start+10}", "samples": len(subset),
                        **{field: summarize([row[field] for row in subset])
                           for field in ("rss_mib", "vms_mib", "private_mib", "cpu_percent", "threads", "handles", "open_files")}})
    means = [item["rss_mib"]["mean"] for item in windows[1:] if item["rss_mib"]]
    return {"samples": len(rows), "first_elapsed_s": rows[0]["elapsed_s"] if rows else None,
            "last_elapsed_s": rows[-1]["elapsed_s"] if rows else None,
            "rss_windows": windows,
            "rss_slope_mib_per_min": {f"{start}-60": slope(rows, start, 60) for start in (10, 20, 30)},
            "late_mean_deltas_mib": [b - a for a, b in zip(means[-3:], means[-2:])],
            "shape_candidate": classify_window_shape(means),
            "note": "Shape candidate requires review of late slopes and raw dispersion; it is not an automatic PASS threshold."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    root = args.run_root.resolve()
    result = analyze(root / "resources/external.csv")
    (root / "outputs/resource-analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
