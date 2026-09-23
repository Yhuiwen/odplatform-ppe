"""Run Phase 4B-1 single-image inference and print JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from core.inference.detector import InferenceError
from services.inference_service import InferenceService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run YOLO11 inference on one image using the frozen runtime."
    )
    parser.add_argument("image", help="Path to one supported image file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        results = InferenceService().infer_image(args.image)
    except InferenceError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": exc.code,
                    "message": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "image": Path(args.image).name,
                "detections": [result.to_dict() for result in results],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
