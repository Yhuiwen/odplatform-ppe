"""Minimal external, append-only resource sampler for P9-C.3f."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep

import psutil

FIELDS = ("timestamp_utc", "elapsed_s", "rss_bytes", "vms_bytes",
          "private_bytes", "cpu_percent", "threads", "handles", "open_files")


def sample(process: psutil.Process, elapsed_s: float) -> dict:
    memory = process.memory_info()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": elapsed_s,
        "rss_bytes": memory.rss,
        "vms_bytes": memory.vms,
        "private_bytes": getattr(memory, "private", ""),
        "cpu_percent": process.cpu_percent(interval=None),
        "threads": process.num_threads(),
        "handles": process.num_handles() if hasattr(process, "num_handles") else "",
        "open_files": len(process.open_files()),
    }


def run(pid: int, output: Path, stop_file: Path, *, interval: float = 5.0) -> int:
    if interval <= 0:
        raise ValueError("interval must be positive")
    process = psutil.Process(pid)
    process.cpu_percent(interval=None)
    output.parent.mkdir(parents=True, exist_ok=True)
    start = monotonic()
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        handle.flush()
        while not stop_file.exists():
            try:
                row = sample(process, monotonic() - start)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            writer.writerow(row)
            handle.flush()
            deadline = monotonic() + interval
            while not stop_file.exists():
                remaining = deadline - monotonic()
                if remaining <= 0:
                    break
                # The stop marker is checked frequently without gathering
                # additional resource samples or retaining history.
                sleep(min(remaining, 0.2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    return run(args.pid, args.output, args.stop_file, interval=args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
