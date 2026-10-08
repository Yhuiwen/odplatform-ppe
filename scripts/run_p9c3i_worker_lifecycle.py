"""Lean T0/T1/T2/T3/T4 real-inference thread/session controls."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from diagnostics.p9c3a_precomputed import detection_template
from diagnostics.p9c3g_cached_source import CachedSourceFactory, load_cached_frames
from diagnostics.p9c3i_workers import PersistentCycleWorker, PersistentInferenceAdapter, run_in_fresh_worker
from core.schemas.video import SourceType
from scripts.run_p9c3f_lean_full_graph import start_sampler
from scripts.run_p9c3g_lean_matrix import VIDEO, load_verified_fixtures
from scripts.run_p9c3h_boundaries import build_graph
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringSourceRequest, MonitoringState

CELLS = ("T0", "T1", "T2", "T3", "T4")


def check_frame_semantics(frame_id, detections, fixture):
    expected = fixture["frames"][frame_id]["detections"]
    if len(detections) != len(expected):
        raise AssertionError(f"detection count mismatch at frame {frame_id}")
    for actual, template in zip(detections, expected):
        observed = detection_template(actual)
        if (observed["class_id"] != template["class_id"] or
                observed["class_name"] != template["class_name"] or
                not math.isclose(observed["confidence"], template["confidence"], abs_tol=1e-6) or
                any(not math.isclose(observed["bbox"][key], template["bbox"][key], abs_tol=1e-5)
                    for key in ("x1", "y1", "x2", "y2"))):
            raise AssertionError(f"detection semantic mismatch at frame {frame_id}")


def infer_cycle(service, frames, source, fixture=None):
    detections = 0
    for frame in frames:
        found = service.infer_frame(frame, source=source)
        if fixture is not None:
            check_frame_semantics(frame.frame_id, found, fixture)
        detections += len(found)
    return {"frames": len(frames), "detections": detections}


class SmokeSemanticAdapter:
    """Inline smoke assertion only; not installed during timed controls."""

    def __init__(self, service, fixture):
        self.service, self.fixture = service, fixture

    def infer_frame(self, frame, *, source):
        found = self.service.infer_frame(frame, source=source)
        check_frame_semantics(frame.frame_id, found, self.fixture)
        return found


def model_identity(service):
    model = service.detector._model
    if model is None:
        raise AssertionError("real inference did not load a model")
    return {"service": id(service), "detector": id(service.detector), "model": id(model)}


def run(cell: str, *, seconds: float = 1200, period: float = 8.0, smoke: bool = False):
    if cell not in CELLS or seconds <= 0 or period <= 0:
        raise ValueError("invalid worker lifecycle control")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3i" / f"{cell.lower()}-{run_id}"
    for name in ("resources", "outputs", "database", "snapshots", "logs"):
        (root / name).mkdir(parents=True, exist_ok=False)
    metadata, frames = load_cached_frames(VIDEO)
    fixture, track = load_verified_fixtures("PP")
    if cell in {"T3", "T4"}:
        factory = CachedSourceFactory(metadata, frames)
        monitoring, _ = build_graph("H0", root, factory, track)
        service = monitoring.inference_service
        adapter = None
        if cell == "T4":
            adapter = PersistentInferenceAdapter(
                service,
                (lambda frame_id, found: check_frame_semantics(frame_id, found, fixture))
                if smoke else None,
            )
            monitoring.inference_service = adapter
        elif smoke:
            monitoring.inference_service = SmokeSemanticAdapter(service, fixture)
        request = MonitoringSourceRequest(source_type=SourceType.MP4, location=str(VIDEO))
        worker = None
    else:
        service = InferenceService(config_path="configs/inference.yaml", execution_enabled=True)
        monitoring = factory = request = adapter = None
        worker = (PersistentCycleWorker(lambda f, s, x: infer_cycle(service, f, s, x))
                  if cell == "T1" else None)
    sampler, sampler_output, stop_file = start_sampler(root)
    print(json.dumps({"cell": cell, "run_root": root.relative_to(ROOT).as_posix(),
                      "business_pid": os.getpid(), "sampler_pid": sampler.pid}), flush=True)
    started = monotonic()
    counters = {"cycles_completed": 0, "frames": 0, "detections": 0,
                "threads_created": 1 if cell == "T1" else 0, "threads_joined": 0}
    identity = None
    failure = None
    try:
        with (root / "outputs/cycles.jsonl").open("w", encoding="utf-8") as handle:
            while counters["cycles_completed"] < (2 if smoke else 1) or (not smoke and monotonic() - started < seconds):
                cycle_start = monotonic() - started
                if cell == "T0":
                    result = infer_cycle(service, frames, metadata.source_id, fixture if smoke else None)
                elif cell == "T1":
                    result = worker.run_cycle(frames, metadata.source_id, fixture if smoke else None)
                elif cell == "T2":
                    counters["threads_created"] += 1
                    result = run_in_fresh_worker(
                        lambda f, s, x: infer_cycle(service, f, s, x),
                        frames, metadata.source_id, fixture if smoke else None)
                    counters["threads_joined"] += 1
                else:
                    counters["threads_created"] += 1
                    monitoring.start(request)
                    if not monitoring.wait(timeout=180):
                        monitoring.stop()
                        raise RuntimeError("T3 MonitoringService cycle timed out")
                    counters["threads_joined"] += 1
                    status = monitoring.status()
                    if status.state is not MonitoringState.COMPLETED:
                        raise RuntimeError(f"T3 monitoring failed: {status.error_message}")
                    result = {"frames": status.frames_processed, "detections": status.detections}
                    if status.tracks != 66:
                        raise AssertionError("T3 precomputed Track semantics differ")
                if result != {"frames": 47, "detections": 77}:
                    raise AssertionError(f"incomplete real inference cycle: {result}")
                current_identity = model_identity(service)
                if identity is None:
                    identity = current_identity
                elif identity != current_identity:
                    raise AssertionError("service/detector/model identity changed")
                counters["cycles_completed"] += 1
                counters["frames"] += result["frames"]
                counters["detections"] += result["detections"]
                handle.write(json.dumps({"cycle": counters["cycles_completed"],
                                         "start_elapsed_s": cycle_start,
                                         "end_elapsed_s": monotonic() - started}) + "\n")
                handle.flush()
                remaining = period - (monotonic() - started - cycle_start)
                if remaining > 0:
                    sleep(min(remaining, max(0, seconds - (monotonic() - started))
                              if not smoke else remaining))
    except BaseException as exc:
        failure = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if cell == "T1":
            worker.close()
            counters["threads_joined"] = worker.joined
        if cell in {"T3", "T4"} and not monitoring.wait(timeout=0):
            monitoring.stop()
        if cell == "T4":
            adapter.shutdown()
            counters["threads_created"] += adapter.created
            counters["threads_joined"] += adapter.joined
        stop_file.write_text("stop\n", encoding="utf-8")
        sampler.wait(timeout=15)
        summary = {"cell": cell, "mode": "smoke" if smoke else "formal",
                   "run_root": root.relative_to(ROOT).as_posix(),
                   "elapsed_seconds": monotonic() - started, "period_seconds": period,
                   **counters, "model_identity": identity,
                   "source_created": factory.created if factory is not None else 0,
                   "worker_exited": monitoring.wait(timeout=0) if monitoring is not None else True,
                   "sampler_exit_code": sampler.returncode,
                   "sampler_samples": max(0, sum(1 for _ in sampler_output.open(encoding="utf-8")) - 1),
                   "failure": failure}
        (root / "outputs/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary), flush=True)
    if summary["sampler_exit_code"] != 0 or not summary["worker_exited"]:
        raise RuntimeError("worker or external sampler did not exit cleanly")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", choices=CELLS, required=True)
    parser.add_argument("--seconds", type=float, default=1200.0)
    parser.add_argument("--period", type=float, default=8.0)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    run(args.cell, seconds=args.seconds, period=args.period, smoke=args.smoke)
