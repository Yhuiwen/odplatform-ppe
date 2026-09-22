from collections import Counter
import json
from pathlib import Path

import pytest
import yaml

from services.dataset_conversion_service import (
    DatasetConversionService,
)
from utils.dataset_utils import (
    build_manifest,
    manifest_lines,
    sha256_file,
    sha256_lines,
    write_manifest,
)
from utils.paths import PROJECT_ROOT


SOURCE_CLASSES = (
    "Hardhat",
    "Mask",
    "NO-Hardhat",
    "NO-Mask",
    "NO-Safety Vest",
    "Person",
    "Safety Cone",
    "Safety Vest",
    "machinery",
    "vehicle",
)
TARGET_CLASSES = (
    "person",
    "hardhat",
    "no_hardhat",
    "vest",
    "no_vest",
    "machinery",
    "vehicle",
)
EXPECTED_MAPPING = {
    0: 1,
    2: 2,
    4: 4,
    5: 0,
    7: 3,
    8: 5,
    9: 6,
}
CONTRACT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "dataset_contracts"
    / "CSS-PPE-10-V1-MAPPING.yaml"
)


def _write_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    for split in ("train", "valid", "test"):
        (source / split / "images").mkdir(parents=True)
        (source / split / "labels").mkdir(parents=True)

    data_yaml = {
        "train": "../train/images",
        "val": "../valid/images",
        "test": "../test/images",
        "nc": len(SOURCE_CLASSES),
        "names": list(SOURCE_CLASSES),
    }
    (source / "data.yaml").write_text(
        yaml.safe_dump(data_yaml, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )

    fixtures = {
        "train": {
            "a.jpg": (
                "5 0.10 0.20 0.30 0.40\n"
                "0 0.11 0.21 0.31 0.41\n"
                "2 0.12 0.22 0.32 0.42\n"
                "4 0.13 0.23 0.33 0.43\n"
                "7 0.14 0.24 0.34 0.44\n"
                "8 0.15 0.25 0.35 0.45\n"
                "9 0.16 0.26 0.36 0.46\n"
                "1 0.17 0.27 0.37 0.47\n"
                "3 0.18 0.28 0.38 0.48\n"
                "6 0.19 0.29 0.39 0.49\n"
            ),
            "b.jpg": "5 0.50 0.50 0.10 0.10\n1 0.20 0.20 0.10 0.10\n",
        },
        "valid": {"c.jpg": "2 0.30 0.30 0.20 0.20\n"},
        "test": {"d.jpg": "6 0.40 0.40 0.20 0.20\n"},
    }
    for split, split_fixtures in fixtures.items():
        for filename, label_text in split_fixtures.items():
            image_path = source / split / "images" / filename
            image_path.write_bytes(f"synthetic-image:{split}:{filename}".encode())
            label_path = source / split / "labels" / f"{Path(filename).stem}.txt"
            label_path.write_text(label_text, encoding="utf-8", newline="\n")
    return source


def _convert(source: Path, output: Path) -> dict[str, object]:
    return DatasetConversionService().convert(
        source,
        output,
        contract_path=CONTRACT_PATH,
        source_manifest_path=source / "checksums.sha256",
        expected_source_data_yaml_sha256=None,
        expected_source_manifest_sha256=None,
    )


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        entry.relative_path: entry.sha256
        for entry in build_manifest(root)
    }


