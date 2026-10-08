"""Isolated P9-C.3 attribution experiments; never used by production runtime."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import tracemalloc
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, sleep
from uuid import uuid4

import psutil

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schemas.alerts import AlertMessage, AlertResult, AlertStatus
from core.schemas.compliance import ComplianceEventType
from core.schemas.video import SourceState, SourceType
from core.video.mp4_source import MP4VideoSource
from core.video.video_source import BaseVideoSource
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from scripts.run_p9b_full_chain import run

VIDEO = ROOT / "artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4"


def count_state(service, console, web, recorder) -> dict:
    """Read existing implementation fields without changing their contracts."""
    def unwrap(value):
        return getattr(value, "target", value)

    def length(owner, field):
        value = getattr(owner, field, None) if owner is not None else None
        return len(value) if value is not None else "UNSUPPORTED"

    event = unwrap(getattr(service, "event_service", None))
    engine = getattr(event, "engine", None)
    temporal = getattr(engine, "temporal_filter", None)
    tracker = unwrap(getattr(service, "tracker", None))
    backend = getattr(tracker, "_backend", None)
    native_tracker = getattr(backend, "_tracker", None)
    status = service.status() if service is not None else None
    output = {
        "alert_console_completed": length(console, "_completed"),
        "alert_web_completed": length(web, "_completed"),
        "web_history": length(web, "_history"),
        "monitor_recent_events": length(status, "recent_events"),
        "event_active": length(engine, "_active"),
        "event_recovery": length(engine, "_recovery_counts"),
        "event_last_recovered": length(engine, "_last_recovered"),
        "temporal_states": length(temporal, "_states"),
        "tracker_active": length(native_tracker, "tracked_stracks"),
        "tracker_lost": length(native_tracker, "lost_stracks"),
        "tracker_removed": length(native_tracker, "removed_stracks"),
        "diagnostic_tracker_cursor": getattr(tracker, "_cursor", "UNSUPPORTED"),
        "diagnostic_tracker_sessions": getattr(tracker, "_session_count", "UNSUPPORTED"),
        "harness_cycles": getattr(recorder, "cycle", "UNSUPPORTED"),
        "harness_events": length(recorder, "events"),
        "harness_timeline": length(recorder, "timeline"),
        "harness_stages": length(recorder, "stage_samples"),
        "harness_frames": length(recorder, "frame_summaries"),
    }
    output["temporal_confidences_total"] = (
        sum(len(state.confidences) for state in temporal._states.values())
        if temporal is not None else "UNSUPPORTED"
    )
    return output


def object_counts() -> dict[str, int]:
    wanted = ("AlertResult", "AlertMessage", "DetectionResult", "Track", "Association", "ComplianceFinding", "ComplianceEvent", "PersistedEvent", "SnapshotReference", "FrameData", "ndarray")
    result = Counter()
    for obj in gc.get_objects():
        cls = type(obj)
        name = f"{cls.__module__}.{cls.__qualname__}"
        if any(part in name for part in wanted):
            result[name] += 1
    return dict(result)


class MemoryProbe:
    def __init__(self, marks=(120, 600, 1200, 1800), *, gc_diagnostic=False) -> None:
        self.marks = tuple(marks)
        self.done: set[int] = set()
        self.object_done: set[int] = set()
        self.snapshots = {}
        self.root = None
        self.service = None
        self.console = None
        self.web = None
        self.recorder = None
        self._samples = None
        self.gc_diagnostic = gc_diagnostic

    def attach(self, *, root, service, console, web, recorder) -> None:
        self.root, self.service, self.console, self.web, self.recorder = root, service, console, web, recorder
        (root / "attribution").mkdir(exist_ok=True)
        self._samples = (root / "attribution/probe.jsonl").open("w", encoding="utf-8")

    def sample(self, *, elapsed, cycle, process) -> None:
        memory = process.memory_info()
        traced, traced_peak = tracemalloc.get_traced_memory()
        row = {
            "elapsed_s": elapsed, "cycle": cycle,
            "frames": self.recorder.total_frames if self.recorder else None,
            "frame_id": getattr(self.recorder, "frame_id", None) if self.recorder else None,
            "total_detections": getattr(self.recorder, "total_detections", None) if self.recorder else None,
            "events": self.recorder.total_events if self.recorder else None,
            "sqlite_rows": self.recorder.total_ingested if self.recorder else None,
            "snapshots": self.recorder.total_snapshots if self.recorder else None,
            "alert_deliveries": self.recorder.alert_success if self.recorder else None,
            "rss": memory.rss, "vms": memory.vms,
            "private": getattr(memory, "private", None),
            "threads": process.num_threads(),
            "handles": process.num_handles() if hasattr(process, "num_handles") else None,
            "open_files": len(process.open_files()),
            "gc_objects": len(gc.get_objects()), "gc_counts": gc.get_count(),
            "traced_current": traced, "traced_peak": traced_peak,
            **count_state(self.service, self.console, self.web, self.recorder),
        }
        self._samples.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._samples.flush()
        for mark in (120, 1800):
            if elapsed >= mark and mark not in self.object_done:
                self.object_done.add(mark)
                (self.root / f"attribution/objects-{mark}.json").write_text(
                    json.dumps(object_counts(), indent=2), encoding="utf-8"
                )
        for mark in self.marks:
            if elapsed >= mark and mark not in self.done:
                self.done.add(mark)
                snapshot = tracemalloc.take_snapshot()
                self.snapshots[mark] = {
                    group: {
                        str(item.traceback): (item.size, item.count)
                        for item in snapshot.statistics(group)[:500]
                    }
                    for group in ("filename", "lineno", "traceback")
                }
                del snapshot
                self._write_diffs(mark)

    def _write_diffs(self, mark):
        previous = max((item for item in self.snapshots if item < mark), default=None)
        if previous is None:
            return
        current = self.snapshots[mark]
        baseline = self.snapshots[previous]
        output = {}
        for group in ("filename", "lineno", "traceback"):
            changes = []
            for key in current[group].keys() | baseline[group].keys():
                after_size, after_count = current[group].get(key, (0, 0))
                before_size, before_count = baseline[group].get(key, (0, 0))
                changes.append({"size_diff": after_size - before_size,
                                "count_diff": after_count - before_count,
                                "traceback": key})
            output[group] = sorted(changes, key=lambda item: item["size_diff"], reverse=True)[:25]
        (self.root / f"attribution/tracemalloc-{previous}-to-{mark}.json").write_text(
            json.dumps(output, indent=2), encoding="utf-8"
        )

    def cycle_end(self, *, cycle, elapsed) -> None:
        pass

    def finish(self, *, elapsed) -> None:
        if self.gc_diagnostic and self.root is not None:
            process = psutil.Process(os.getpid())
            before = {"rss": process.memory_info().rss,
                      "traced_current": tracemalloc.get_traced_memory()[0],
                      "gc_objects": len(gc.get_objects())}
            collected = gc.collect()
            after = {"rss": process.memory_info().rss,
                     "traced_current": tracemalloc.get_traced_memory()[0],
                     "gc_objects": len(gc.get_objects())}
            (self.root / "attribution/gc-diagnostic.json").write_text(
                json.dumps({"before": before, "collected": collected, "after": after}, indent=2),
                encoding="utf-8",
            )
        if self._samples is not None:
            self._samples.close()


class StatelessAttributionAlert:
    """NON-PRODUCTION adapter: identical success contract, no idempotency memory."""

    def __init__(self, name: str) -> None:
        self.name = name

    def send(self, message: AlertMessage) -> AlertResult:
        return AlertResult(
            event_id=message.event_id, adapter=self.name,
            status=AlertStatus.DELIVERED,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def history(self) -> tuple:
        return ()


def stateless_alerts():
    return StatelessAttributionAlert("console"), StatelessAttributionAlert("web")


class CachedFrameSource(BaseVideoSource):
    """Diagnostic control: same MP4 frames/metadata, no decoder in cycle loop."""

    source_type = SourceType.MP4

    def __init__(self, metadata, frames):
        super().__init__()
        self._cached_metadata = metadata
        self._cached_frames = frames
        self._index = 0

    def open(self):
        self._mark_opening()
        self._index = 0
        self._mark_live(self._cached_metadata)
        return self._cached_metadata

    def read(self):
        if self._state is not SourceState.LIVE:
            raise RuntimeError("cached source must be opened before reading")
        if self._index >= len(self._cached_frames):
            self._mark_ended()
            return None
        frame = self._cached_frames[self._index]
        self._index += 1
        return self._record_frame(frame)


def cached_mp4_frames():
    source = MP4VideoSource(VIDEO)
    metadata = source.open()
    try:
        frames = tuple(iter(source.read, None))
    finally:
        source.close()
    if len(frames) != 47:
        raise AssertionError(f"cached control expected 47 frames, got {len(frames)}")
    return metadata, frames


def run_full(seconds: float, *, stateless: bool, gc_diagnostic: bool = False,
             snapshot_diagnostic: bool = False, cached_source: bool = False,
             precomputed: bool = False, precomputed_tracks: bool = False) -> dict:
    cached = cached_mp4_frames() if cached_source or precomputed or precomputed_tracks else None
    diagnostic_inference = None
    if precomputed or precomputed_tracks:
        from diagnostics.p9c3a_precomputed import PrecomputedInferenceService, load_fixture, sha256
        diagnostic_fixture = load_fixture(
            ROOT / "artifacts/p9c3/p9c3a-real-detections.json",
            expected_mp4_sha256=sha256(VIDEO),
            expected_checkpoint_sha256=sha256(ROOT / "models/checkpoints/EXP-001/best.pt"),
            expected_config_sha256=sha256(ROOT / "configs/inference.yaml"),
            expected_lock_sha256=sha256(ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"),
        )
        diagnostic_inference = PrecomputedInferenceService(diagnostic_fixture)
    diagnostic_tracker = None
    if precomputed_tracks:
        from importlib.metadata import version
        from diagnostics.p9c3b_precomputed_tracking import PrecomputedTrackingAdapter, load_track_fixture
        track_fixture = load_track_fixture(
            ROOT / "artifacts/p9c3/p9c3b-real-tracks.json",
            detection_sha256=sha256(ROOT / "artifacts/p9c3/p9c3a-real-detections.json"),
            tracker_config_sha256=sha256(ROOT / "configs/tracker.yaml"),
            ultralytics_version=version("ultralytics"), lap_version=version("lap"),
        )
        diagnostic_tracker = PrecomputedTrackingAdapter(track_fixture)
    tracemalloc.start(1)
    probe = MemoryProbe(marks=(120, 300, 540) if snapshot_diagnostic else (),
                        gc_diagnostic=gc_diagnostic)
    result = run(
        source_type=SourceType.MP4, location=str(VIDEO), min_duration=seconds,
        metrics=True, bounded=True, artifact_kind="p9c3",
        diagnostic_probe=probe,
        diagnostic_alert_factory=stateless_alerts if stateless else None,
        diagnostic_source_factory=(lambda _request: CachedFrameSource(*cached)) if cached else None,
        diagnostic_inference_service=diagnostic_inference,
        diagnostic_tracker=diagnostic_tracker,
        diagnostic_cycle_period_seconds=8.0 if (precomputed or precomputed_tracks) and seconds >= 1200 else 0.0,
    )
    return {"run_root": result["run_root"], "cycles": result["observer_counts"]["cycles"],
            "frames": result["total_frames"], "events": result["total_events"],
            "elapsed_seconds": result["elapsed_seconds"],
            "mode": "N" if precomputed_tracks else "L" if precomputed else "K" if cached_source else "G" if gc_diagnostic else "T" if snapshot_diagnostic else "D" if stateless else "A"}


def run_source(seconds: float, *, cycle_period_seconds: float = 7.7) -> dict:
    tracemalloc.start(1)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3" / run_id
    root.mkdir(parents=True)
    probe = MemoryProbe(marks=())
    probe.attach(root=root, service=None, console=None, web=None, recorder=None)
    process = psutil.Process(os.getpid())
    start = perf_counter()
    cycles = frames = 0
    while perf_counter() - start < seconds:
        cycle_started = perf_counter()
        source = MP4VideoSource(VIDEO)
        source.open()
        current = 0
        try:
            while source.read() is not None:
                current += 1
        finally:
            source.close()
        if current != 47:
            raise AssertionError(f"source cycle {cycles + 1}: {current} frames")
        cycles += 1
        frames += current
        probe.sample(elapsed=perf_counter() - start, cycle=cycles, process=process)
        sleep(max(0.0, min(cycle_period_seconds - (perf_counter() - cycle_started),
                            seconds - (perf_counter() - start))))
    probe.sample(elapsed=perf_counter() - start, cycle=cycles, process=process)
    probe.finish(elapsed=perf_counter() - start)
    output = {"run_root": root.relative_to(ROOT).as_posix(), "mode": "B",
              "cycles": cycles, "frames": frames, "elapsed_seconds": perf_counter() - start}
    (root / "attribution/summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def run_source_rewind(seconds: float, *, cycle_period_seconds: float = 7.7) -> dict:
    """Supplemental source-only control; not the full-pipeline C experiment."""
    import cv2
    from diagnostics.p9c3_capture import open_diagnostic_capture

    tracemalloc.start(1)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3" / run_id
    root.mkdir(parents=True)
    probe = MemoryProbe(marks=())
    probe.attach(root=root, service=None, console=None, web=None, recorder=None)
    process = psutil.Process(os.getpid())
    capture = open_diagnostic_capture(VIDEO)
    start = perf_counter()
    cycles = frames = 0
    try:
        while perf_counter() - start < seconds:
            cycle_started = perf_counter()
            current = 0
            while True:
                ok, image = capture.read()
                if not ok:
                    break
                if image is None:
                    raise RuntimeError("persistent decoder returned no frame")
                current += 1
            if current != 47:
                raise AssertionError(f"rewind cycle {cycles + 1}: {current} frames")
            cycles += 1
            frames += current
            if not capture.set(cv2.CAP_PROP_POS_FRAMES, 0):
                raise RuntimeError("VideoCapture rewind failed")
            probe.sample(elapsed=perf_counter() - start, cycle=cycles, process=process)
            sleep(max(0.0, min(cycle_period_seconds - (perf_counter() - cycle_started),
                                seconds - (perf_counter() - start))))
    finally:
        capture.release()
        probe.finish(elapsed=perf_counter() - start)
    output = {"run_root": root.relative_to(ROOT).as_posix(), "mode": "C0_SOURCE_ONLY",
              "cycles": cycles, "frames": frames, "elapsed_seconds": perf_counter() - start}
    (root / "attribution/summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def run_alert_micro(count: int = 10000) -> dict:
    tracemalloc.start(1)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3" / run_id
    root.mkdir(parents=True)
    console = ConsoleAlertAdapter(sink=lambda _: None)
    web = WebAlertAdapter()
    process = psutil.Process(os.getpid())
    samples = []
    for index in range(count + 1):
        if index:
            message = AlertMessage(event_id=f"EVT-{index:032x}", timestamp="2026-09-25T00:00:00Z",
                                   track_id=1, alert_type=ComplianceEventType.PPE_UNKNOWN,
                                   confidence=0.0, snapshot=None, message="diagnostic")
            console.send(message)
            web.send(message)
        if index in {0, 100, 300, 600} or index % 1000 == 0:
            samples.append({"events": index, "console_completed": len(console._completed),
                            "web_completed": len(web._completed), "web_history": len(web._history),
                            "rss": process.memory_info().rss,
                            "traced_current": tracemalloc.get_traced_memory()[0]})
    output = {"mode": "E", "run_root": root.relative_to(ROOT).as_posix(), "samples": samples}
    (root / "summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def run_event_snapshot_micro(count: int = 1000) -> dict:
    """Formal persistence/snapshot components, without model or source loop."""
    from core.schemas.compliance import ComplianceEvent
    from infra.database.database import Database
    from infra.database.repository import EventRepository
    from infra.database.snapshot_repository import SnapshotRepository
    from infra.storage.snapshot_storage import SnapshotStorage
    from services.event_ingest_service import EventIngestService
    from services.snapshot_service import SnapshotService

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3" / run_id
    root.mkdir(parents=True)
    source = MP4VideoSource(VIDEO)
    source.open()
    frame = source.read()
    source.close()
    if frame is None:
        raise RuntimeError("frozen MP4 provided no diagnostic frame")
    image = frame.image
    del frame, source
    database = Database(root / "events.sqlite3")
    events = EventRepository(database)
    snapshots = SnapshotRepository(database)
    ingest = EventIngestService(events)
    snapshot_service = SnapshotService(events, snapshots, SnapshotStorage(root / "snapshots"))
    tracemalloc.start(1)
    process = psutil.Process(os.getpid())
    samples = []
    start = perf_counter()

    def sample(stage, index):
        samples.append({"stage": stage, "events": index, "elapsed_s": perf_counter() - start,
                        "rss": process.memory_info().rss,
                        "traced_current": tracemalloc.get_traced_memory()[0],
                        "handles": process.num_handles() if hasattr(process, "num_handles") else None,
                        "open_files": len(process.open_files())})

    sample("event", 0)
    for index in range(1, count + 1):
        event = ComplianceEvent(
            event_id=f"EVT-{index:032x}", track_id=1,
            event_type=ComplianceEventType.PPE_UNKNOWN,
            confidence=0.0, timestamp=float(index),
        )
        ingest.ingest(event, source="diagnostic:mp4", frame_id=index)
        if index % 100 == 0:
            sample("event", index)
    sample("snapshot", 0)
    for index in range(1, count + 1):
        snapshot_service.capture(f"EVT-{index:032x}", image)
        if index % 100 == 0:
            sample("snapshot", index)
    output = {"mode": "F", "run_root": root.relative_to(ROOT).as_posix(),
              "events": count, "snapshots": count, "samples": samples}
    (root / "summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return {key: output[key] for key in ("mode", "run_root", "events", "snapshots")}


def run_fixed_inference(iterations: int = 10000) -> dict:
    """Real frozen detector on one decoded frame; no source/event side effects."""
    from core.schemas.video import FrameData
    from services.inference_service import InferenceService

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = ROOT / "artifacts/p9c3" / run_id
    (root / "attribution").mkdir(parents=True)
    source = MP4VideoSource(VIDEO)
    source.open()
    first = source.read()
    source.close()
    if first is None:
        raise RuntimeError("frozen MP4 provided no diagnostic frame")
    image = first.image
    del first, source
    inference = InferenceService(config_path="configs/inference.yaml", execution_enabled=True)
    tracemalloc.start(1)
    process = psutil.Process(os.getpid())
    start = perf_counter()
    path = root / "attribution/probe.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        def sample(index):
            memory = process.memory_info()
            row = {"elapsed_s": perf_counter() - start, "cycle": index,
                   "frames": index, "events": 0, "rss": memory.rss,
                   "vms": memory.vms, "private": getattr(memory, "private", None),
                   "traced_current": tracemalloc.get_traced_memory()[0],
                   "threads": process.num_threads(),
                   "handles": process.num_handles() if hasattr(process, "num_handles") else None,
                   "open_files": len(process.open_files())}
            handle.write(json.dumps(row) + "\n")
            handle.flush()

        sample(0)
        for index in range(1, iterations + 1):
            frame = FrameData(frame_id=index, timestamp=float(index) / 23.976, image=image)
            inference.infer_frame(frame, source="diagnostic:fixed-frame")
            if index % 500 == 0:
                sample(index)
    output = {"mode": "I_FIXED_FRAME", "run_root": root.relative_to(ROOT).as_posix(),
              "iterations": iterations, "elapsed_seconds": perf_counter() - start}
    (root / "attribution/summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("A", "B", "C0", "D", "E", "F", "G", "I", "T", "K", "L", "N"), required=True)
    parser.add_argument("--seconds", type=float, default=None)
    parser.add_argument("--iterations", type=int, default=10000)
    args = parser.parse_args()
    result = (run_full(args.seconds or (1800 if args.mode == "A" else 1200 if args.mode in {"D", "K", "L", "N"} else 600 if args.mode == "T" else 1),
                       stateless=args.mode == "D", gc_diagnostic=args.mode == "G",
                       snapshot_diagnostic=args.mode == "T", cached_source=args.mode == "K",
                       precomputed=args.mode == "L", precomputed_tracks=args.mode == "N")
              if args.mode in {"A", "D", "G", "T", "K", "L", "N"} else
              run_source(args.seconds or 1200) if args.mode == "B" else
              run_source_rewind(args.seconds or 1200) if args.mode == "C0" else
              run_alert_micro() if args.mode == "E" else
              run_event_snapshot_micro() if args.mode == "F" else
              run_fixed_inference(args.iterations))
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
