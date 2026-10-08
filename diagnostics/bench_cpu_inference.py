"""Exploratory warm CPU YOLO inference benchmark; no production state writes."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from time import perf_counter

import cv2
import torch
from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--sizes", type=int, nargs="+", default=[640, 512, 416, 320])
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    capture = cv2.VideoCapture(str(args.video))
    frames = []
    try:
        while len(frames) < args.frames:
            ok, frame = capture.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        capture.release()
    if not frames:
        raise RuntimeError("No video frames were decoded")

    model = YOLO(str(args.model), task="detect")
    for size in args.sizes:
        for frame in frames[:5]:
            model.predict(frame, imgsz=size, conf=0.25, iou=0.45,
                          device="cpu", classes=[0, 1, 2, 3, 4],
                          max_det=300, verbose=False)
        timings = []
        counts: Counter[int] = Counter()
        for frame in frames:
            start = perf_counter()
            result = model.predict(frame, imgsz=size, conf=0.25, iou=0.45,
                                   device="cpu", classes=[0, 1, 2, 3, 4],
                                   max_det=300, verbose=False)[0]
            timings.append(perf_counter() - start)
            counts.update(int(item) for item in result.boxes.cls.tolist())
        print(json.dumps({"size": size, "threads": args.threads,
                          "frames": len(frames), "mean_ms": round(statistics.mean(timings)*1000, 2),
                          "median_ms": round(statistics.median(timings)*1000, 2),
                          "fps": round(len(frames)/sum(timings), 2),
                          "detections_by_class": dict(sorted(counts.items()))}), flush=True)


if __name__ == "__main__":
    main()
