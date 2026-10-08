"""Measure OpenVINO model-only CPU latency across thread counts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
import openvino as ov


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=90)
    args = parser.parse_args()

    capture = cv2.VideoCapture(str(args.video))
    frames = []
    try:
        while len(frames) < args.frames:
            ok, frame = capture.read()
            if not ok:
                break
            # This measures only model execution; production preprocessing
            # still belongs in the end-to-end benchmark.
            resized = cv2.resize(frame, (640, 640))
            tensor = np.ascontiguousarray(resized.transpose(2, 0, 1)[None]).astype(np.float32) / 255
            frames.append(tensor)
    finally:
        capture.release()

    core = ov.Core()
    model = core.read_model(str(args.model / "best.xml"))
    for threads in (1, 2, 4, 6, 8, 12):
        compiled = core.compile_model(model, "CPU", {
            "PERFORMANCE_HINT": "LATENCY",
            "INFERENCE_PRECISION_HINT": ov.Type.f32,
            "INFERENCE_NUM_THREADS": threads,
        })
        for frame in frames[:5]:
            compiled(frame)
        start = perf_counter()
        for frame in frames:
            compiled(frame)
        elapsed = perf_counter() - start
        print(json.dumps({"threads": threads, "frames": len(frames),
                          "model_fps": round(len(frames)/elapsed, 2),
                          "model_ms": round(1000*elapsed/len(frames), 2)}), flush=True)


if __name__ == "__main__":
    main()
