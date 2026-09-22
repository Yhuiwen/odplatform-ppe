"""Deterministic P1C conversion from the frozen CSS export to YOLO labels."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import yaml

from utils.dataset_utils import (
    IMAGE_EXTENSIONS,
    build_manifest,
    manifest_lines,
    sha256_file,
    sha256_lines,
    write_manifest,
)
from utils.paths import DATA_DIR, PROJECT_ROOT


SOURCE_DATASET_ID = "CSS-PPE-10-V1"
MAPPING_VERSION = "PPE-MAPPING-V1"
OUTPUT_DATASET_ID = "css-ppe-10-v1"
FROZEN_SOURCE_DATA_YAML_SHA256 = (
    "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34"
)
FROZEN_SOURCE_MANIFEST_SHA256 = (
    "ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795"
)
SPLIT_NAMES = ("train", "valid", "test")
DEFAULT_SOURCE_DIR = DATA_DIR / "external" / "css-v27-yolov8" / "source"
DEFAULT_SOURCE_MANIFEST = (
    DATA_DIR / "external" / "css-v27-yolov8" / "metadata" / "checksums.sha256"
)
DEFAULT_OUTPUT_DIR = DATA_DIR / "processed" / OUTPUT_DATASET_ID
DEFAULT_CONTRACT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "dataset_contracts"
    / "CSS-PPE-10-V1-MAPPING.yaml"
)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _integer_mapping(
    raw_mapping: object,
    *,
    field: str,
) -> dict[int, str]:
    if not isinstance(raw_mapping, Mapping) or not raw_mapping:
        raise ValueError(f"Contract field '{field}' must be a non-empty mapping")
    result: dict[int, str] = {}
    for raw_key, raw_value in raw_mapping.items():
        try:
            key = int(raw_key)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Contract field '{field}' has a non-integer key: {raw_key!r}"
            ) from exc
        if key < 0:
            raise ValueError(f"Contract field '{field}' contains a negative key")
        if not isinstance(raw_value, str) or not raw_value:
            raise ValueError(
                f"Contract field '{field}' has an invalid name for ID {key}"
            )
        result[key] = raw_value
    return dict(sorted(result.items()))


def _class_id_mapping(
    raw_mapping: object,
) -> dict[int, int]:
    if not isinstance(raw_mapping, Mapping) or not raw_mapping:
        raise ValueError("Contract field 'class_mapping' must not be empty")
    result: dict[int, int] = {}
    for raw_source_id, raw_target_id in raw_mapping.items():
        try:
            source_id = int(raw_source_id)
            target_id = int(raw_target_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("Contract class_mapping values must be integers") from exc
        if source_id < 0 or target_id < 0:
            raise ValueError("Contract class_mapping cannot contain negative IDs")
        result[source_id] = target_id
    return dict(sorted(result.items()))


def _class_names(data_yaml: Mapping[str, Any]) -> list[str]:
    raw_names = data_yaml.get("names")
    if isinstance(raw_names, Mapping):
        return [
            str(raw_names[key])
            for key in sorted(raw_names, key=lambda value: int(value))
        ]
    if isinstance(raw_names, (list, tuple)):
        return [str(value) for value in raw_names]
    raise ValueError("Source data.yaml 'names' must be a list or mapping")


def _load_contract(path: Path) -> dict[str, Any]:
    contract = _read_yaml(path)
    source_dataset = contract.get("source_dataset")
    mapping_version = contract.get("mapping_version")
    if not isinstance(source_dataset, Mapping):
        raise ValueError("Contract field 'source_dataset' must be a mapping")
    if not isinstance(mapping_version, Mapping):
        raise ValueError("Contract field 'mapping_version' must be a mapping")
    if source_dataset.get("id") != SOURCE_DATASET_ID:
        raise ValueError("Conversion contract source dataset ID is not frozen")
    if mapping_version.get("id") != MAPPING_VERSION:
        raise ValueError("Conversion contract mapping version is not frozen")

    source_classes = _integer_mapping(
        contract.get("source_classes"),
        field="source_classes",
    )
    target_classes = _integer_mapping(
        contract.get("target_classes"),
        field="target_classes",
    )
    discard_classes = _integer_mapping(
        contract.get("discard_classes"),
        field="discard_classes",
    )
    class_mapping = _class_id_mapping(contract.get("class_mapping"))

    if list(source_classes) != list(range(10)):
        raise ValueError("Contract source_classes must contain IDs 0 through 9")
    if list(target_classes) != list(range(7)):
        raise ValueError("Contract target_classes must contain IDs 0 through 6")
    if set(class_mapping) & set(discard_classes):
        raise ValueError("A source class cannot be both mapped and discarded")
    covered_ids = set(class_mapping) | set(discard_classes)
    if covered_ids != set(source_classes):
        missing = sorted(set(source_classes) - covered_ids)
        extra = sorted(covered_ids - set(source_classes))
        raise ValueError(
            f"Contract mapping coverage error; missing={missing}, extra={extra}"
        )
    unknown_targets = sorted(set(class_mapping.values()) - set(target_classes))
    if unknown_targets:
        raise ValueError(
            f"Contract maps to unknown target class IDs: {unknown_targets}"
        )
    if len(set(class_mapping.values())) != len(class_mapping):
        raise ValueError("Each target class must be produced by exactly one source ID")

    conversion_rules = contract.get("conversion_rules")
    if not isinstance(conversion_rules, list):
        raise ValueError("Contract field 'conversion_rules' must be a list")
    return {
        "source_dataset_id": SOURCE_DATASET_ID,
        "mapping_version": MAPPING_VERSION,
        "source_classes": source_classes,
        "target_classes": target_classes,
        "class_mapping": class_mapping,
        "discard_classes": discard_classes,
        "conversion_rules": [str(rule) for rule in conversion_rules],
    }


def _image_files(directory: Path) -> tuple[Path, ...]:
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    return tuple(
        sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
    )


def _label_files(directory: Path) -> tuple[Path, ...]:
    if not directory.is_dir():
        raise NotADirectoryError(directory)
    return tuple(
        sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() == ".txt"
        )
    )


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_data_yaml(path: Path, target_classes: Mapping[int, str]) -> None:
    lines = [
        "train: ../train/images",
        "val: ../valid/images",
        "test: ../test/images",
        f"nc: {len(target_classes)}",
        "names:",
    ]
    lines.extend(
        f"  {class_id}: {name}" for class_id, name in target_classes.items()
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _validate_source(
    source_dir: Path,
    contract: Mapping[str, Any],
    *,
    source_manifest_path: Path,
    expected_data_yaml_sha256: str | None,
    expected_manifest_sha256: str | None,
) -> dict[str, Any]:
    if not source_dir.is_dir():
        raise NotADirectoryError(source_dir)
    if not source_manifest_path.is_file():
        raise FileNotFoundError(source_manifest_path)

    data_yaml_path = source_dir / "data.yaml"
    data_yaml = _read_yaml(data_yaml_path)
    classes = _class_names(data_yaml)
    expected_classes = list(contract["source_classes"].values())
    if classes != expected_classes:
        raise ValueError(
            "Source class list does not match the frozen conversion contract"
        )
    declared_nc = data_yaml.get("nc")
    try:
        nc = int(declared_nc)
    except (TypeError, ValueError) as exc:
        raise ValueError("Source data.yaml 'nc' must be an integer") from exc
    if nc != len(classes):
        raise ValueError("Source data.yaml 'nc' does not match its class list")

    data_yaml_sha256 = sha256_file(data_yaml_path)
    if (
        expected_data_yaml_sha256 is not None
        and data_yaml_sha256 != expected_data_yaml_sha256
    ):
        raise ValueError(
            "Source data.yaml fingerprint does not match the frozen artifact"
        )

    manifest_entries = build_manifest(source_dir)
    manifest_sha256 = sha256_lines(manifest_lines(manifest_entries))
    if (
        expected_manifest_sha256 is not None
        and manifest_sha256 != expected_manifest_sha256
    ):
        raise ValueError(
            "Source manifest fingerprint does not match the frozen artifact"
        )
    recorded_manifest_sha256 = sha256_file(source_manifest_path)
    if (
        expected_manifest_sha256 is not None
        and recorded_manifest_sha256 != expected_manifest_sha256
    ):
        raise ValueError(
            "Recorded source manifest does not match the frozen artifact"
        )

    return {
        "classes": classes,
        "data_yaml_sha256": data_yaml_sha256,
        "manifest_entries": manifest_entries,
        "manifest_sha256": manifest_sha256,
        "recorded_manifest_sha256": recorded_manifest_sha256,
    }


def _convert_split(
    source_dir: Path,
    staged_output: Path,
    split: str,
    class_mapping: Mapping[int, int],
    discard_classes: Mapping[int, str],
    class_names: tuple[str, ...],
    *,
    source_manifest_hashes: Mapping[str, str],
) -> dict[str, Any]:
    source_images = _image_files(source_dir / split / "images")
    source_labels = _label_files(source_dir / split / "labels")
    image_stem_counts = Counter(path.stem for path in source_images)
    label_stem_counts = Counter(path.stem for path in source_labels)
    duplicate_image_stems = sorted(
        stem for stem, count in image_stem_counts.items() if count > 1
    )
    duplicate_label_stems = sorted(
        stem for stem, count in label_stem_counts.items() if count > 1
    )
    if duplicate_image_stems or duplicate_label_stems:
        raise ValueError(
            f"{split} contains duplicate image or label stems; "
            f"images={duplicate_image_stems}, labels={duplicate_label_stems}"
        )
    source_by_stem = {path.stem: path for path in source_images}
    labels_by_stem = {path.stem: path for path in source_labels}
    missing_labels = sorted(set(source_by_stem) - set(labels_by_stem))
    orphan_labels = sorted(set(labels_by_stem) - set(source_by_stem))
    if missing_labels or orphan_labels:
        raise ValueError(
            f"{split} image-label pairing error; "
            f"missing={missing_labels}, orphan={orphan_labels}"
        )

    output_images = staged_output / split / "images"
    output_labels = staged_output / split / "labels"
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    kept_boxes = 0
    source_boxes = 0
    discarded_by_class: Counter[str] = Counter()
    target_box_counts: Counter[str] = Counter()

    for source_image in source_images:
        source_label = labels_by_stem[source_image.stem]
        output_image = output_images / source_image.name
        output_label = output_labels / source_label.name

        shutil.copyfile(source_image, output_image)
        source_hash = source_manifest_hashes.get(
            source_image.relative_to(source_dir).as_posix()
        )
        if source_hash is None or sha256_file(output_image) != source_hash:
            raise RuntimeError(
                f"Image hash changed during copy: {source_image.name}"
            )

        converted_lines: list[str] = []
        for line_number, raw_line in enumerate(
            source_label.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            stripped = raw_line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) != 5:
                raise ValueError(
                    f"{source_label}: line {line_number} must contain 5 fields"
                )
            try:
                source_class_id = int(parts[0])
            except ValueError as exc:
                raise ValueError(
                    f"{source_label}: line {line_number} has an invalid class ID"
                ) from exc
            source_boxes += 1
            if source_class_id in class_mapping:
                target_class_id = class_mapping[source_class_id]
                target_name = class_names[target_class_id]
                converted_lines.append(
                    f"{target_class_id} {' '.join(parts[1:])}"
                )
                kept_boxes += 1
                target_box_counts[target_name] += 1
            elif source_class_id in discard_classes:
                discarded_by_class[discard_classes[source_class_id]] += 1
            else:
                raise ValueError(
                    f"{source_label}: line {line_number} contains unknown "
                    f"source class ID {source_class_id}"
                )

        output_label.write_text(
            "\n".join(converted_lines) + ("\n" if converted_lines else ""),
            encoding="utf-8",
            newline="\n",
        )

    return {
        "source_images": len(source_images),
        "processed_images": len(source_images),
        "source_labels": len(source_labels),
        "processed_labels": len(source_labels),
        "source_boxes": source_boxes,
        "kept_boxes": kept_boxes,
        "discarded_boxes": source_boxes - kept_boxes,
        "discard_statistics": {
            class_name: int(discarded_by_class[class_name])
            for class_name in discard_classes.values()
        },
        "target_box_counts": {
            class_name: int(target_box_counts[class_name])
            for class_name in class_names
        },
    }


class DatasetConversionService:
    """Convert the frozen source artifact without mutating the source."""

    def convert(
        self,
        source_dir: str | Path = DEFAULT_SOURCE_DIR,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
        *,
        contract_path: str | Path = DEFAULT_CONTRACT_PATH,
        source_manifest_path: str | Path = DEFAULT_SOURCE_MANIFEST,
        expected_source_data_yaml_sha256: str | None = (
            FROZEN_SOURCE_DATA_YAML_SHA256
        ),
        expected_source_manifest_sha256: str | None = (
            FROZEN_SOURCE_MANIFEST_SHA256
        ),
    ) -> dict[str, Any]:
        source = Path(source_dir).expanduser().resolve()
        output = Path(output_dir).expanduser().resolve()
        contract_file = Path(contract_path).expanduser().resolve()
        manifest_file = Path(source_manifest_path).expanduser().resolve()

        if source == output or source in output.parents or output in source.parents:
            raise ValueError("Source and processed output directories must not overlap")

        contract = _load_contract(contract_file)
        source_record = _validate_source(
            source,
            contract,
            source_manifest_path=manifest_file,
            expected_data_yaml_sha256=expected_source_data_yaml_sha256,
            expected_manifest_sha256=expected_source_manifest_sha256,
        )
        source_manifest_hashes = {
            entry.relative_path: entry.sha256
            for entry in source_record["manifest_entries"]
        }

        staging = output.parent / f".{output.name}.conversion-staging"
        backup = output.parent / f".{output.name}.conversion-backup"
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists():
            shutil.rmtree(backup)
        staging.mkdir(parents=True, exist_ok=False)

        try:
            split_statistics: dict[str, dict[str, Any]] = {}
            all_discard_statistics: Counter[str] = Counter()
            all_target_box_counts: Counter[str] = Counter()
            source_boxes = 0
            kept_boxes = 0
            classified_boxes = 0
            for split in SPLIT_NAMES:
                statistics = _convert_split(
                    source,
                    staging,
                    split,
                    contract["class_mapping"],
                    contract["discard_classes"],
                    tuple(contract["target_classes"].values()),
                    source_manifest_hashes=source_manifest_hashes,
                )
                split_statistics[split] = {
                    key: value
                    for key, value in statistics.items()
                    if key not in {"discard_statistics", "target_box_counts"}
                }
                all_discard_statistics.update(statistics["discard_statistics"])
                all_target_box_counts.update(statistics["target_box_counts"])
                source_boxes += int(statistics["source_boxes"])
                kept_boxes += int(statistics["kept_boxes"])
                classified_boxes += (
                    int(statistics["kept_boxes"])
                    + int(statistics["discarded_boxes"])
                )

            if classified_boxes != source_boxes or kept_boxes + sum(
                all_discard_statistics.values()
            ) != source_boxes:
                raise RuntimeError("Conversion box accounting is inconsistent")

            metadata_dir = staging / "metadata"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            target_classes = contract["target_classes"]
            _write_data_yaml(staging / "data.yaml", target_classes)

            class_mapping_record = {
                "mapping_version": MAPPING_VERSION,
                "source_dataset": SOURCE_DATASET_ID,
                "source_classes": {
                    str(key): value
                    for key, value in contract["source_classes"].items()
                },
                "target_classes": {
                    str(key): value for key, value in target_classes.items()
                },
                "class_mapping": {
                    str(key): value
                    for key, value in contract["class_mapping"].items()
                },
                "discard_classes": {
                    str(key): value
                    for key, value in contract["discard_classes"].items()
                },
            }
            counts_record = {
                "dataset_id": OUTPUT_DATASET_ID,
                "splits": {
                    split: {
                        "images": split_statistics[split]["processed_images"],
                        "labels": split_statistics[split]["processed_labels"],
                    }
                    for split in SPLIT_NAMES
                },
                "total_images": sum(
                    int(split_statistics[split]["processed_images"])
                    for split in SPLIT_NAMES
                ),
                "total_labels": sum(
                    int(split_statistics[split]["processed_labels"])
                    for split in SPLIT_NAMES
                ),
                "source_boxes": source_boxes,
                "kept_boxes": kept_boxes,
                "discarded_boxes": source_boxes - kept_boxes,
            }
            conversion_record = {
                "source_dataset": SOURCE_DATASET_ID,
                "output_dataset": OUTPUT_DATASET_ID,
                "mapping_version": MAPPING_VERSION,
                "source_data_yaml_sha256": source_record["data_yaml_sha256"],
                "source_manifest_sha256": source_record["manifest_sha256"],
                "target_classes": {
                    str(key): value for key, value in target_classes.items()
                },
                "split_statistics": split_statistics,
                "discard_statistics": {
                    name: int(all_discard_statistics[name])
                    for name in contract["discard_classes"].values()
                },
                "target_box_counts": {
                    name: int(all_target_box_counts[name])
                    for name in target_classes.values()
                },
                "unknown_class_ids": [],
                "conversion_rules": contract["conversion_rules"],
            }
            _write_json(metadata_dir / "class_mapping.json", class_mapping_record)
            _write_json(metadata_dir / "counts.json", counts_record)
            _write_json(metadata_dir / "conversion.json", conversion_record)
            processed_manifest = build_manifest(staging)
            write_manifest(
                staging,
                metadata_dir / "checksums.sha256",
                entries=processed_manifest,
            )

            if output.exists():
                output.rename(backup)
            staging.rename(output)
            if backup.exists():
                shutil.rmtree(backup)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            if backup.exists() and not output.exists():
                backup.rename(output)
            raise

        return {
            "source_dataset": SOURCE_DATASET_ID,
            "mapping_version": MAPPING_VERSION,
            "output_dataset": OUTPUT_DATASET_ID,
            "output_dir": output.name,
            "source_data_yaml_sha256": source_record["data_yaml_sha256"],
            "source_manifest_sha256": source_record["manifest_sha256"],
            "split_statistics": split_statistics,
            "discard_statistics": conversion_record["discard_statistics"],
            "target_box_counts": conversion_record["target_box_counts"],
            "unknown_class_ids": [],
        }
