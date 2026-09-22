"""Phase 1B dataset snapshot, inspection, and verification service."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import yaml

from utils.dataset_utils import (
    build_manifest,
    count_split_files,
    extract_archive_safely,
    manifest_lines,
    sha256_file,
    sha256_lines,
    validate_image_label_pairs,
    verify_manifest,
    verify_source_against_archive,
    write_manifest,
)


DATASET_ID = "CSS-V1"
DATASET_NAME = "Construction Site Safety"
WORKSPACE = "roboflow-universe-projects"
PROJECT = "construction-site-safety"
VERSION = 27
EXPORT_FORMAT = "yolov8"
SOURCE_URL = (
    "https://universe.roboflow.com/"
    "roboflow-universe-projects/construction-site-safety/dataset/27"
)
LICENSE = "CC BY 4.0"
EXPECTED_COUNTS = {
    "train": 2605,
    "valid": 114,
    "test": 82,
    "total": 2801,
}
REQUIRED_SOURCE_CLASSES = (
    "Person",
    "Hardhat",
    "NO-Hardhat",
    "Safety Vest",
    "NO-Safety Vest",
)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _class_names(data_yaml: Mapping[str, Any]) -> list[str]:
    raw_names = data_yaml.get("names", [])
    if isinstance(raw_names, Mapping):
        return [
            str(raw_names[key])
            for key in sorted(raw_names, key=lambda value: int(value))
        ]
    if isinstance(raw_names, list):
        return [str(value) for value in raw_names]
    if isinstance(raw_names, tuple):
        return [str(value) for value in raw_names]
    raise ValueError("data.yaml 'names' must be a list or mapping")


def _source_yaml_record(data_yaml: Mapping[str, Any]) -> dict[str, Any]:
    fields = ("path", "train", "val", "test", "nc", "names")
    record = {field: data_yaml[field] for field in fields if field in data_yaml}
    extra_fields = {
        str(key): value
        for key, value in data_yaml.items()
        if key not in fields
    }
    if extra_fields:
        record["other_fields"] = extra_fields
    return record


def _expected_count_differences(
    actual_counts: Mapping[str, Any],
    expected_counts: Mapping[str, int],
) -> dict[str, dict[str, int]]:
    actual_splits = actual_counts["splits"]
    assert isinstance(actual_splits, Mapping)
    actual_values = {
        **{
            split: int(actual_splits[split]["images"])
            for split in ("train", "valid", "test")
        },
        "total": int(actual_counts["total_images"]),
    }
    return {
        key: {
            "expected": int(expected),
            "actual": actual_values[key],
            "difference": actual_values[key] - int(expected),
        }
        for key, expected in expected_counts.items()
        if actual_values[key] != int(expected)
    }


class DatasetService:
    """Phase 1 facade for snapshots and deterministic dataset conversion."""

    def inspect_source(self, source_dir: str | Path) -> dict[str, Any]:
        """Inspect an extracted source tree without modifying it."""

        root = Path(source_dir).expanduser().resolve()
        data_yaml = _load_yaml(root / "data.yaml")
        classes = _class_names(data_yaml)
        entries = build_manifest(root)
        counts = count_split_files(root, entries=entries)
        pairing = validate_image_label_pairs(root)
        return {
            "dataset_id": DATASET_ID,
            "version": VERSION,
            "export_format": EXPORT_FORMAT,
            "source_file_verified": len(classes) == 25,
            "class_count": len(classes),
            "classes": classes,
            "required_five_semantics_present": all(
                name in classes for name in REQUIRED_SOURCE_CLASSES
            ),
            "data_yaml": _source_yaml_record(data_yaml),
            "counts": counts,
            "pair_integrity": pairing,
            "manifest_file_count": len(entries),
        }

    def create_snapshot(
        self,
        archive_path: str | Path,
        output_dir: str | Path,
        *,
        source_url: str = SOURCE_URL,
        downloaded_at: str | None = None,
        summary_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Copy, extract, hash, and register one frozen official export."""

        archive = Path(archive_path).expanduser().resolve()
        if not archive.is_file():
            raise FileNotFoundError(archive)
        if source_url != SOURCE_URL:
            raise ValueError(
                "Only the official Roboflow CSS version 27 source URL is allowed"
            )

        output = Path(output_dir).expanduser().resolve()
        archive_dir = output / "archive"
        source_dir = output / "source"
        metadata_dir = output / "metadata"
        if source_dir.exists() and any(source_dir.iterdir()):
            raise FileExistsError(
                f"Source snapshot already exists and is immutable: {source_dir}"
            )

        archive_dir.mkdir(parents=True, exist_ok=True)
        snapshot_archive = archive_dir / archive.name
        if archive != snapshot_archive:
            shutil.copy2(archive, snapshot_archive)

        extract_archive_safely(snapshot_archive, source_dir)
        if not (source_dir / "data.yaml").is_file():
            raise FileNotFoundError(
                "Extracted source does not contain data.yaml at its root"
            )

        archive_sha256 = sha256_file(snapshot_archive)
        archive_size = snapshot_archive.stat().st_size
        manifest_path = metadata_dir / "checksums.sha256"
        manifest = write_manifest(source_dir, manifest_path)
        counts = count_split_files(source_dir, entries=manifest)
        data_yaml = _load_yaml(source_dir / "data.yaml")
        classes = _class_names(data_yaml)
        timestamp = downloaded_at or datetime.now(timezone.utc).isoformat()

        source_record = {
            "dataset_id": DATASET_ID,
            "dataset": DATASET_NAME,
            "workspace": WORKSPACE,
            "project": PROJECT,
            "version": VERSION,
            "export_format": EXPORT_FORMAT,
            "source_url": source_url,
            "downloaded_at": timestamp,
            "archive_filename": snapshot_archive.name,
            "archive_size_bytes": archive_size,
            "archive_sha256": archive_sha256,
            "license": LICENSE,
            "source_data_yaml": _source_yaml_record(data_yaml),
            "source_data_yaml_sha256": sha256_file(source_dir / "data.yaml"),
            "original_class_count": len(classes),
            "original_class_names": classes,
        }
        _write_json(metadata_dir / "source.json", source_record)
        _write_json(metadata_dir / "counts.json", counts)

        summary: Path | None = None
        if summary_path is not None:
            summary = Path(summary_path).expanduser().resolve()
            self._write_snapshot_summary(
                summary,
                source_record=source_record,
                counts=counts,
                manifest_sha256=sha256_file(manifest_path),
            )

        return {
            "source_record": source_record,
            "counts": counts,
            "manifest": {
                "path": manifest_path.relative_to(output).as_posix(),
                "file_count": len(manifest),
                "sha256": sha256_file(manifest_path),
            },
            "summary_path": (
                summary.relative_to(Path.cwd()).as_posix()
                if summary is not None and summary.is_relative_to(Path.cwd())
                else None
            ),
        }

    def create_snapshot_from_directory(
        self,
        source_dir: str | Path,
        output_dir: str | Path,
        *,
        downloaded_at: str | None = None,
        summary_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Copy and register an already-extracted official Roboflow export."""

        source = Path(source_dir).expanduser().resolve()
        if not source.is_dir():
            raise NotADirectoryError(source)
        for required in ("train", "valid", "test", "data.yaml"):
            if not (source / required).exists():
                raise FileNotFoundError(source / required)

        output = Path(output_dir).expanduser().resolve()
        source_snapshot = output / "source"
        metadata_dir = output / "metadata"
        if source_snapshot.exists() and any(source_snapshot.iterdir()):
            raise FileExistsError(
                f"Source snapshot already exists and is immutable: {source_snapshot}"
            )

        source_manifest = build_manifest(source)
        output.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, source_snapshot, dirs_exist_ok=True)
        copied_manifest = build_manifest(source_snapshot)
        if source_manifest != copied_manifest:
            raise RuntimeError("Directory copy did not preserve source file hashes")

        manifest_path = metadata_dir / "checksums.sha256"
        manifest = write_manifest(
            source_snapshot,
            manifest_path,
            entries=copied_manifest,
        )
        manifest_sha256 = sha256_file(manifest_path)
        counts = count_split_files(source_snapshot, entries=manifest)
        data_yaml_path = source_snapshot / "data.yaml"
        data_yaml_sha256 = sha256_file(data_yaml_path)
        data_yaml = _load_yaml(data_yaml_path)
        classes = _class_names(data_yaml)
        timestamp = downloaded_at or datetime.now(timezone.utc).isoformat()
        differences = _expected_count_differences(counts, EXPECTED_COUNTS)
        validation_status = (
            "PASS"
            if not differences and len(classes) == 25
            else "FAILED - EXPECTED COUNT OR CLASS MISMATCH"
        )
        source_manifest_sha256 = sha256_lines(manifest_lines(source_manifest))

        source_record = {
            "dataset_id": DATASET_ID,
            "dataset": DATASET_NAME,
            "workspace": WORKSPACE,
            "project": PROJECT,
            "version": VERSION,
            "export_format": EXPORT_FORMAT,
            "format": EXPORT_FORMAT,
            "source_url": SOURCE_URL,
            "downloaded_at": timestamp,
            "download_method": "Roboflow API",
            "dataset_extracted_directory": source.name,
            "license": LICENSE,
            "secret_saved": "NO",
            "source_data_yaml": _source_yaml_record(data_yaml),
            "source_data_yaml_sha256": data_yaml_sha256,
            "original_class_count": len(classes),
            "original_class_names": classes,
            "source_directory_manifest_sha256": source_manifest_sha256,
            "snapshot_manifest_sha256": manifest_sha256,
            "snapshot_status": "IMMUTABLE",
            "validation_status": validation_status,
            "expected_counts": EXPECTED_COUNTS,
            "actual_counts": {
                "train": counts["splits"]["train"]["images"],
                "valid": counts["splits"]["valid"]["images"],
                "test": counts["splits"]["test"]["images"],
                "total": counts["total_images"],
            },
            "expected_count_differences": differences,
        }
        _write_json(metadata_dir / "source.json", source_record)
        _write_json(metadata_dir / "counts.json", counts)

        summary: Path | None = None
        if summary_path is not None:
            summary = Path(summary_path).expanduser().resolve()
            self._write_snapshot_summary(
                summary,
                source_record=source_record,
                counts=counts,
                manifest_sha256=manifest_sha256,
            )

        return {
            "source_record": source_record,
            "counts": counts,
            "manifest": {
                "path": manifest_path.relative_to(output).as_posix(),
                "file_count": len(manifest),
                "sha256": manifest_sha256,
            },
            "summary_path": (
                summary.relative_to(Path.cwd()).as_posix()
                if summary is not None and summary.is_relative_to(Path.cwd())
                else None
            ),
        }

    def verify_snapshot(
        self,
        source_dir: str | Path,
        *,
        archive_path: str | Path | None = None,
        manifest_path: str | Path | None = None,
        expected_counts: Mapping[str, int] | None = None,
    ) -> dict[str, Any]:
        """Verify file counts, pairing, data.yaml classes, and archive fidelity."""

        root = Path(source_dir).expanduser().resolve()
        manifest_root: Path | None = None
        if manifest_path is not None:
            manifest_root = Path(manifest_path).expanduser().resolve()
            if not manifest_root.is_file():
                raise FileNotFoundError(manifest_root)

        counts = count_split_files(root)
        pairing = validate_image_label_pairs(root)
        data_yaml = _load_yaml(root / "data.yaml")
        classes = _class_names(data_yaml)
        differences = _expected_count_differences(
            counts,
            EXPECTED_COUNTS if expected_counts is None else expected_counts,
        )
        manifest_report = (
            verify_manifest(root, manifest_root)
            if manifest_root is not None
            else None
        )
        archive_report = (
            verify_source_against_archive(archive_path, root)
            if archive_path is not None
            else None
        )

        checks = {
            "expected_counts": not differences,
            "image_label_pairing": not any(
                (
                    pairing["missing_labels"],
                    pairing["orphan_labels"],
                    pairing["duplicate_relative_paths"],
                )
            ),
            "data_yaml_present": bool(pairing["data_yaml_exists"]),
            "source_class_count_25": len(classes) == 25,
            "required_five_semantics_present": all(
                name in classes for name in REQUIRED_SOURCE_CLASSES
            ),
            "manifest_matches": (
                True
                if manifest_report is None
                else bool(manifest_report["passed"])
            ),
            "source_matches_archive": (
                True
                if archive_report is None
                else bool(archive_report["passed"])
            ),
        }
        return {
            "passed": all(checks.values()),
            "checks": checks,
            "expected_count_differences": differences,
            "counts": counts,
            "pair_integrity": pairing,
            "class_count": len(classes),
            "classes": classes,
            "required_five_semantics_present": all(
                name in classes for name in REQUIRED_SOURCE_CLASSES
            ),
            "manifest": manifest_report,
            "archive": archive_report,
        }

    def prepare(self) -> dict[str, Any]:
        """Delegate deterministic conversion to the P1C conversion service."""

        from services.dataset_conversion_service import DatasetConversionService

        return DatasetConversionService().convert()

    def validate(self) -> None:
        """Deep label, coordinate, and duplicate validation belongs to P1D."""

        raise NotImplementedError(
            "Deep dataset quality validation belongs to P1D "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )

    def _write_snapshot_summary(
        self,
        path: Path,
        *,
        source_record: Mapping[str, Any],
        counts: Mapping[str, Any],
        manifest_sha256: str,
    ) -> None:
        splits = counts["splits"]
        assert isinstance(splits, Mapping)
        classes = source_record["original_class_names"]
        assert isinstance(classes, list)

        lines = [
            "# CSS v27 YOLOv8 Source Snapshot",
            "",
            f"- Dataset ID: `{source_record['dataset_id']}`",
            f"- Dataset: {source_record['dataset']}",
            f"- Version: `{source_record['version']}`",
            f"- Format: `{source_record['export_format']}`",
            f"- Source URL: {source_record['source_url']}",
            f"- License: {source_record['license']}",
            f"- Download Date: `{source_record['downloaded_at']}`",
        ]
        if "dataset_extracted_directory" in source_record:
            lines.append(
                "- Dataset extracted directory: "
                f"`{source_record['dataset_extracted_directory']}`"
            )
        if "archive_sha256" in source_record:
            lines.extend(
                [
                    f"- Archive SHA-256: `{source_record['archive_sha256']}`",
                    f"- Archive Size: `{source_record['archive_size_bytes']}` bytes",
                ]
            )
        else:
            lines.append(
                "- Archive: Downloaded via Roboflow API directly; "
                "archive unavailable"
            )
        lines.extend(
            [
                f"- Source data.yaml SHA-256: "
                f"`{source_record.get('source_data_yaml_sha256', 'NOT AVAILABLE')}`",
                "",
                "## Actual Counts",
                "",
                "| Split | Images | Labels |",
                "| --- | ---: | ---: |",
            ]
        )
        for split in ("train", "valid", "test"):
            split_counts = splits[split]
            lines.append(
                f"| {split} | {split_counts['images']} | "
                f"{split_counts['labels']} |"
            )
        lines.extend(
            [
                "",
                f"- Total images: {counts['total_images']}",
                f"- Total labels: {counts['total_labels']}",
                "- Expected image counts: train 2605, valid 114, test 82, "
                "total 2801",
                f"- Expected count match: "
                f"`{'YES' if not source_record.get('expected_count_differences', {}) else 'NO'}`",
                "",
                "## Source Classes",
                "",
                f"- Expected original class count: 25",
                f"- Actual original class count: {len(classes)}",
                f"- Class count match: `{'YES' if len(classes) == 25 else 'NO'}`",
                f"- Original class names: {', '.join(classes)}",
                "",
                "## File Integrity",
                "",
                f"- Missing labels: {counts['missing_label_files']}",
                f"- Orphan labels: {counts['orphan_label_files']}",
                f"- Empty labels: {counts['empty_label_files']}",
                f"- Zero-byte images: {counts['zero_byte_images']}",
                f"- Exact duplicate files: {counts['exact_duplicate_files']}",
                f"- Manifest file SHA-256: `{manifest_sha256}`",
                "",
                f"- Snapshot status: `{source_record.get('snapshot_status', 'IMMUTABLE')}`",
                f"- Validation status: "
                f"`{source_record.get('validation_status', 'NOT RECORDED')}`",
                "",
                "The full source manifest remains in the Git-ignored external "
                "snapshot metadata directory.",
                "",
            ]
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
