"""Generate and independently verify formal ByteTrack output for 47 frames."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from diagnostics.p9c3a_precomputed import PrecomputedInferenceService, load_fixture, sha256
from diagnostics.p9c3b_precomputed_tracking import load_track_fixture, track_template
from scripts.run_p9c3_memory_attribution import VIDEO, cached_mp4_frames

DETECTIONS = ROOT / "artifacts/p9c3/p9c3a-real-detections.json"
OUTPUT = ROOT / "artifacts/p9c3/p9c3b-real-tracks.json"
TRACKER_CONFIG = ROOT / "configs/tracker.yaml"


def real_pass(frames, source_id, detection_fixture):
    inference = PrecomputedInferenceService(detection_fixture)
    tracker = ByteTrackPersonTrackingAdapter()
    tracker.reset()
    rows = []
    for ordinal, frame in enumerate(frames):
        detections = inference.infer_frame(frame, source=source_id)
        person_detections = [item for item in detections if item.class_id == 0]
        tracks = tracker.update(person_detections, frame_id=frame.frame_id,
                                timestamp=frame.timestamp, source=source_id)
        rows.append({"ordinal": ordinal,
                     "tracks": [track_template(item, person_detections) for item in tracks]})
    return rows


def main() -> None:
    metadata, frames = cached_mp4_frames()
    detection_fixture = load_fixture(
        DETECTIONS, expected_mp4_sha256=sha256(VIDEO),
        expected_checkpoint_sha256=sha256(ROOT / "models/checkpoints/EXP-001/best.pt"),
        expected_config_sha256=sha256(ROOT / "configs/inference.yaml"),
        expected_lock_sha256=sha256(ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"),
    )
    first = real_pass(frames, metadata.source_id, detection_fixture)
    fixture = {
        "schema": "p9c3b-real-tracks-v1", "diagnostic_only": True,
        "detection_fixture_sha256": sha256(DETECTIONS),
        "tracker_config_sha256": sha256(TRACKER_CONFIG),
        "ultralytics_version": version("ultralytics"), "lap_version": version("lap"),
        "runtime": sys.version.split()[0],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_frames": len(first),
        "total_tracks": sum(len(row["tracks"]) for row in first),
        "frames": first,
    }
    OUTPUT.write_text(json.dumps(fixture, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    loaded = load_track_fixture(
        OUTPUT, detection_sha256=sha256(DETECTIONS),
        tracker_config_sha256=sha256(TRACKER_CONFIG),
        ultralytics_version=version("ultralytics"), lap_version=version("lap"),
    )
    second = real_pass(frames, metadata.source_id, detection_fixture)
    if second != loaded["frames"]:
        raise AssertionError("second real ByteTrack pass differs from first")
    print(json.dumps({"path": str(OUTPUT), "sha256": sha256(OUTPUT),
                      "frames": loaded["total_frames"], "tracks": loaded["total_tracks"],
                      "independent_pass": "PASS"}))


if __name__ == "__main__":
    main()
