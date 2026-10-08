"""Non-production tracker-only P/Q/R lifecycle attribution."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import threading
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import psutil

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from diagnostics.p9c3a_precomputed import load_fixture, sha256
from scripts.run_p9b_full_chain import diagnostic_cycle_pause
from scripts.run_p9c3_memory_attribution import VIDEO

FIXTURE = ROOT / "artifacts/p9c3/p9c3a-real-detections.json"


def load_real_fixture() -> dict:
    return load_fixture(
        FIXTURE, expected_mp4_sha256=sha256(VIDEO),
        expected_checkpoint_sha256=sha256(ROOT / "models/checkpoints/EXP-001/best.pt"),
        expected_config_sha256=sha256(ROOT / "configs/inference.yaml"),
        expected_lock_sha256=sha256(ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"),
    )


def person_inputs(fixture: dict, *, cycle: int, persistent: bool):
    """Rebuild real person detections with monotonic context in P."""
    if cycle < 0:
        raise ValueError("cycle must be nonnegative")
    for ordinal, row in enumerate(fixture["frames"]):
        frame_id = cycle * 47 + ordinal if persistent else ordinal
        timestamp = frame_id / 23.976 if persistent else ordinal / 23.976
        source = "mp4:p9c3c-tracker-control"
        detections = tuple(DetectionResult(
            frame_id=frame_id, timestamp=timestamp, source=source,
            detection=Detection(
                bbox=BoundingBox(**item["bbox"]), class_id=item["class_id"],
                class_name=item["class_name"], confidence=item["confidence"],
            ),
        ) for item in row["detections"] if item["class_id"] == 0)
        yield frame_id, timestamp, source, detections


def tracker_state(adapter: ByteTrackPersonTrackingAdapter | None) -> dict:
    backend = getattr(adapter, "_backend", None)
    native = getattr(backend, "_tracker", None)
    return {
        "native_tracker_live": int(native is not None),
        "tracked": len(native.tracked_stracks) if native is not None else 0,
        "lost": len(native.lost_stracks) if native is not None else 0,
        "removed": len(native.removed_stracks) if native is not None else 0,
        "native_frame_id": native.frame_id if native is not None else 0,
    }


def object_counts() -> dict:
    selected = {"STrack", "TrackResult", "KalmanFilterXYAH", "ndarray", "BYTETracker"}
    counts = {name: 0 for name in selected}
    for obj in gc.get_objects():
        name = type(obj).__name__
        if name in selected:
            counts[name] += 1
    return counts


class Probe:
    def __init__(self, root: Path, state: dict, adapter_ref) -> None:
        self.root, self.state, self.adapter_ref = root, state, adapter_ref
        self.stop = threading.Event()
        self.process = psutil.Process(os.getpid())
        self.start = perf_counter()
        (root / "attribution").mkdir(parents=True, exist_ok=True)
        self.out = (root / "attribution/probe.jsonl").open("w", encoding="utf-8")
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def sample(self) -> None:
        memory = self.process.memory_info()
        traced, peak = tracemalloc.get_traced_memory()
        row = {
            "elapsed_s": perf_counter() - self.start,
            "cycle": self.state["cycles"], "frames": self.state["updates"],
            "track_outputs": self.state["track_outputs"],
            "tracker_instances": self.state["tracker_instances"],
            "rss": memory.rss, "vms": memory.vms,
            "private": getattr(memory, "private", None),
            "threads": self.process.num_threads(),
            "handles": self.process.num_handles(),
            "open_files": len(self.process.open_files()),
            "traced_current": traced, "traced_peak": peak,
            "gc_objects": len(gc.get_objects()), "gc_counts": gc.get_count(),
            **tracker_state(self.adapter_ref()),
        }
        self.out.write(json.dumps(row) + "\n")
        self.out.flush()

    def _loop(self) -> None:
        while not self.stop.is_set():
            self.sample()
            self.stop.wait(5)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=6)
        self.sample()
        self.out.close()


def drive_cycle(mode: str, fixture: dict, cycle: int,
                adapter: ByteTrackPersonTrackingAdapter | None,
                state: dict) -> ByteTrackPersonTrackingAdapter | None:
    if mode == "Q":
        adapter = ByteTrackPersonTrackingAdapter()
        adapter._get_backend()._get_tracker()  # existing project factory path, diagnostic only
        state["tracker_instances"] += 1
        adapter.reset()
        return None

    if adapter is None:
        adapter = ByteTrackPersonTrackingAdapter()
    if mode == "R":
        adapter.reset()
    before = getattr(getattr(adapter, "_backend", None), "_tracker", None)
    for frame_id, timestamp, source, detections in person_inputs(
        fixture, cycle=cycle, persistent=mode == "P"
    ):
        tracks = adapter.update(detections, frame_id=frame_id,
                                timestamp=timestamp, source=source)
        state["updates"] += 1
        state["track_outputs"] += len(tracks)
        if before is None:
            state["tracker_instances"] += 1
            before = adapter._backend._tracker
    if mode == "R":
        adapter.reset()
    return adapter


def run(mode: str, seconds: float, period: float = 8.0) -> dict:
    if mode not in {"P", "Q", "R"} or seconds <= 0 or period < 0:
        raise ValueError("invalid tracker attribution run")
    fixture = load_real_fixture()
    root = ROOT / "artifacts/p9c3" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8])
    root.mkdir(parents=True)
    state = {"cycles": 0, "updates": 0, "track_outputs": 0, "tracker_instances": 0}
    holder = [None]
    tracemalloc.start(1)
    with Probe(root, state, lambda: holder[0]) as probe:
        start = probe.start
        while perf_counter() - start < seconds:
            cycle_start = perf_counter()
            holder[0] = drive_cycle(mode, fixture, state["cycles"], holder[0], state)
            state["cycles"] += 1
            remaining = seconds - (perf_counter() - start)
            if remaining > 0:
                probe.stop.wait(diagnostic_cycle_pause(
                    cycle_elapsed=perf_counter() - cycle_start,
                    target_period=period, remaining_duration=remaining,
                ))
        final_state = tracker_state(holder[0])
        objects = object_counts()
        (root / "attribution/objects-final.json").write_text(json.dumps(objects, indent=2), encoding="utf-8")
    output = {"mode": mode, "run_root": root.relative_to(ROOT).as_posix(),
              "elapsed_seconds": perf_counter() - start, **state,
              "final_tracker_state": final_state, "final_objects": objects,
              "fixture_sha256": sha256(FIXTURE),
              "tracker_config_sha256": sha256(ROOT / "configs/tracker.yaml")}
    (root / "attribution/summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("P", "Q", "R"), required=True)
    parser.add_argument("--seconds", type=float, default=1200)
    parser.add_argument("--period", type=float, default=8.0)
    args = parser.parse_args()
    print(json.dumps(run(args.mode, args.seconds, args.period)))


if __name__ == "__main__":
    main()
