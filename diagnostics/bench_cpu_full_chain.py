"""Isolated warm monitoring benchmark for candidate CPU input sizes."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import torch
import yaml

from core.inference.detector import YOLODetector
from core.schemas.video import SourceType
from services.monitoring_service import MonitoringSourceRequest
from web.monitoring_support import build_monitoring_runtime


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--openvino", type=Path)
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--real-alerts", action="store_true")
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    cv2.setNumThreads(1)
    with tempfile.TemporaryDirectory(prefix="odplatform-cpu-benchmark-") as tmp:
        os.environ["ODPLATFORM_P9B_VALIDATION_ROOT"] = tmp
        config = yaml.safe_load(Path("configs/inference.yaml").read_text(encoding="utf-8"))
        config["inference"]["preprocessing"]["imgsz"] = args.size
        candidate = Path(tmp) / "inference.yaml"
        candidate.write_text(yaml.safe_dump(config), encoding="utf-8")

        runtime = build_monitoring_runtime(SimpleNamespace(session_state={}))
        model_factory = None
        if args.openvino is not None:
            from ultralytics import YOLO

            model_factory = lambda _: YOLO(str(args.openvino), task="detect")
        if not args.production:
            runtime.service.inference_service.detector = YOLODetector(
                config_path=candidate, execution_enabled=True,
                model_factory=model_factory,
            )
        detector = runtime.service.inference_service.detector
        print(json.dumps({"detector_backend": detector.backend,
                          "detector_imgsz": detector.imgsz,
                          "detector_export": str(detector.export_path)}), flush=True)
        if not args.real_alerts:
            runtime.service.alert_service = SimpleNamespace(
                dispatch_event=lambda event: ()
            )

        capture = cv2.VideoCapture(str(args.video))
        ok, first = capture.read()
        capture.release()
        if not ok:
            raise RuntimeError("No first frame")
        runtime.service.inference_service.detector.detect_frame(
            first, frame_id=0, timestamp=0.0, source="warmup"
        )

        start = perf_counter()
        runtime.service.start(MonitoringSourceRequest(SourceType.MP4, str(args.video)))
        done = runtime.service.wait(timeout=180)
        elapsed = perf_counter() - start
        status = runtime.service.status()
        print(json.dumps({
            "size": args.size,
            "threads": args.threads,
            "backend": "production" if args.production else ("openvino" if args.openvino else "pytorch"),
            "done": done,
            "state": status.state.value,
            "frames": status.frames_processed,
            "elapsed_s": round(elapsed, 3),
            "fps": round(status.frames_processed / elapsed, 3),
            "detections": status.detections,
            "event_types": dict(Counter(event["type"] for event in status.recent_events)),
            "error_code": status.error_code,
            "alerts_delivered": status.alerts_delivered,
            "alerts_failed": status.alerts_failed,
        }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
