"""Summarize isolated P9-C.3 probe JSONL without altering run artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, median


def slope(rows: list[dict], field: str, *, start: float = 120.0) -> float | None:
    values = [(row["elapsed_s"] / 60, row[field] / 1024**2) for row in rows
              if row["elapsed_s"] >= start and isinstance(row.get(field), (int, float))]
    if len(values) < 2:
        return None
    xbar = mean(x for x, _ in values)
    ybar = mean(y for _, y in values)
    denominator = sum((x - xbar) ** 2 for x, _ in values)
    return sum((x - xbar) * (y - ybar) for x, y in values) / denominator if denominator else None


def slope_per_cycle(rows: list[dict], field: str, *, start: float = 120.0) -> float | None:
    values = [(row["cycle"], row[field] / 1024**2) for row in rows
              if row["elapsed_s"] >= start and isinstance(row.get(field), (int, float))]
    if len(values) < 2:
        return None
    xbar = mean(x for x, _ in values)
    ybar = mean(y for _, y in values)
    denominator = sum((x - xbar) ** 2 for x, _ in values)
    return sum((x - xbar) * (y - ybar) for x, y in values) / denominator if denominator else None


def slope_per_event(rows: list[dict], field: str, *, start: float = 120.0) -> float | None:
    values = [(row["events"], row[field] / 1024**2) for row in rows
              if row["elapsed_s"] >= start and isinstance(row.get("events"), int)
              and isinstance(row.get(field), (int, float))]
    if len(values) < 2:
        return None
    xbar = mean(x for x, _ in values)
    ybar = mean(y for _, y in values)
    denominator = sum((x - xbar) ** 2 for x, _ in values)
    return sum((x - xbar) * (y - ybar) for x, y in values) / denominator if denominator else None


def slope_per_frame(rows: list[dict], field: str, *, start: float = 120.0) -> float | None:
    values = [(row["frames"], row[field] / 1024**2) for row in rows
              if row["elapsed_s"] >= start and isinstance(row.get("frames"), int)
              and isinstance(row.get(field), (int, float))]
    if len(values) < 2:
        return None
    xbar = mean(x for x, _ in values)
    ybar = mean(y for _, y in values)
    denominator = sum((x - xbar) ** 2 for x, _ in values)
    return sum((x - xbar) * (y - ybar) for x, y in values) / denominator if denominator else None


def summarize(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError("probe has no rows")
    windows = []
    for low, high in ((0, 2), (2, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60)):
        selected = [row for row in rows if low * 60 <= row["elapsed_s"] < high * 60]
        if selected:
            def metric(key):
                values = [row[key] / 1024**2 for row in selected if isinstance(row.get(key), (int, float))]
                return {"mean": mean(values), "median": median(values),
                        "min": min(values), "max": max(values)} if values else None
            windows.append({"window_min": f"{low}-{high}", "n": len(selected),
                            "rss_mib": metric("rss"), "traced_mib": metric("traced_current"),
                            "private_mib": metric("private"),
                            "cycles_first_last": [selected[0]["cycle"], selected[-1]["cycle"]],
                            "events_first_last": [selected[0]["events"], selected[-1]["events"]]})
    output = {"samples": len(rows), "elapsed_s": rows[-1]["elapsed_s"],
              "cycles": rows[-1]["cycle"], "frames": rows[-1]["frames"],
              "events": rows[-1]["events"], "windows": windows,
              "warm_rss_slope_mib_per_min": slope(rows, "rss"),
              "warm_rss_slope_mib_per_cycle": slope_per_cycle(rows, "rss"),
              "warm_rss_slope_mib_per_event": slope_per_event(rows, "rss"),
              "warm_rss_slope_mib_per_frame": slope_per_frame(rows, "rss"),
              "late_rss_slope_mib_per_min": slope(rows, "rss", start=600.0),
              "rss_slope_20_to_60_mib_per_min": slope(rows, "rss", start=1200.0),
              "rss_slope_30_to_60_mib_per_min": slope(rows, "rss", start=1800.0),
              "warm_traced_slope_mib_per_min": slope(rows, "traced_current"),
              "late_traced_slope_mib_per_min": slope(rows, "traced_current", start=600.0),
              "warm_private_slope_mib_per_min": slope(rows, "private"),
              "first": rows[0], "last": rows[-1]}
    (path.parent / "analysis.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("probe", type=Path)
    args = parser.parse_args()
    result = summarize(args.probe)
    print(json.dumps({key: result[key] for key in ("samples", "elapsed_s", "cycles", "frames", "events", "warm_rss_slope_mib_per_min", "warm_rss_slope_mib_per_cycle", "late_rss_slope_mib_per_min", "warm_traced_slope_mib_per_min", "late_traced_slope_mib_per_min", "warm_private_slope_mib_per_min")}, indent=2))


if __name__ == "__main__":
    main()
