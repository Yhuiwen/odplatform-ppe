"""P9-C.3e H: reuse the historical N harness with frozen precomputed inputs."""

from __future__ import annotations

import argparse
import gc
import json
import sys
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schemas.video import SourceType
from diagnostics.p9c3a_precomputed import PrecomputedInferenceService
from diagnostics.p9c3b_precomputed_tracking import PrecomputedTrackingAdapter
from scripts.run_p9b_full_chain import RollingStreamList, run
from scripts.run_p9c3_memory_attribution import MemoryProbe, VIDEO, CachedFrameSource, cached_mp4_frames
from scripts.run_p9c3d_downstream_stages import load_fixtures


ROLLING_NAMES = (
    "track_ids", "track_details", "associations", "association_candidates",
    "first_seen", "confirmed", "events", "timeline", "stage_samples",
    "resource_samples", "frame_summaries",
)


def recorder_cardinalities(recorder) -> dict:
    return {name: {"length": len(getattr(recorder, name)),
                   "cap": getattr(getattr(recorder, name), "limit", None),
                   "lines_written": getattr(getattr(recorder, name), "count", None)}
            for name in ROLLING_NAMES}


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


class BridgeProbe(MemoryProbe):
    """Companion boundedness stream; leaves the historical N probe intact."""

    def __init__(self) -> None:
        super().__init__(marks=())
        self.extra = None
        self.max_lengths: dict[str, int] = {}
        self.last_row = None
        self.line_scan_state: dict[str, tuple[int, int]] = {}

    def attach(self, *, root, service, console, web, recorder) -> None:
        super().attach(root=root, service=service, console=console, web=web, recorder=recorder)
        self.extra = (root / "attribution/harness-cardinality.jsonl").open("w", encoding="utf-8")

    def sample(self, *, elapsed, cycle, process) -> None:
        super().sample(elapsed=elapsed, cycle=cycle, process=process)
        containers = recorder_cardinalities(self.recorder)
        for name, value in containers.items():
            self.max_lengths[name] = max(self.max_lengths.get(name, 0), value["length"])
        metrics = self.root / "metrics"
        frame_objects = ndarray_objects = 0
        for obj in gc.get_objects():
            name = type(obj).__name__
            frame_objects += name == "FrameData"
            ndarray_objects += name == "ndarray"
        row = {
            "elapsed_s": elapsed, "cycle": cycle,
            "containers": containers,
            "cycle_history": {"length": None, "cap": 200,
                              "lines_written": self.streamed_lines(metrics / "cycles.jsonl")},
            "console_history": {"length": None, "cap": 200,
                                "lines_written": self.streamed_lines(self.root / "logs/console_alerts.jsonl")},
            "jsonl_bytes": {name: file_size(path) for name, path in {
                "events": self.root / "logs/events.jsonl",
                "frames": metrics / "frames.jsonl",
                "stages": metrics / "stages.jsonl",
                "associations": metrics / "associations.jsonl",
                "timeline": metrics / "timeline.jsonl",
                "cycles": metrics / "cycles.jsonl",
                "console": self.root / "logs/console_alerts.jsonl",
                "resources": metrics / "resources.jsonl",
            }.items()},
            "event_jsonl_lines": self.streamed_lines(self.root / "logs/events.jsonl"),
            "frame_data_gc": frame_objects, "ndarray_gc": ndarray_objects,
            "alert_console_completed": len(self.console._completed),
            "alert_web_completed": len(self.web._completed),
            "web_history": len(self.web._history),
        }
        self.last_row = row
        self.extra.write(json.dumps(row) + "\n")
        self.extra.flush()

    def streamed_lines(self, path: Path) -> int:
        """Count only newly flushed bytes; never load the entire JSONL file."""
        key = str(path)
        offset, count = self.line_scan_state.get(key, (0, 0))
        if path.exists():
            with path.open("rb") as handle:
                handle.seek(offset)
                for block in iter(lambda: handle.read(65536), b""):
                    count += block.count(b"\n")
                offset = handle.tell()
        self.line_scan_state[key] = (offset, count)
        return count

    def finish(self, *, elapsed) -> None:
        self.extra.close()
        super().finish(elapsed=elapsed)
        (self.root / "attribution/harness-cardinality-summary.json").write_text(
            json.dumps({"max_lengths": self.max_lengths, "end": self.last_row}, indent=2),
            encoding="utf-8",
        )


def run_bridge(*, seconds: float = 1200, smoke: bool = False) -> dict:
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    metadata, frames = cached_mp4_frames()
    detection, track = load_fixtures()
    inference = PrecomputedInferenceService(detection)
    tracker = PrecomputedTrackingAdapter(track)
    probe = BridgeProbe()
    tracemalloc.start(1)
    summary = run(
        source_type=SourceType.MP4, location=str(VIDEO),
        seconds=seconds if smoke else 1.0,
        cycles=1, min_duration=0.0 if smoke else seconds,
        metrics=True, bounded=True, artifact_kind="p9c3",
        diagnostic_probe=probe,
        diagnostic_source_factory=lambda _request: CachedFrameSource(metadata, frames),
        diagnostic_inference_service=inference,
        diagnostic_tracker=tracker,
        diagnostic_cycle_period_seconds=0.0 if smoke else 8.0,
    )
    output = {"run_root": summary["run_root"], "smoke": smoke,
              "cycles": summary["observer_counts"]["cycles"],
              "frames": summary["total_frames"],
              "events": summary["total_events"],
              "sqlite_rows": summary["sqlite_count"],
              "snapshots": summary["total_snapshots"],
              "alerts": summary["alert_success"],
              "elapsed_seconds": summary["elapsed_seconds"]}
    print(json.dumps(output), flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=1200)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    run_bridge(seconds=args.seconds, smoke=args.smoke)


if __name__ == "__main__":
    main()
