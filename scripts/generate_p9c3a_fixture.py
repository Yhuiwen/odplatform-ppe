"""Generate and independently verify one diagnostic real-detection fixture."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from diagnostics.p9c3a_precomputed import (
    detection_template, fixture_from_results, load_fixture, sha256,
)
from scripts.run_p9c3_memory_attribution import VIDEO, cached_mp4_frames
from services.inference_service import InferenceService

CHECKPOINT = ROOT / "models/checkpoints/EXP-001/best.pt"
CONFIG = ROOT / "configs/inference.yaml"
LOCK = ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"
OUTPUT = ROOT / "artifacts/p9c3/p9c3a-real-detections.json"


def real_pass(frames, source_id):
    service = InferenceService(config_path=CONFIG, execution_enabled=True)
    return [service.infer_frame(frame, source=source_id) for frame in frames]


def main() -> None:
    metadata, frames = cached_mp4_frames()
    first = real_pass(frames, metadata.source_id)
    fixture = fixture_from_results(
        frames=frames, results_by_frame=first, source_path=VIDEO,
        checkpoint_path=CHECKPOINT, config_path=CONFIG, lock_path=LOCK,
        generated_at=datetime.now(timezone.utc).isoformat(), runtime=sys.version.split()[0],
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fixture, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    loaded = load_fixture(
        OUTPUT, expected_mp4_sha256=sha256(VIDEO),
        expected_checkpoint_sha256=sha256(CHECKPOINT),
        expected_config_sha256=sha256(CONFIG),
        expected_lock_sha256=sha256(LOCK),
    )
    second = real_pass(frames, metadata.source_id)
    if [[detection_template(item) for item in row] for row in second] != [row["detections"] for row in loaded["frames"]]:
        raise AssertionError("independent real inference pass differs from saved fixture")
    print(json.dumps({"path": str(OUTPUT), "sha256": sha256(OUTPUT),
                      "frames": loaded["total_frames"], "detections": loaded["total_detections"],
                      "classes": loaded["classes"], "independent_pass": "PASS"}))


if __name__ == "__main__":
    main()
