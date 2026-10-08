"""P9-C.3b M: cached variable MP4 frames through real inference only."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Thread
from time import perf_counter
from types import SimpleNamespace
from uuid import uuid4

import psutil

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from diagnostics.p9c3a_precomputed import detection_template, load_fixture, sha256
from scripts.run_p9b_full_chain import diagnostic_cycle_pause
from scripts.run_p9c3_memory_attribution import MemoryProbe, VIDEO, cached_mp4_frames
from services.inference_service import InferenceService


def assert_cycle_matches(results, fixture) -> None:
    if len(results) != fixture["total_frames"]:
        raise AssertionError("M frame count differs from real fixture")
    total = 0
    for ordinal, actual in enumerate(results):
        expected = fixture["frames"][ordinal]["detections"]
        if len(actual) != len(expected):
            raise AssertionError(f"M detection count differs on frame {ordinal}")
        total += len(actual)
        for detection, template in zip(actual, expected):
            observed = detection_template(detection)
            if observed["class_id"] != template["class_id"] or observed["class_name"] != template["class_name"]:
                raise AssertionError(f"M detection class differs on frame {ordinal}")
            if not math.isclose(observed["confidence"], template["confidence"], abs_tol=1e-6):
                raise AssertionError(f"M confidence differs on frame {ordinal}")
            if any(not math.isclose(observed["bbox"][key], template["bbox"][key], abs_tol=1e-5)
                   for key in ("x1", "y1", "x2", "y2")):
                raise AssertionError(f"M bbox differs on frame {ordinal}")
    if total != fixture["total_detections"]:
        raise AssertionError("M total detections differ from real fixture")


def run(seconds: float, period: float = 8.0) -> dict:
    metadata, frames = cached_mp4_frames()
    fixture_path = ROOT / "artifacts/p9c3/p9c3a-real-detections.json"
    fixture = load_fixture(
        fixture_path, expected_mp4_sha256=sha256(VIDEO),
        expected_checkpoint_sha256=sha256(ROOT / "models/checkpoints/EXP-001/best.pt"),
        expected_config_sha256=sha256(ROOT / "configs/inference.yaml"),
        expected_lock_sha256=sha256(ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"),
    )
    tracemalloc.start(1)
    service = InferenceService(config_path="configs/inference.yaml", execution_enabled=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3" / run_id
    root.mkdir(parents=True)
    recorder = SimpleNamespace(total_frames=0, total_events=0, total_ingested=0,
                               total_snapshots=0, alert_success=0,
                               total_detections=0, frame_id=None, cycle=0)
    probe = MemoryProbe(marks=())
    probe.attach(root=root, service=None, console=None, web=None, recorder=recorder)
    process = psutil.Process(os.getpid())
    stop = Event()
    start = perf_counter()

    def sample_loop():
        while not stop.is_set():
            probe.sample(elapsed=perf_counter() - start, cycle=recorder.cycle, process=process)
            stop.wait(5.0)

    sampler = Thread(target=sample_loop, daemon=True)
    sampler.start()
    checks = []
    final_results = None
    try:
        while perf_counter() - start < seconds:
            cycle_started = perf_counter()
            current_results = []
            for frame in frames:
                result = service.infer_frame(frame, source=metadata.source_id)
                recorder.frame_id = frame.frame_id
                recorder.total_frames += 1
                recorder.total_detections += len(result)
                current_results.append(result)
            recorder.cycle += 1
            if recorder.cycle in {1, 75}:
                assert_cycle_matches(current_results, fixture)
                checks.append(recorder.cycle)
            # Keep one bounded cycle of results for the last-cycle check.
            final_results = current_results
            remaining = seconds - (perf_counter() - start)
            if remaining > 0:
                stop.wait(diagnostic_cycle_pause(
                    cycle_elapsed=perf_counter() - cycle_started,
                    target_period=period, remaining_duration=remaining,
                ))
        if final_results is None:
            raise AssertionError("M did not retain its last cycle")
        assert_cycle_matches(final_results, fixture)
        if recorder.cycle not in checks:
            checks.append(recorder.cycle)
    finally:
        stop.set()
        sampler.join(timeout=5)
        probe.sample(elapsed=perf_counter() - start, cycle=recorder.cycle, process=process)
        probe.finish(elapsed=perf_counter() - start)
    output = {"mode": "M", "run_root": root.relative_to(ROOT).as_posix(),
              "elapsed_seconds": perf_counter() - start, "cycles": recorder.cycle,
              "frames": recorder.total_frames, "detections": recorder.total_detections,
              "verified_cycles": checks, "source_sha256": sha256(VIDEO),
              "fixture_sha256": sha256(fixture_path)}
    (root / "attribution/summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=1200)
    parser.add_argument("--period", type=float, default=8.0)
    args = parser.parse_args()
    print(json.dumps(run(args.seconds, args.period)))


if __name__ == "__main__":
    main()
