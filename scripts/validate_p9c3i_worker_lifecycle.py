"""Post-exit integrity gate for P9-C.3i controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(root: Path):
    summary = json.loads((root / "outputs/summary.json").read_text(encoding="utf-8"))
    cycles = [json.loads(line) for line in (root / "outputs/cycles.jsonl").read_text(
        encoding="utf-8").splitlines()]
    count = summary["cycles_completed"]
    cell = summary["cell"]
    expected_threads = {"T0": 0, "T1": 1, "T2": count, "T3": count, "T4": count + 1}[cell]
    failures = []
    if count < 1 or len(cycles) != count:
        failures.append("cycle count")
    if summary["frames"] != count * 47 or summary["detections"] != count * 77:
        failures.append("frame/detection count")
    if summary["threads_created"] != expected_threads or summary["threads_joined"] != expected_threads:
        failures.append("worker lifecycle")
    if cell in {"T3", "T4"} and summary["source_created"] != count:
        failures.append("source lifecycle")
    if any(not isinstance(summary["model_identity"].get(k), int)
           for k in ("service", "detector", "model")):
        failures.append("model identity")
    if not summary["worker_exited"] or summary["sampler_exit_code"] != 0 or summary["failure"]:
        failures.append("process exit")
    result = {"pass": not failures, "cell": cell, "cycles": count,
              "frames": summary["frames"], "detections": summary["detections"],
              "threads_created": summary["threads_created"],
              "threads_joined": summary["threads_joined"], "failures": failures}
    (root / "outputs/validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if failures:
        raise AssertionError(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    print(json.dumps(validate(parser.parse_args().root.resolve())))
