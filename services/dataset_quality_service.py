"""Observation-only P1D dataset quality validation framework."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from utils.dataset_utils import (
    IMAGE_EXTENSIONS,
    ManifestEntry,
    manifest_lines,
    sha256_file,
    sha256_lines,
)
from utils.quality_metrics import (
    BBoxRecord,
    DEFAULT_CLASS_NAMES,
    QualityThresholds,
    bbox_issue_codes,
    class_distribution,
    cross_split_duplicate_groups,
    dhash64,
    group_exact_duplicates,
    parse_yolo_values,
    perceptual_duplicate_analysis,
    small_object_summary,
)


SPLIT_NAMES = ("train", "valid", "test")
PAYLOAD_DIRECTORIES = tuple(
    f"{split}/{kind}"
    for split in SPLIT_NAMES
    for kind in ("images", "labels")
)
PAYLOAD_ROOT_FILES = ("data.yaml",)
REPORT_SCHEMA_VERSION = "p1d-quality-report-v1"
COORDINATE_ISSUE_CODES = frozenset(
    {
        "x_center_out_of_range",
        "y_center_out_of_range",
        "width_out_of_range",
        "height_out_of_range",
        "bbox_out_of_image_bounds",
    }
)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _class_names(data_yaml: Mapping[str, Any]) -> list[str]:
    raw_names = data_yaml.get("names")
    if isinstance(raw_names, Mapping):
        return [
            str(raw_names[key])
            for key in sorted(raw_names, key=lambda value: int(value))
        ]
    if isinstance(raw_names, (list, tuple)):
        return [str(name) for name in raw_names]
    raise ValueError("data.yaml 'names' must be a list or mapping")


def _files(directory: Path, suffixes: set[str]) -> tuple[Path, ...]:
    if not directory.is_dir():
        return ()
    return tuple(
        sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in suffixes
        )
    )


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _payload_files(root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for relative_file in PAYLOAD_ROOT_FILES:
        candidate = root / relative_file
        if candidate.is_file():
            paths.append(candidate)
    for relative_directory in PAYLOAD_DIRECTORIES:
        directory = root / relative_directory
        if directory.is_dir():
            paths.extend(path for path in directory.rglob("*") if path.is_file())
    return tuple(sorted(set(paths), key=lambda path: _relative(path, root)))


def _manifest_entries(
    root: Path,
    paths: Sequence[Path],
) -> tuple[ManifestEntry, ...]:
    return tuple(
        ManifestEntry(
            relative_path=_relative(path, root),
            file_size_bytes=path.stat().st_size,
            sha256=sha256_file(path),
        )
        for path in paths
    )


def _class_counts(
    distribution: Mapping[str, Mapping[str, int]],
    class_names: Sequence[str],
) -> dict[str, dict[str, object]]:
    total_boxes = sum(int(distribution["total"][name]) for name in class_names)
    output: dict[str, dict[str, object]] = {}
    for class_id, class_name in enumerate(class_names):
        train_boxes = int(distribution["train"][class_name])
        valid_boxes = int(distribution["valid"][class_name])
        test_boxes = int(distribution["test"][class_name])
        total = train_boxes + valid_boxes + test_boxes
        output[str(class_id)] = {
            "class_id": class_id,
            "class_name": class_name,
            "train_boxes": train_boxes,
            "valid_boxes": valid_boxes,
            "test_boxes": test_boxes,
            "total_boxes": total,
            "share_of_total_boxes": (
                total / total_boxes if total_boxes else 0.0
            ),
        }
    return output


def _risk_flag(
    code: str,
    severity: str,
    observed: object,
    recommendation: str,
) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "observed": observed,
        "recommendation": recommendation,
    }


def _render_group_lines(
    groups: Sequence[Mapping[str, object]],
    *,
    limit: int = 20,
) -> list[str]:
    lines: list[str] = []
    for group in groups[:limit]:
        raw_paths = group.get("paths", [])
        paths = (
            [str(path) for path in raw_paths]
            if isinstance(raw_paths, list)
            else []
        )
        splits = group.get("splits", [])
        split_text = (
            ", ".join(str(split) for split in splits)
            if isinstance(splits, list)
            else ""
        )
        lines.append(
            f"- `{group.get('count', len(paths))}` files across "
            f"`{split_text}`: "
            + ", ".join(f"`{path}`" for path in paths)
        )
    if len(groups) > limit:
        lines.append(
            "- Additional groups omitted here; see the JSON report."
        )
    return lines


class DatasetQualityService:
    """Collect deterministic quality observations without modifying payload."""

    def analyze(
        self,
        dataset_dir: str | Path,
        *,
        expected_classes: Sequence[str] = DEFAULT_CLASS_NAMES,
        thresholds: QualityThresholds = QualityThresholds(),
        dataset_id: str = "CSS-PPE-10-V1",
        mapping_version: str = "PPE-MAPPING-V1",
    ) -> dict[str, Any]:
        """Return a report object; this method never writes to disk."""

        root = Path(dataset_dir).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(root)

        before_files = _payload_files(root)
        before_entries = _manifest_entries(root, before_files)
        before_manifest_sha256 = sha256_lines(manifest_lines(before_entries))

        data_yaml_path = root / "data.yaml"
        data_yaml_exists = data_yaml_path.is_file()
        if data_yaml_exists:
            data_yaml = _load_yaml(data_yaml_path)
            classes = _class_names(data_yaml)
        else:
            data_yaml = {}
            classes = list(expected_classes)

        split_structure: dict[str, dict[str, object]] = {}
        label_issues: list[dict[str, object]] = []
        bbox_issues: list[dict[str, object]] = []
        empty_labels: list[str] = []
        empty_labels_by_split: Counter[str] = Counter()
        parsed_records: list[BBoxRecord] = []
        valid_records: list[BBoxRecord] = []
        missing_labels: list[str] = []
        orphan_labels: list[str] = []
        zero_byte_images: list[str] = []
        malformed_count = 0

        for split in SPLIT_NAMES:
            images_dir = root / split / "images"
            labels_dir = root / split / "labels"
            images = _files(images_dir, set(IMAGE_EXTENSIONS))
            labels = _files(labels_dir, {".txt"})
            images_by_stem = {path.stem: path for path in images}
            labels_by_stem = {path.stem: path for path in labels}

            split_missing = sorted(set(images_by_stem) - set(labels_by_stem))
            split_orphan = sorted(set(labels_by_stem) - set(images_by_stem))
            missing_labels.extend(
                _relative(images_by_stem[stem], root) for stem in split_missing
            )
            orphan_labels.extend(
                _relative(labels_by_stem[stem], root) for stem in split_orphan
            )

            split_zero_byte_images = sorted(
                _relative(path, root)
                for path in images
                if path.stat().st_size == 0
            )
            zero_byte_images.extend(split_zero_byte_images)

            for label_path in labels:
                raw_lines = label_path.read_text(encoding="utf-8").splitlines()
                populated_lines = [line for line in raw_lines if line.strip()]
                if not populated_lines:
                    empty_labels_by_split[split] += 1
                    empty_labels.append(_relative(label_path, root))
                    continue

                image_path = images_by_stem.get(label_path.stem)
                image_relative_path = (
                    _relative(image_path, root)
                    if image_path is not None
                    else ""
                )
                for line_number, raw_line in enumerate(raw_lines, start=1):
                    if not raw_line.strip():
                        continue
                    try:
                        class_id, x_center, y_center, width, height = (
                            parse_yolo_values(raw_line)
                        )
                    except ValueError as exc:
                        malformed_count += 1
                        bbox_issues.append(
                            {
                                "split": split,
                                "label": _relative(label_path, root),
                                "line": line_number,
                                "issues": ["malformed_yolo_line"],
                                "message": str(exc),
                            }
                        )
                        continue

                    issue_codes = bbox_issue_codes(
                        class_id,
                        x_center,
                        y_center,
                        width,
                        height,
                        class_count=len(classes),
                    )
                    if issue_codes:
                        bbox_issues.append(
                            {
                                "split": split,
                                "label": _relative(label_path, root),
                                "line": line_number,
                                "issues": list(issue_codes),
                                "class_id": class_id,
                                "bbox": [
                                    x_center,
                                    y_center,
                                    width,
                                    height,
                                ],
                            }
                        )
                    record = BBoxRecord(
                        split=split,
                        image_relative_path=image_relative_path,
                        label_relative_path=_relative(label_path, root),
                        line_number=line_number,
                        class_id=class_id,
                        x_center=x_center,
                        y_center=y_center,
                        width=width,
                        height=height,
                    )
                    parsed_records.append(record)
                    if not issue_codes:
                        valid_records.append(record)

            duplicate_image_stems = sorted(
                stem
                for stem, count in Counter(path.stem for path in images).items()
                if count > 1
            )
            duplicate_label_stems = sorted(
                stem
                for stem, count in Counter(path.stem for path in labels).items()
                if count > 1
            )
            if duplicate_image_stems or duplicate_label_stems:
                label_issues.append(
                    {
                        "split": split,
                        "issue": "duplicate_stems",
                        "images": duplicate_image_stems,
                        "labels": duplicate_label_stems,
                    }
                )

            split_structure[split] = {
                "images_dir_exists": images_dir.is_dir(),
                "labels_dir_exists": labels_dir.is_dir(),
                "images": len(images),
                "labels": len(labels),
                "missing_labels": [
                    _relative(images_by_stem[stem], root)
                    for stem in split_missing
                ],
                "orphan_labels": [
                    _relative(labels_by_stem[stem], root)
                    for stem in split_orphan
                ],
                "zero_byte_images": split_zero_byte_images,
                "empty_labels": int(empty_labels_by_split[split]),
                "counts_match": len(images) == len(labels),
            }

        image_hash_records = [
            (entry.relative_path, entry.sha256)
            for entry in before_entries
            if Path(entry.relative_path).suffix.lower() in IMAGE_EXTENSIONS
        ]
        label_hash_records = [
            (entry.relative_path, entry.sha256)
            for entry in before_entries
            if Path(entry.relative_path).suffix.lower() == ".txt"
        ]
        exact_image_groups = group_exact_duplicates(image_hash_records)
        exact_label_groups = group_exact_duplicates(label_hash_records)
        cross_split_exact_groups = cross_split_duplicate_groups(
            exact_image_groups
        )
        cross_split_hashes = {
            str(group["sha256"]) for group in cross_split_exact_groups
        }
        same_split_exact_groups = [
            group
            for group in exact_image_groups
            if str(group["sha256"]) not in cross_split_hashes
        ]

        dhash_records: list[tuple[str, int]] = []
        decoder_failures: list[dict[str, str]] = []
        for relative_path, _ in image_hash_records:
            try:
                dhash_records.append(
                    (relative_path, dhash64(root / relative_path))
                )
            except (OSError, ValueError) as exc:
                decoder_failures.append(
                    {
                        "path": relative_path,
                        "error_type": type(exc).__name__,
                    }
                )

        perceptual = perceptual_duplicate_analysis(
            dhash_records,
            hamming_distance_threshold=(
                thresholds.perceptual_hash_hamming_distance
            ),
        )
        perceptual["status"] = "EXECUTED"
        perceptual["decoder_failures"] = decoder_failures
        perceptual_cross_split_groups = [
            group
            for group in perceptual["groups"]
            if bool(group["cross_split"])
        ]

        after_files = _payload_files(root)
        after_entries = _manifest_entries(root, after_files)
        after_manifest_sha256 = sha256_lines(manifest_lines(after_entries))
        dataset_unchanged = before_entries == after_entries

        distribution = class_distribution(parsed_records, classes)
        class_counts = _class_counts(distribution, classes)
        total_images = sum(
            int(split_structure[split]["images"]) for split in SPLIT_NAMES
        )
        total_labels = sum(
            int(split_structure[split]["labels"]) for split in SPLIT_NAMES
        )
        total_box_count = sum(
            int(details["total_boxes"]) for details in class_counts.values()
        )
        ppe_names = set(expected_classes[:5])
        ppe_box_count = sum(
            int(details["total_boxes"])
            for details in class_counts.values()
            if details["class_name"] in ppe_names
        )

        issue_code_counts: Counter[str] = Counter(
            code
            for issue in bbox_issues
            for code in issue["issues"]
        )
        invalid_class_count = int(issue_code_counts["unknown_class_id"])
        invalid_coordinate_count = sum(
            any(code in COORDINATE_ISSUE_CODES for code in issue["issues"])
            for issue in bbox_issues
        )

        class_totals = [
            int(details["total_boxes"]) for details in class_counts.values()
        ]
        positive_class_totals = [count for count in class_totals if count > 0]
        imbalance_ratio = (
            max(positive_class_totals) / min(positive_class_totals)
            if len(positive_class_totals) > 1
            else None
        )
        small_objects = small_object_summary(
            valid_records,
            classes,
            thresholds,
        )
        high_small_object_classes = sorted(
            class_name
            for class_name, details in small_objects["classes"].items()
            if details["small_object_risk"] == "HIGH"
        )
        medium_small_object_classes = sorted(
            class_name
            for class_name, details in small_objects["classes"].items()
            if details["small_object_risk"] == "MEDIUM"
        )

        structure_ok = (
            data_yaml_exists
            and data_yaml.get("nc") == len(classes)
            and classes == list(expected_classes)
            and all(
                bool(split_structure[split]["images_dir_exists"])
                and bool(split_structure[split]["labels_dir_exists"])
                and bool(split_structure[split]["counts_match"])
                for split in SPLIT_NAMES
            )
            and not missing_labels
            and not orphan_labels
            and not label_issues
            and not zero_byte_images
        )

        empty_label_count = len(empty_labels)
        empty_label_ratio = (
            empty_label_count / total_labels if total_labels else 0.0
        )
        risk_flags: list[dict[str, object]] = []
        if not dataset_unchanged:
            risk_flags.append(
                _risk_flag(
                    "DATASET_PAYLOAD_HASH_CHANGED",
                    "HIGH",
                    {
                        "before": before_manifest_sha256,
                        "after": after_manifest_sha256,
                    },
                    "Stop and investigate validator or filesystem behavior.",
                )
            )
        if not structure_ok:
            risk_flags.append(
                _risk_flag(
                    "STRUCTURE_OR_PAIRING_ISSUES",
                    "HIGH",
                    {
                        "missing_labels": len(missing_labels),
                        "orphan_labels": len(orphan_labels),
                        "structure_issue_groups": len(label_issues),
                        "zero_byte_images": len(zero_byte_images),
                    },
                    "Review structure and pairing evidence before training.",
                )
            )
        if bbox_issues:
            risk_flags.append(
                _risk_flag(
                    "INVALID_BOUNDING_BOXES",
                    "HIGH",
                    len(bbox_issues),
                    "Review invalid labels and define a new dataset version "
                    "before any correction.",
                )
            )
        if exact_image_groups:
            risk_flags.append(
                _risk_flag(
                    "EXACT_IMAGE_DUPLICATES_OBSERVED",
                    "MEDIUM",
                    {
                        "group_count": len(exact_image_groups),
                        "same_split_groups": len(same_split_exact_groups),
                        "cross_split_groups": len(cross_split_exact_groups),
                    },
                    "Review duplicate groups and generated augmentation context.",
                )
            )
        if cross_split_exact_groups:
            risk_flags.append(
                _risk_flag(
                    "EXACT_SPLIT_LEAKAGE",
                    "HIGH",
                    len(cross_split_exact_groups),
                    "Resolve leakage through an approved new dataset version; "
                    "do not edit the frozen payload in place.",
                )
            )
        if perceptual_cross_split_groups:
            risk_flags.append(
                _risk_flag(
                    "PERCEPTUAL_SPLIT_LEAKAGE_CANDIDATES",
                    "MEDIUM",
                    {
                        "pair_count": perceptual[
                            "cross_split_candidate_pair_count"
                        ],
                        "group_count": len(perceptual_cross_split_groups),
                    },
                    "Review perceptual candidates as risk evidence only; do "
                    "not auto-delete augmented images.",
                )
            )
        if decoder_failures:
            risk_flags.append(
                _risk_flag(
                    "IMAGE_DECODE_FAILURES",
                    "HIGH",
                    len(decoder_failures),
                    "Review undecodable image files and their source provenance.",
                )
            )
        if high_small_object_classes:
            risk_flags.append(
                _risk_flag(
                    "HIGH_SMALL_OBJECT_RISK",
                    "MEDIUM",
                    high_small_object_classes,
                    "Plan class-aware validation and small-object evaluation.",
                )
            )
        elif medium_small_object_classes:
            risk_flags.append(
                _risk_flag(
                    "MEDIUM_SMALL_OBJECT_RISK",
                    "LOW",
                    medium_small_object_classes,
                    "Monitor small-object recall during training and evaluation.",
                )
            )
        if imbalance_ratio is not None:
            risk_flags.append(
                _risk_flag(
                    "CLASS_IMBALANCE_OBSERVED",
                    "MEDIUM",
                    {
                        "max_to_min_ratio": imbalance_ratio,
                        "class_totals": {
                            str(details["class_id"]): int(
                                details["total_boxes"]
                            )
                            for details in class_counts.values()
                        },
                    },
                    "Use per-class metrics and evaluate class-aware training "
                    "strategies in later approved phases.",
                )
            )
        if empty_label_count:
            risk_flags.append(
                _risk_flag(
                    "EMPTY_LABELS_OBSERVED",
                    "INFO",
                    {
                        "count": empty_label_count,
                        "ratio": empty_label_ratio,
                    },
                    "Retain as valid images without target objects; do not "
                    "delete solely for being empty.",
                )
            )

        severity_counts = Counter(
            str(flag["severity"]) for flag in risk_flags
        )
        bounding_boxes = {
            "total_lines": len(parsed_records) + malformed_count,
            "valid_count": len(valid_records),
            "invalid_count": len(bbox_issues),
            "invalid_bbox_count": len(bbox_issues),
            "invalid_class_count": invalid_class_count,
            "invalid_coordinate_count": int(invalid_coordinate_count),
            "malformed_line_count": malformed_count,
            "issue_code_counts": dict(sorted(issue_code_counts.items())),
            "issues": bbox_issues,
        }
        duplicates = {
            "exact_images": {
                "duplicate_groups": exact_image_groups,
                "duplicate_group_count": len(exact_image_groups),
                "duplicate_file_count": sum(
                    int(group["count"]) - 1 for group in exact_image_groups
                ),
                "same_split_group_count": len(same_split_exact_groups),
                "cross_split_group_count": len(cross_split_exact_groups),
            },
            "exact_labels": {
                "duplicate_groups": exact_label_groups,
                "duplicate_group_count": len(exact_label_groups),
                "duplicate_file_count": sum(
                    int(group["count"]) - 1 for group in exact_label_groups
                ),
            },
            "perceptual": perceptual,
        }
        leakage = {
            "cross_split_exact_image_groups": cross_split_exact_groups,
            "exact_group_count": len(cross_split_exact_groups),
            "group_count": len(cross_split_exact_groups),
            "perceptual_cross_split_groups": perceptual_cross_split_groups,
            "perceptual_group_count": len(perceptual_cross_split_groups),
            "perceptual_candidate_pair_count": int(
                perceptual["cross_split_candidate_pair_count"]
            ),
            "exact_detected": bool(cross_split_exact_groups),
            "perceptual_detected": bool(perceptual_cross_split_groups),
            "detected": bool(
                cross_split_exact_groups or perceptual_cross_split_groups
            ),
        }

        nc = data_yaml.get("nc")
        return {
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "dataset": {
                "dataset_id": dataset_id,
                "mapping_version": mapping_version,
                "directory_name": root.name,
                "observation_only": True,
                "payload_scope": [
                    *PAYLOAD_ROOT_FILES,
                    *PAYLOAD_DIRECTORIES,
                ],
                "data_yaml_loaded": data_yaml_exists,
                "expected_classes": list(expected_classes),
                "actual_classes": classes,
                "class_count": len(classes),
                "nc": nc,
                "nc_matches_class_list": nc == len(classes),
                "classes_match_expected": classes == list(expected_classes),
                "image_count": total_images,
                "label_count": total_labels,
                "box_count": total_box_count,
            },
            "thresholds": thresholds.as_dict(),
            "structure": {
                "status": "PASS" if structure_ok else "FAIL",
                "data_yaml_exists": data_yaml_exists,
                "splits": split_structure,
                "missing_label_count": len(missing_labels),
                "orphan_label_count": len(orphan_labels),
                "zero_byte_image_count": len(zero_byte_images),
                "duplicate_stem_issue_count": len(label_issues),
            },
            "structure_status": "PASS" if structure_ok else "FAIL",
            "class_distribution": distribution,
            "class_counts": class_counts,
            "class_statistics": {
                "image_counts": {
                    split: int(split_structure[split]["images"])
                    for split in SPLIT_NAMES
                },
                "box_counts": {
                    split: sum(
                        int(distribution[split][class_name])
                        for class_name in classes
                    )
                    for split in SPLIT_NAMES
                },
                "class_count": len(classes),
                "max_to_min_ratio": imbalance_ratio,
                "zero_box_classes": sorted(
                    class_name
                    for class_name, details in class_counts.items()
                    if int(details["total_boxes"]) == 0
                ),
                "ppe_box_count": ppe_box_count,
                "ppe_share_of_total_boxes": (
                    ppe_box_count / total_box_count if total_box_count else 0.0
                ),
            },
            "empty_labels": {
                "label_file_count": total_labels,
                "count": empty_label_count,
                "ratio": empty_label_ratio,
                "by_split": {
                    split: int(empty_labels_by_split[split])
                    for split in SPLIT_NAMES
                },
                "paths": sorted(empty_labels),
                "interpretation": "image_without_object",
            },
            "bounding_boxes": bounding_boxes,
            "bbox_stats": bounding_boxes,
            "small_objects": small_objects,
            "duplicates": duplicates,
            "duplicate_stats": duplicates,
            "leakage": leakage,
            "label_consistency": {
                "missing_labels": sorted(missing_labels),
                "orphan_labels": sorted(orphan_labels),
                "structure_issues": label_issues,
                "unknown_class_issues": invalid_class_count,
                "consistent": not (
                    missing_labels
                    or orphan_labels
                    or label_issues
                    or invalid_class_count
                    or bbox_issues
                ),
            },
            "dataset_hash": {
                "scope": "payload_only",
                "before": before_manifest_sha256,
                "after": after_manifest_sha256,
                "unchanged": dataset_unchanged,
                "payload_file_count": len(after_files),
            },
            "dataset_hash_before": before_manifest_sha256,
            "dataset_hash_after": after_manifest_sha256,
            "risk_flags": risk_flags,
            "risk_summary": {
                "flag_count": len(risk_flags),
                "severity_counts": dict(sorted(severity_counts.items())),
            },
        }

    def write_json_report(
        self,
        report: Mapping[str, Any],
        output_path: str | Path,
    ) -> Path:
        """Write the machine-readable report without touching payload files."""

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return output

    def render_markdown_report(self, report: Mapping[str, Any]) -> str:
        """Render the required P1D-1 Markdown report from validated data."""

        dataset = report["dataset"]
        structure = report["structure"]
        class_counts = report["class_counts"]
        class_statistics = report["class_statistics"]
        empty_labels = report["empty_labels"]
        bbox_stats = report["bbox_stats"]
        small_objects = report["small_objects"]
        duplicates = report["duplicate_stats"]
        leakage = report["leakage"]
        risk_flags = report["risk_flags"]
        dataset_hash = report["dataset_hash"]

        lines = [
            "# Dataset Quality Report",
            "",
            "> Status: QUALITY ASSESSED / PAYLOAD IMMUTABLE",
            "",
            "## 1 Dataset Identity",
            "",
            f"- Dataset: `{dataset['dataset_id']}`",
            f"- Mapping: `{dataset['mapping_version']}`",
            f"- Processed directory: `{dataset['directory_name']}`",
            f"- Payload files: `{dataset_hash['payload_file_count']}`",
            "",
            "## 2 Validation Method",
            "",
            "Observation only. No image, label, `data.yaml`, or metadata "
            "payload file was repaired, rewritten, or deleted.",
            "",
            "Payload scope:",
            "",
            "```text",
            "data.yaml",
            "train/images + labels",
            "valid/images + labels",
            "test/images + labels",
            "```",
            "",
            f"- Payload hash before: `{dataset_hash['before']}`",
            f"- Payload hash after: `{dataset_hash['after']}`",
            f"- Hash unchanged: `{str(dataset_hash['unchanged']).upper()}`",
            "",
            "## 3 Dataset Structure",
            "",
            f"Structure status: `{structure['status']}`",
            "",
            "| Split | Images | Labels | Counts match | Empty labels |",
            "| --- | ---: | ---: | --- | ---: |",
        ]
        for split in SPLIT_NAMES:
            split_data = structure["splits"][split]
            lines.append(
                f"| {split} | {split_data['images']} | "
                f"{split_data['labels']} | "
                f"{str(split_data['counts_match']).upper()} | "
                f"{split_data['empty_labels']} |"
            )
        lines.extend(
            [
                "",
                f"Missing labels: `{structure['missing_label_count']}`",
                f"Orphan labels: `{structure['orphan_label_count']}`",
                f"Zero-byte images: `{structure['zero_byte_image_count']}`",
                "",
                "## 4 Class Distribution",
                "",
                "| ID | Class | Train boxes | Valid boxes | Test boxes | "
                "Total | Share |",
                "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for details in class_counts.values():
            lines.append(
                f"| {details['class_id']} | `{details['class_name']}` | "
                f"{details['train_boxes']} | {details['valid_boxes']} | "
                f"{details['test_boxes']} | {details['total_boxes']} | "
                f"{float(details['share_of_total_boxes']):.4f} |"
            )
        ratio = class_statistics["max_to_min_ratio"]
        lines.extend(
            [
                "",
                f"Total boxes: `{dataset['box_count']}`",
                "PPE five-class box count: "
                f"`{class_statistics['ppe_box_count']}` "
                f"(`{float(class_statistics['ppe_share_of_total_boxes']):.4f}` "
                "of all boxes)",
                "Maximum-to-minimum class ratio: "
                f"`{ratio if ratio is not None else 'N/A'}`",
                "",
                "## 5 Empty Labels",
                "",
                f"- Label files: `{empty_labels['label_file_count']}`",
                f"- Empty labels: `{empty_labels['count']}`",
                f"- Empty-label ratio: `{float(empty_labels['ratio']):.4f}`",
                "- Classification: image without object; retained in place.",
                "",
                "| Split | Empty labels |",
                "| --- | ---: |",
            ]
        )
        for split in SPLIT_NAMES:
            lines.append(
                f"| {split} | {empty_labels['by_split'][split]} |"
            )
        lines.extend(
            [
                "",
                "## 6 Bounding Box Quality",
                "",
                "| Metric | Count |",
                "| --- | ---: |",
                f"| Total label lines | {bbox_stats['total_lines']} |",
                f"| Valid bboxes | {bbox_stats['valid_count']} |",
                f"| Invalid bboxes | {bbox_stats['invalid_bbox_count']} |",
                f"| Invalid class IDs | {bbox_stats['invalid_class_count']} |",
                "| Invalid coordinates | "
                f"{bbox_stats['invalid_coordinate_count']} |",
                f"| Malformed lines | {bbox_stats['malformed_line_count']} |",
                "",
                "Issue-code counts:",
                "",
                "```json",
                json.dumps(
                    bbox_stats["issue_code_counts"],
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                "```",
                "",
                "## 7 Small Object Analysis",
                "",
                f"- Overall: small `{small_objects['small']}`, "
                f"medium `{small_objects['medium']}`, "
                f"large `{small_objects['large']}`",
                "- Thresholds: small `< 0.01`, medium `< 0.09`, "
                "large `>= 0.09`",
                "",
                "| Class | Total | Small | Small share | Risk |",
                "| --- | ---: | ---: | ---: | --- |",
            ]
        )
        for class_name in dataset["actual_classes"]:
            details = small_objects["classes"][class_name]
            lines.append(
                f"| `{class_name}` | {details['total']} | {details['small']} | "
                f"{float(details['small_share']):.4f} | "
                f"{details['small_object_risk']} |"
            )
        exact = duplicates["exact_images"]
        perceptual = duplicates["perceptual"]
        lines.extend(
            [
                "",
                "## 8 Duplicate Analysis",
                "",
                "Exact image duplicates:",
                "",
                f"- Groups: `{exact['duplicate_group_count']}`",
                f"- Same-split groups: `{exact['same_split_group_count']}`",
                f"- Cross-split groups: `{exact['cross_split_group_count']}`",
                "",
                "Perceptual dHash candidates:",
                "",
                f"- Algorithm: `{perceptual['algorithm']}`",
                f"- Hamming threshold: "
                f"`{perceptual['hamming_distance_threshold']}`",
                f"- Hashed images: `{perceptual['hashed_image_count']}`",
                f"- Candidate pairs: `{perceptual['candidate_pair_count']}`",
                "- Same-split candidate pairs: "
                f"`{perceptual['same_split_candidate_pair_count']}`",
                "- Cross-split candidate pairs: "
                f"`{perceptual['cross_split_candidate_pair_count']}`",
                f"- Candidate groups: `{perceptual['group_count']}`",
                f"- Decoder failures: "
                f"`{len(perceptual['decoder_failures'])}`",
                "- Mutation: `NOT ALLOWED`; candidates are risk evidence only.",
                "",
                "## 9 Leakage Analysis",
                "",
                f"- Exact cross-split leakage groups: "
                f"`{leakage['exact_group_count']}`",
                f"- Perceptual cross-split candidate groups: "
                f"`{leakage['perceptual_group_count']}`",
                f"- Perceptual cross-split candidate pairs: "
                f"`{leakage['perceptual_candidate_pair_count']}`",
                f"- Leakage detected: `{str(leakage['detected']).upper()}`",
                "",
            ]
        )
        if leakage["cross_split_exact_image_groups"]:
            lines.extend(
                _render_group_lines(
                    leakage["cross_split_exact_image_groups"]
                )
            )
        else:
            lines.append("No exact cross-split image groups were detected.")
        lines.append("")
        if leakage["perceptual_cross_split_groups"]:
            lines.extend(
                _render_group_lines(
                    leakage["perceptual_cross_split_groups"]
                )
            )
        else:
            lines.append(
                "No perceptual cross-split candidate groups were detected."
            )
        lines.extend(
            [
                "",
                "## 10 Risks",
                "",
            ]
        )
        if risk_flags:
            for flag in risk_flags:
                lines.append(
                    f"- `{flag['severity']}` `{flag['code']}`: "
                    f"{flag['recommendation']}"
                )
        else:
            lines.append("- No risk flags were produced.")
        lines.extend(
            [
                "",
                "## 11 Conclusion",
                "",
                "Quality assessed. The payload remained byte-identical before "
                "and after validation. No dataset cleaning, repair, deletion, "
                "relabeling, remapping, or resplitting was performed.",
                "",
                "Any data correction requires a new dataset version and a new "
                "frozen artifact fingerprint.",
                "",
            ]
        )
        return "\n".join(lines)

    def write_markdown_report(
        self,
        report: Mapping[str, Any],
        output_path: str | Path,
    ) -> Path:
        """Write the Markdown report without touching payload files."""

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            self.render_markdown_report(report),
            encoding="utf-8",
            newline="\n",
        )
        return output

    def write_reports(
        self,
        report: Mapping[str, Any],
        *,
        json_output_path: str | Path,
        markdown_output_path: str | Path,
    ) -> tuple[Path, Path]:
        """Write both reports after proving the payload hash is unchanged."""

        if not bool(report["dataset_hash"]["unchanged"]):
            raise ValueError(
                "Refusing to write reports because payload hash changed"
            )
        json_path = self.write_json_report(report, json_output_path)
        markdown_path = self.write_markdown_report(
            report,
            markdown_output_path,
        )
        return json_path, markdown_path
