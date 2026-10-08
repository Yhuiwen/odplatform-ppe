"""Run the real MonitoringService pipeline into an isolated P9-B workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, perf_counter_ns, sleep
from threading import Event, Thread, Lock
from uuid import uuid4

import psutil

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.events.event_engine import EventEngine
from core.rules.temporal_filter import TemporalViolationFilter
from core.schemas.video import SourceType
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.json_event_store import JSONEventStore
from infra.storage.snapshot_storage import SnapshotStorage
from services.alert_service import AlertService
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService
from services.event_query_service import EventQueryService
from services.event_service import EventService
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringService, MonitoringSourceRequest, build_video_source
from services.snapshot_service import SnapshotService


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def diagnostic_cycle_pause(*, cycle_elapsed: float, target_period: float,
                           remaining_duration: float) -> float:
    """Bound optional attribution pacing without extending the requested run."""
    return max(0.0, min(target_period - cycle_elapsed, remaining_duration))


class Recorder:
    def __init__(self) -> None:
        self.detection_classes: Counter[str] = Counter()
        self.track_ids: dict[int, list[int]] = {}
        self.track_details: dict[int, list[dict]] = {}
        self.associations: list[dict] = []
        self.association_candidates: list[dict] = []
        self.findings: Counter[str] = Counter()
        self.candidates: Counter[str] = Counter()
        self.first_seen: dict[tuple[int, str], int] = {}
        self.confirmed: dict[tuple[int, str], int] = {}
        self.events: dict[str, dict] = {}
        self.timeline: list[dict] = []
        self.current_operation: str | None = None
        self.frame_id: int | None = None
        self.cycle = 0
        self.stage_samples: list[dict] = []
        self.resource_samples: list[dict] = []
        self.metrics_enabled = False
        self.total_frames = 0
        self.total_events = 0
        self.total_ingested = 0
        self.total_snapshots = 0
        self.alert_success = 0
        self.alert_failure = 0
        self.frame_summaries: list[dict] = []
        self.last_detection_count = 0
        self.last_track_count = 0
        self.last_association_count = 0

    def mark(self, name: str, **details) -> None:
        self.timeline.append({"name": name, "at_ns": perf_counter_ns(), **details})


class RollingStreamList(list):
    """Append full diagnostics to JSONL while retaining at most ``limit`` rows."""

    def __init__(self, path: Path, limit: int = 200) -> None:
        super().__init__()
        self.path = path
        self.limit = limit
        self._handle = path.open("w", encoding="utf-8")
        self._lock = Lock()
        self.count = 0

    def append(self, item) -> None:
        with self._lock:
            self._handle.write(json.dumps(item, ensure_ascii=False) + "\n")
            self.count += 1
            if self.count % 100 == 0:
                self._handle.flush()
            super().append(item)
            if len(self) > self.limit:
                del self[0]

    def extend(self, items) -> None:
        for item in items:
            self.append(item)

    def close(self) -> None:
        with self._lock:
            self._handle.flush()
            self._handle.close()


class RollingDict(OrderedDict):
    """Keep a bounded recent diagnostic mapping."""

    def __init__(self, limit: int = 200) -> None:
        super().__init__()
        self.limit = limit

    def __setitem__(self, key, value) -> None:
        super().__setitem__(key, value)
        if len(self) > self.limit:
            self.popitem(last=False)

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]


class BoundedRecorder(Recorder):
    def __init__(self, root: Path, limit: int = 200) -> None:
        super().__init__()
        metrics_root = root / "metrics"
        metrics_root.mkdir(parents=True, exist_ok=True)
        self.track_ids = RollingDict(limit)
        self.track_details = RollingDict(limit)
        self.associations = RollingStreamList(metrics_root / "associations.jsonl", limit)
        self.association_candidates = RollingStreamList(metrics_root / "association-candidates.jsonl", limit)
        self.first_seen = RollingDict(limit)
        self.confirmed = RollingDict(limit)
        self.events = RollingDict(limit)
        self.timeline = RollingStreamList(metrics_root / "timeline.jsonl", limit)
        self.stage_samples = RollingStreamList(metrics_root / "stages.jsonl", limit)
        self.resource_samples = RollingStreamList(metrics_root / "resources.jsonl", limit)
        self.frame_summaries = RollingStreamList(metrics_root / "frames.jsonl", limit)

    def close(self) -> None:
        for name in ("associations", "association_candidates", "timeline", "stage_samples", "resource_samples", "frame_summaries"):
            getattr(self, name).close()


class Observed:
    """Forward to the real service, recording only successful outputs."""

    def __init__(self, target, method: str, after, recorder: Recorder | None = None) -> None:
        self.target = target
        self.method = method
        self.after = after
        self.recorder = recorder

    def __getattr__(self, name):
        if name != self.method:
            return getattr(self.target, name)
        real = getattr(self.target, name)

        def call(*args, **kwargs):
            started_ns = perf_counter_ns() if self.recorder is not None and self.recorder.metrics_enabled else None
            if self.recorder is not None:
                self.recorder.current_operation = self.method
                self.recorder.mark(self.method + "_start")
            try:
                result = real(*args, **kwargs)
            finally:
                if self.recorder is not None:
                    ended_ns = perf_counter_ns()
                    self.recorder.mark(self.method + "_end")
                    if started_ns is not None:
                        self.recorder.stage_samples.append({"cycle": self.recorder.cycle, "frame_id": self.recorder.frame_id, "stage": self.method, "ms": (ended_ns - started_ns) / 1_000_000})
                    self.recorder.current_operation = None
            self.after(result, args, kwargs, perf_counter_ns())
            return result

        return call


class ObservedSource:
    def __init__(self, source, recorder: Recorder) -> None:
        self.source = source
        self.recorder = recorder

    def __getattr__(self, name):
        return getattr(self.source, name)

    def _call(self, name):
        started_ns = perf_counter_ns() if self.recorder.metrics_enabled else None
        self.recorder.current_operation = "source." + name
        self.recorder.mark("source_" + name + "_start")
        try:
            return getattr(self.source, name)()
        finally:
            ended_ns = perf_counter_ns()
            self.recorder.mark("source_" + name + "_end")
            if started_ns is not None:
                self.recorder.stage_samples.append({"cycle": self.recorder.cycle, "frame_id": self.recorder.frame_id, "stage": "source_" + name, "ms": (ended_ns - started_ns) / 1_000_000})
            self.recorder.current_operation = None

    def open(self):
        return self._call("open")

    def read(self):
        return self._call("read")

    def close(self):
        return self._call("close")


class TimedAlertAdapter:
    def __init__(self, target, recorder: Recorder) -> None:
        self.target = target
        self.recorder = recorder
        self.name = target.name

    def send(self, message):
        started_ns = perf_counter_ns()
        try:
            return self.target.send(message)
        finally:
            self.recorder.stage_samples.append({"cycle": self.recorder.cycle, "frame_id": self.recorder.frame_id, "stage": "alert_" + self.name, "ms": (perf_counter_ns() - started_ns) / 1_000_000})


class ObservedMonitoringService(MonitoringService):
    def __init__(self, recorder: Recorder, **kwargs) -> None:
        self.recorder = recorder
        super().__init__(**kwargs)

    def _process_frame(self, frame, source_metadata):
        self.recorder.frame_id = frame.frame_id
        started_ns = perf_counter_ns() if self.recorder.metrics_enabled else None
        try:
            return super()._process_frame(frame, source_metadata)
        finally:
            self.recorder.total_frames += 1
            if started_ns is not None:
                self.recorder.stage_samples.append({"cycle": self.recorder.cycle, "frame_id": frame.frame_id, "stage": "frame_pipeline", "ms": (perf_counter_ns() - started_ns) / 1_000_000})
                self.recorder.frame_summaries.append({"cycle": self.recorder.cycle, "frame_id": frame.frame_id, "detections": self.recorder.last_detection_count, "tracks": self.recorder.last_track_count, "associations": self.recorder.last_association_count, "elapsed_ms": (perf_counter_ns() - started_ns) / 1_000_000})
            if self._stop_event.is_set():
                self.recorder.mark("worker_observed_stop", frame_id=frame.frame_id)

    def _run(self, request, source):
        self.recorder.mark("worker_start")
        try:
            return super()._run(request, source)
        finally:
            self.recorder.mark("worker_exit")


class ObservedTemporalFilter(TemporalViolationFilter):
    def __init__(self, recorder: Recorder):
        super().__init__()
        self.recorder = recorder

    def update(self, result):
        confirmed = super().update(result)
        at = perf_counter_ns()
        for finding in confirmed:
            self.recorder.confirmed[(finding.track_id, finding.event_type.value)] = at
        return confirmed


def run(*, source_type: SourceType, location: str | int, seconds: float = 40.0, diagnose_stop: bool = False, cycles: int = 1, min_frames: int = 0, metrics: bool = False, artifact_kind: str = "p9b", min_duration: float = 0.0, stop_trigger: str | None = None, stop_after_frames: int = 0, bounded: bool = False, restart_seconds: float = 0.0, diagnostic_probe=None, diagnostic_alert_factory=None, diagnostic_source_factory=None, diagnostic_inference_service=None, diagnostic_tracker=None, diagnostic_cycle_period_seconds: float = 0.0) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    if artifact_kind not in {"p9b", "p9c", "p9c2", "p9c3"}:
        raise ValueError("artifact_kind must be p9b, p9c, p9c2 or p9c3")
    root = ROOT / "artifacts" / artifact_kind / run_id
    for part in ("database", "snapshots", "logs", "outputs", "reports"):
        (root / part).mkdir(parents=True, exist_ok=False)
    recorder = BoundedRecorder(root) if bounded else Recorder()
    recorder.metrics_enabled = metrics
    database = Database(root / "database/events.sqlite3")
    events = EventRepository(database)
    snapshots = SnapshotRepository(database)
    storage = SnapshotStorage(root / "snapshots")
    query = EventQueryService(events, snapshots, storage)
    console_lines: list[str] = RollingStreamList(root / "logs/console_alerts.jsonl") if bounded else []
    web = WebAlertAdapter()
    console = ConsoleAlertAdapter(sink=console_lines.append)
    if diagnostic_alert_factory is not None:
        console, web = diagnostic_alert_factory()
    alert_adapters = (TimedAlertAdapter(console, recorder), TimedAlertAdapter(web, recorder)) if metrics else (console, web)

    def detection_after(result, _args, _kwargs, _at):
        recorder.detection_classes.update(item.class_name for item in result)
        recorder.last_detection_count = len(result)

    def tracking_after(result, _args, kwargs, _at):
        recorder.track_ids[kwargs["frame_id"]] = [item.track_id for item in result]
        recorder.track_details[kwargs["frame_id"]] = [item.to_dict() for item in result]
        recorder.last_track_count = len(result)

    def association_after(result, _args, _kwargs, _at):
        recorder.associations.extend(item.to_dict() for item in result.associations)
        recorder.last_association_count = len(result.associations)
        for association in result.associations:
            for track in result.tracks:
                containment, iou = PPEPersonAssociationAdapter._measure_pair(association.ppe.bbox, track.bbox)
                recorder.association_candidates.append({
                    "frame_id": result.frame_id,
                    "ppe_class": association.ppe.class_name,
                    "ppe_confidence": association.ppe.confidence,
                    "ppe_bbox": association.ppe.bbox.as_tuple(),
                    "track_id": track.track_id,
                    "track_confidence": track.confidence,
                    "track_bbox": track.bbox.as_tuple(),
                    "containment_ratio": containment,
                    "iou": iou,
                    "selected_track_id": association.track_id,
                    "status": association.status.value,
                })

    def compliance_after(result, _args, _kwargs, at):
        for finding in result.findings:
            recorder.findings[f"{finding.event_type.value}:{finding.state.value}"] += 1
        for finding in result.candidate_findings:
            key = (finding.track_id, finding.event_type.value)
            recorder.candidates[finding.event_type.value] += 1
            recorder.first_seen.setdefault(key, at)

    def event_after(result, _args, _kwargs, at):
        for event in result:
            recorder.total_events += 1
            key = (event.track_id, event.event_type.value)
            recorder.events[event.event_id] = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "track_id": event.track_id,
                "source_timestamp": event.timestamp,
                "confidence": event.confidence,
                "t0_first_candidate_ns": recorder.first_seen.get(key),
                "t1_temporal_confirmed_ns": recorder.confirmed.get(key),
                "t2_event_created_ns": at,
            }

    def ingest_after(result, args, kwargs, at):
        recorder.total_ingested += 1
        event = args[0]
        recorder.events[event.event_id].update(
            source=kwargs["source"], frame_id=kwargs["frame_id"],
            persisted_id=result.id, t3_sqlite_persisted_ns=at,
        )

    def snapshot_after(result, args, _kwargs, at):
        recorder.total_snapshots += 1
        recorder.events[args[0]].update(
            snapshot_relative_path=result.relative_path,
            snapshot_sha256=result.sha256,
            snapshot_width=result.width,
            snapshot_height=result.height,
            t4_snapshot_persisted_ns=at,
        )

    def alert_after(result, args, _kwargs, at):
        recorder.alert_success += sum(item.delivered for item in result)
        recorder.alert_failure += sum(item.status.value == "failed" for item in result)
        recorder.events[args[0].id].update(
            alert_results=[item.to_dict() for item in result],
            t5_alert_complete_ns=at,
        )

    inference_service = diagnostic_inference_service or InferenceService(config_path="configs/inference.yaml", execution_enabled=True)
    if metrics and diagnostic_inference_service is None:
        for method_name in ("_verify_checkpoint", "_load_model"):
            original = getattr(inference_service.detector, method_name)
            def measured(*args, _original=original, _name=method_name, **kwargs):
                start_ns = perf_counter_ns()
                try:
                    return _original(*args, **kwargs)
                finally:
                    recorder.stage_samples.append({"cycle": recorder.cycle, "frame_id": recorder.frame_id, "stage": _name, "ms": (perf_counter_ns() - start_ns) / 1_000_000})
            setattr(inference_service.detector, method_name, measured)
    service_type = ObservedMonitoringService if diagnose_stop or metrics else MonitoringService
    service = service_type(
        **({"recorder": recorder} if diagnose_stop or metrics else {}),
        inference_service=Observed(inference_service, "infer_frame", detection_after, recorder if diagnose_stop or metrics else None),
        tracker=Observed(diagnostic_tracker or ByteTrackPersonTrackingAdapter(), "update", tracking_after, recorder if diagnose_stop or metrics else None),
        association_adapter=Observed(PPEPersonAssociationAdapter(), "associate", association_after, recorder if metrics else None),
        compliance_service=Observed(ComplianceService(), "evaluate", compliance_after, recorder if metrics else None),
        event_service=Observed(EventService(engine=EventEngine(temporal_filter=ObservedTemporalFilter(recorder)), store=JSONEventStore(root / "logs/events.jsonl")), "process", event_after, recorder if metrics else None),
        ingest_service=Observed(EventIngestService(events), "ingest", ingest_after, recorder if metrics else None),
        snapshot_service=Observed(SnapshotService(events, snapshots, storage), "capture", snapshot_after, recorder if metrics else None),
        alert_service=Observed(AlertService(alert_adapters), "dispatch_event", alert_after, recorder if metrics else None),
        event_loader=events.get,
        **({"source_factory": lambda request: ObservedSource((diagnostic_source_factory or build_video_source)(request), recorder)} if diagnose_stop or metrics else ({"source_factory": diagnostic_source_factory} if diagnostic_source_factory else {})),
    )
    if diagnostic_probe is not None:
        diagnostic_probe.attach(root=root, service=service, console=console, web=web, recorder=recorder)
    request = MonitoringSourceRequest(source_type=source_type, location=location)
    start = perf_counter()
    cycle_results: list[dict] = RollingStreamList(root / "metrics/cycles.jsonl") if bounded else []
    sampler_stop = Event()
    process = psutil.Process(os.getpid())
    process.cpu_percent(interval=None)
    def sample_resources():
        while not sampler_stop.is_set():
            status = service.status()
            try:
                open_files = len(process.open_files()) if bounded else None
            except (psutil.Error, OSError):
                open_files = None
            recorder.resource_samples.append({"elapsed_seconds": perf_counter() - start, "cpu_percent": process.cpu_percent(interval=None), "rss_bytes": process.memory_info().rss, "threads": process.num_threads(), "handles": process.num_handles() if hasattr(process, "num_handles") else None, "open_files": open_files, "frames": recorder.total_frames if bounded else status.frames_processed, "events": recorder.total_events if bounded else status.events_generated, "snapshots": recorder.total_snapshots if bounded else None, "alerts": recorder.alert_success if bounded else status.alerts_delivered, "alert_failures": recorder.alert_failure if bounded else status.alerts_failed, "database_bytes": database.path.stat().st_size if database.path and database.path.exists() else 0, "snapshot_bytes": sum(p.stat().st_size for p in (root / "snapshots").rglob("*") if p.is_file())})
            if diagnostic_probe is not None:
                diagnostic_probe.sample(elapsed=perf_counter() - start, cycle=recorder.cycle, process=process)
            sampler_stop.wait(5.0 if bounded else (1.0 if metrics else 5.0))
    sampler = Thread(target=sample_resources, daemon=True)
    if metrics:
        sampler.start()
    cycle = 0
    while cycle < cycles or (source_type is SourceType.MP4 and min_duration and perf_counter() - start < min_duration):
        recorder.cycle = cycle + 1
        cycle_start = perf_counter()
        service.start(request)
        if source_type is SourceType.MP4:
            completed = service.wait(timeout=180)
            if not completed:
                service.stop()
        else:
            deadline = perf_counter() + (restart_seconds if restart_seconds and cycle > 0 else seconds)
            observed_read_end = None
            while perf_counter() < deadline:
                current_frames = service.status().frames_processed
                if stop_trigger == "warm_steady" and current_frames >= stop_after_frames:
                    break
                if stop_trigger == "warm_infer" and current_frames >= stop_after_frames and recorder.current_operation == "infer_frame":
                    break
                if stop_trigger == "cold_infer" and current_frames == 0 and recorder.current_operation == "infer_frame":
                    break
                if stop_trigger == "after_read" and current_frames >= stop_after_frames:
                    read_ends = sum(item["name"] == "source_read_end" for item in recorder.timeline)
                    if observed_read_end is not None and read_ends > observed_read_end:
                        break
                    observed_read_end = read_ends
                if min_frames and service.status().frames_processed >= min_frames:
                    break
                sleep(0.001 if stop_trigger else 0.05)
            if diagnose_stop:
                recorder.mark("stop_requested", cycle=cycle + 1, current_operation=recorder.current_operation, frames=service.status().frames_processed)
            stop_status = service.stop()
            if diagnose_stop:
                recorder.mark("stop_returned", cycle=cycle + 1, state=stop_status.state.value, error_code=stop_status.error_code)
            service.wait(timeout=30 if diagnose_stop else 10)
        cycle_results.append({"cycle": cycle + 1, "status": service.status().to_dict(), "elapsed_seconds": perf_counter() - cycle_start, "worker_exited": service.wait(timeout=0)})
        if diagnostic_probe is not None:
            diagnostic_probe.cycle_end(cycle=cycle + 1, elapsed=perf_counter() - start)
        cycle += 1
        if diagnostic_cycle_period_seconds > 0 and min_duration and perf_counter() - start < min_duration:
            sleep(diagnostic_cycle_pause(
                cycle_elapsed=perf_counter() - cycle_start,
                target_period=diagnostic_cycle_period_seconds,
                remaining_duration=min_duration - (perf_counter() - start),
            ))
    if metrics:
        sampler_stop.set()
        sampler.join(timeout=2)
    elapsed = perf_counter() - start
    status = service.status()
    page = query.list_events(limit=1000)
    verified = {item.id: query.evidence(item.id).verified for item in page.items if query.evidence(item.id) is not None}
    if not bounded:
        (root / "logs/console_alerts.jsonl").write_text("\n".join(console_lines) + ("\n" if console_lines else ""), encoding="utf-8")
    summary = {
        "run_id": run_id,
        "run_root": root.relative_to(ROOT).as_posix(),
        "source_type": source_type.value,
        "source": str(location),
        "source_sha256": _sha256(Path(location)) if source_type is SourceType.MP4 else None,
        "checkpoint_sha256": _sha256(ROOT / "models/checkpoints/EXP-001/best.pt"),
        "runtime": sys.version.split()[0],
        "status": status.to_dict(),
        "elapsed_seconds": elapsed,
        "processing_fps": status.frames_processed / elapsed if elapsed else None,
        "detection_classes": dict(recorder.detection_classes),
        "track_ids_by_frame": recorder.track_ids,
        "track_details_by_frame": recorder.track_details,
        "associations": recorder.associations,
        "association_candidates": recorder.association_candidates,
        "cycles": cycle_results,
        "compliance_findings": dict(recorder.findings),
        "candidate_findings": dict(recorder.candidates),
        "events": list(recorder.events.values()),
        "sqlite_count": page.total_count,
        "verified_evidence": verified,
        "web_alerts": [item.to_dict() for item in web.history()],
        "stop_timeline": recorder.timeline if diagnose_stop else None,
        "stage_samples": recorder.stage_samples if metrics else None,
        "resource_samples": recorder.resource_samples if metrics else None,
        "total_frames": recorder.total_frames,
        "total_events": recorder.total_events,
        "total_snapshots": recorder.total_snapshots,
        "alert_success": recorder.alert_success,
        "alert_failure": recorder.alert_failure,
        "bounded_observer": bounded,
        "observer_counts": {"stages": recorder.stage_samples.count, "resources": recorder.resource_samples.count, "frames": recorder.frame_summaries.count, "cycles": cycle_results.count} if bounded else None,
    }
    output = root / "outputs/full_chain.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if bounded:
        recorder.close()
        console_lines.close()
        cycle_results.close()
    if diagnostic_probe is not None:
        diagnostic_probe.finish(elapsed=elapsed)
    print(json.dumps({"run_root": summary["run_root"], "state": status.state.value, "frames": status.frames_processed, "events": status.events_generated, "sqlite": page.total_count, "output": str(output)}, ensure_ascii=False))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("mp4", "usb"), default="mp4")
    parser.add_argument("--video", default="artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4")
    parser.add_argument("--seconds", type=float, default=40.0)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--diagnose-stop", action="store_true")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--min-frames", type=int, default=0)
    args = parser.parse_args()
    if args.source == "mp4":
        location = str((ROOT / args.video).resolve())
        source_type = SourceType.MP4
    else:
        location = args.camera_index
        source_type = SourceType.USB_CAMERA
    summary = run(source_type=source_type, location=location, seconds=args.seconds, diagnose_stop=args.diagnose_stop, cycles=args.cycles, min_frames=args.min_frames)
    return 0 if summary["status"]["state"] in {"completed", "stopped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
