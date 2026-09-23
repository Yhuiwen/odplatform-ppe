"""CLI for one local MP4 video inference run."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from core.inference.detector import InferenceError
from core.video.reader import VideoError
from services.video_inference_service import VideoInferenceService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local MP4 inference")
    parser.add_argument("video", help="Path to a local .mp4 video")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = VideoInferenceService().infer_video(args.video)
    except (InferenceError, VideoError) as exc:
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
            {"status": "ok", **result.to_dict()},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
