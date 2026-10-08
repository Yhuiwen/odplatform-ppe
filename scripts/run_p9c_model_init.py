"""Diagnostic split of trusted checkpoint deserialization and YOLO assembly."""

from __future__ import annotations

import gc
import json
from pathlib import Path
from time import perf_counter_ns

import torch
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    checkpoint = ROOT / "models/checkpoints/EXP-001/best.pt"
    started = perf_counter_ns()
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    deserialize_ms = (perf_counter_ns() - started) / 1_000_000
    del payload
    gc.collect()
    started = perf_counter_ns()
    model = YOLO(str(checkpoint))
    construct_ms = (perf_counter_ns() - started) / 1_000_000
    del model
    gc.collect()
    result = {
        "checkpoint": str(checkpoint),
        "device": "CPU",
        "checkpoint_deserialize_ms": deserialize_ms,
        "yolo_constructor_including_checkpoint_load_ms": construct_ms,
        "note": "Two diagnostic operations in one process with warm OS cache; overlapping checkpoint load work must not be added together. Official MonitoringService timings are reported separately.",
    }
    target = ROOT / "artifacts/p9c/model-initialization.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