@pytest.fixture
def converted_dataset(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    source = _write_source(tmp_path)
    write_manifest(source, source / "checksums.sha256")
    output = tmp_path / "processed"
    report = _convert(source, output)
    return source, output, report


def test_class_mapping_is_deterministic(
    converted_dataset: tuple[Path, Path, dict[str, object]],
) -> None:
    _, output, _ = converted_dataset
    lines = (output / "train" / "labels" / "a.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    assert [int(line.split()[0]) for line in lines] == [
        EXPECTED_MAPPING[source_id]
        for source_id in (5, 0, 2, 4, 7, 8, 9)
    ]
    metadata = json.loads(
        (output / "metadata" / "class_mapping.json").read_text(encoding="utf-8")
    )
    assert metadata["mapping_version"] == "PPE-MAPPING-V1"
    assert {
        int(source_id): target_id
        for source_id, target_id in metadata["class_mapping"].items()
    } == EXPECTED_MAPPING


def test_unknown_source_class_id_is_an_error(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    (source / "train" / "labels" / "b.txt").write_text(
        "10 0.50 0.50 0.10 0.10\n",
        encoding="utf-8",
        newline="\n",
    )
    write_manifest(source, source / "checksums.sha256")
    with pytest.raises(ValueError, match="unknown source class ID 10"):
        _convert(source, tmp_path / "processed")


def test_discard_statistics_are_complete(
    converted_dataset: tuple[Path, Path, dict[str, object]],
) -> None:
    _, output, report = converted_dataset
    assert report["discard_statistics"] == {
        "Mask": 2,
        "NO-Mask": 1,
        "Safety Cone": 2,
    }
    metadata = json.loads(
        (output / "metadata" / "conversion.json").read_text(encoding="utf-8")
    )
    assert metadata["discard_statistics"] == report["discard_statistics"]
    assert metadata["split_statistics"]["train"]["source_boxes"] == 12
    assert metadata["split_statistics"]["train"]["kept_boxes"] == 8
    assert metadata["split_statistics"]["train"]["discarded_boxes"] == 4


def test_bounding_box_coordinates_are_unchanged(
    converted_dataset: tuple[Path, Path, dict[str, object]],
) -> None:
    source, output, _ = converted_dataset
    source_lines = (source / "train" / "labels" / "a.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    output_lines = (output / "train" / "labels" / "a.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    retained_source = [
        line for line in source_lines if int(line.split()[0]) in EXPECTED_MAPPING
    ]
    assert [
        line.split(maxsplit=1)[1] for line in output_lines
    ] == [
        line.split(maxsplit=1)[1] for line in retained_source
    ]


def test_image_hashes_are_unchanged(
    converted_dataset: tuple[Path, Path, dict[str, object]],
) -> None:
    source, output, _ = converted_dataset
    for split in ("train", "valid", "test"):
        for source_image in sorted((source / split / "images").iterdir()):
            output_image = output / split / "images" / source_image.name
            assert sha256_file(output_image) == sha256_file(source_image)


def test_processed_data_yaml_is_correct(
    converted_dataset: tuple[Path, Path, dict[str, object]],
) -> None:
    _, output, _ = converted_dataset
    data_yaml = yaml.safe_load(
        (output / "data.yaml").read_text(encoding="utf-8")
    )
    assert data_yaml == {
        "train": "../train/images",
        "val": "../valid/images",
        "test": "../test/images",
        "nc": 7,
        "names": {
            class_id: name for class_id, name in enumerate(TARGET_CLASSES)
        },
    }


def test_source_dataset_is_untouched(
    converted_dataset: tuple[Path, Path, dict[str, object]],
) -> None:
    source, _, _ = converted_dataset
    before = _tree_hashes(source)
    output = source.parent / "repeat"
    _convert(source, output)
    assert _tree_hashes(source) == before


def test_repeated_conversion_produces_identical_tree(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    write_manifest(source, source / "checksums.sha256")
    output = tmp_path / "processed"
    _convert(source, output)
    first = _tree_hashes(output)
    _convert(source, output)
    second = _tree_hashes(output)
    assert first == second


def test_converted_label_class_counts_match_metadata(
    converted_dataset: tuple[Path, Path, dict[str, object]],
) -> None:
    _, output, report = converted_dataset
    counts: Counter[int] = Counter()
    for label_path in (output / "train" / "labels").glob("*.txt"):
        for line in label_path.read_text(encoding="utf-8").splitlines():
            counts[int(line.split()[0])] += 1
    assert counts == Counter({0: 2, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})
    assert report["target_box_counts"]["person"] == 2
