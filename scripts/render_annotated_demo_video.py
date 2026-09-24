"""CLI for M-007 annotated local MP4 rendering."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.annotated_video_service import AnnotatedVideoService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render one local MP4 with M-007 annotations."
    )
    parser.add_argument("video", help="Path to one local .mp4 video")
    parser.add_argument(
        "--output-dir",
        help="New output directory; defaults to artifacts/inference/annotated/<run-id>",
    )
    parser.add_argument(
        "--config",
        default="configs/inference.yaml",
        help="Frozen inference configuration path",
    )
    parser.add_argument(
        "--authorized-execution",
        action="store_true",
        help=(
            "Explicit validation authorization required while the frozen "
            "config keeps execution_enabled: false"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        service = AnnotatedVideoService(
            args.config,
            execution_enabled=True if args.authorized_execution else None,
        )
        result = service.render_video(
            args.video,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        code = str(getattr(exc, "code", "m007_unexpected_error"))
        print(
            json.dumps(
                {
                    "status": "error",
                    "run_id": None,
                    "output_video": None,
                    "processed_frames": 0,
                    "source_frames": None,
                    "elapsed_seconds": 0.0,
                    "error": code,
                    "message": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    print(json.dumps(result.to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
