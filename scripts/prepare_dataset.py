"""Phase 1 commands for snapshotting and converting an official CSS export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.dataset_service import DatasetService
from services.dataset_conversion_service import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_DIR,
    DEFAULT_SOURCE_MANIFEST,
    DatasetConversionService,
)
from services.dataset_quality_service import DatasetQualityService
from utils.paths import DATA_DIR


DEFAULT_SNAPSHOT_DIR = DATA_DIR / "external" / "css-v27-yolov8"
DEFAULT_ARCHIVE_PATH = DEFAULT_SNAPSHOT_DIR / "archive" / "css-v27-yolov8.zip"
DEFAULT_MANIFEST_PATH = DEFAULT_SNAPSHOT_DIR / "metadata" / "checksums.sha256"
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "docs" / "dataset_snapshots" / "CSS_V27_YOLOV8.md"
)
DEFAULT_QUALITY_JSON_PATH = (
    DEFAULT_OUTPUT_DIR / "metadata" / "quality_report.json"
)
DEFAULT_QUALITY_MARKDOWN_PATH = (
    PROJECT_ROOT / "docs" / "17_DATASET_QUALITY_REPORT.md"
)


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))


def _inspect(args: argparse.Namespace) -> int:
    report = DatasetService().inspect_source(args.source)
    _print(report)
    return 0


def _snapshot(args: argparse.Namespace) -> int:
    service = DatasetService()
    if args.source_dir is not None:
        report = service.create_snapshot_from_directory(
            args.source_dir,
            args.output,
            downloaded_at=args.downloaded_at,
            summary_path=args.summary,
        )
    else:
        archive = args.archive or DEFAULT_ARCHIVE_PATH
        report = service.create_snapshot(
            archive,
            args.output,
            downloaded_at=args.downloaded_at,
            summary_path=args.summary,
        )
    _print(report)
    return 0


def _verify(args: argparse.Namespace) -> int:
    archive = args.archive
    if archive is None and DEFAULT_ARCHIVE_PATH.is_file():
        archive = DEFAULT_ARCHIVE_PATH
    report = DatasetService().verify_snapshot(
        args.source,
        archive_path=archive,
        manifest_path=args.manifest,
    )
    _print(report)
    return 0 if report["passed"] else 1


def _convert(args: argparse.Namespace) -> int:
    report = DatasetConversionService().convert(
        args.source,
        args.output,
        contract_path=args.contract,
        source_manifest_path=args.manifest,
    )
    _print(report)
    return 0


def _quality(args: argparse.Namespace) -> int:
    service = DatasetQualityService()
    report = service.analyze(
        args.source,
        dataset_id=args.dataset_id,
        mapping_version=args.mapping_version,
    )
    if not report["dataset_hash"]["unchanged"]:
        _print(
            {
                "dataset_hash_before": report["dataset_hash_before"],
                "dataset_hash_after": report["dataset_hash_after"],
                "unchanged": False,
                "reports_written": False,
            }
        )
        return 1
    json_path, markdown_path = service.write_reports(
        report,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
    )
    _print(
        {
            "dataset_id": report["dataset"]["dataset_id"],
            "dataset_hash_before": report["dataset_hash_before"],
            "dataset_hash_after": report["dataset_hash_after"],
            "unchanged": True,
            "structure_status": report["structure_status"],
            "risk_flags": len(report["risk_flags"]),
            "json_report": str(json_path),
            "markdown_report": str(markdown_path),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 1 immutable source snapshot and deterministic conversion "
            "tools, including observation-only P1D quality validation."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect and count an extracted official source tree.",
    )
    inspect_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    inspect_parser.set_defaults(handler=_inspect)

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Copy, extract, hash, and register a downloaded official ZIP.",
    )
    snapshot_inputs = snapshot_parser.add_mutually_exclusive_group()
    snapshot_inputs.add_argument("--archive", type=Path)
    snapshot_inputs.add_argument("--source-dir", type=Path)
    snapshot_parser.add_argument("--output", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    snapshot_parser.add_argument("--downloaded-at")
    snapshot_parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY_PATH,
    )
    snapshot_parser.set_defaults(handler=_snapshot)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify expected counts, pairing, manifest, and archive fidelity.",
    )
    verify_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    verify_parser.add_argument("--archive", type=Path)
    verify_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    verify_parser.set_defaults(handler=_verify)

    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert the frozen CSS source to deterministic YOLO labels.",
    )
    convert_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    convert_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    convert_parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
    )
    convert_parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_SOURCE_MANIFEST,
    )
    convert_parser.set_defaults(handler=_convert)

    quality_parser = subparsers.add_parser(
        "quality",
        help="Run observation-only quality validation on a processed dataset.",
    )
    quality_parser.add_argument("--source", type=Path, default=DEFAULT_OUTPUT_DIR)
    quality_parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_QUALITY_JSON_PATH,
    )
    quality_parser.add_argument(
        "--markdown-output",
        type=Path,
        default=DEFAULT_QUALITY_MARKDOWN_PATH,
    )
    quality_parser.add_argument(
        "--dataset-id",
        default="CSS-PPE-10-V1",
    )
    quality_parser.add_argument(
        "--mapping-version",
        default="PPE-MAPPING-V1",
    )
    quality_parser.set_defaults(handler=_quality)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, FileExistsError, NotADirectoryError, ValueError) as exc:
        parser.exit(2, f"{type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
