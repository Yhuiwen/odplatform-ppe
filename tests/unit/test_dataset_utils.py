from hashlib import sha256
from pathlib import Path
import shutil
import zipfile

import pytest

from utils.dataset_utils import (
    build_manifest,
    count_split_files,
    extract_archive_safely,
    read_manifest,
    sha256_file,
    validate_image_label_pairs,
    verify_manifest,
    verify_source_against_archive,
    write_manifest,
)
from utils.paths import PROJECT_ROOT


FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "css_v27_mini"


def _zip_directory(source: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(candidate for candidate in source.rglob("*") if candidate.is_file()):
            bundle.write(path, path.relative_to(source).as_posix())


def test_sha256_file_matches_standard_library() -> None:
    path = FIXTURE_ROOT / "train" / "images" / "a.jpg"
    expected = sha256(path.read_bytes()).hexdigest()
    assert sha256_file(path) == expected


def test_manifest_is_deterministic_and_source_relative(tmp_path: Path) -> None:
    first = tmp_path / "first.sha256"
    second = tmp_path / "second.sha256"
    entries = write_manifest(FIXTURE_ROOT, first)
    write_manifest(FIXTURE_ROOT, second, entries=build_manifest(FIXTURE_ROOT))

    assert first.read_bytes() == second.read_bytes()
    assert tuple(entry.relative_path for entry in entries) == tuple(
        sorted(entry.relative_path for entry in entries)
    )
    assert all("\\" not in entry.relative_path for entry in entries)
    assert all(not entry.relative_path.startswith(FIXTURE_ROOT.drive) for entry in entries)
    assert read_manifest(first)[0].relative_path == entries[0].relative_path


def test_count_split_files_reports_expected_fixture_statistics() -> None:
    report = count_split_files(FIXTURE_ROOT)

    assert report["splits"] == {
        "train": {"images": 4, "labels": 4},
        "valid": {"images": 1, "labels": 1},
        "test": {"images": 1, "labels": 1},
    }
    assert report["total_images"] == 6
    assert report["total_labels"] == 6
    assert report["other_files"] == 2
    assert report["empty_label_files"] == 1
    assert report["missing_label_files"] == 1
    assert report["orphan_label_files"] == 1
    assert report["zero_byte_images"] == 0
    assert report["exact_duplicate_files"] == 1
    assert report["exact_duplicate_groups"] == [
        ["train/images/a.jpg", "train/images/duplicate.jpg"]
    ]


def test_pair_validation_reports_file_level_issues() -> None:
    report = validate_image_label_pairs(FIXTURE_ROOT)

    assert report["data_yaml_exists"] is True
    assert report["missing_labels"] == ["train/images/missing.jpg"]
    assert report["orphan_labels"] == ["train/labels/orphan.txt"]
    assert report["empty_labels"] == ["train/labels/b.txt"]
    assert report["zero_byte_images"] == []
    assert report["duplicate_relative_paths"] == []


def test_verify_manifest_detects_modified_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(FIXTURE_ROOT, source)
    manifest = tmp_path / "checksums.sha256"
    write_manifest(source, manifest)
    assert verify_manifest(source, manifest)["passed"] is True

    (source / "train" / "images" / "a.jpg").write_text(
        "changed",
        encoding="utf-8",
    )
    report = verify_manifest(source, manifest)
    assert report["passed"] is False
    assert report["hash_mismatches"] == ["train/images/a.jpg"]


def test_archive_round_trip_preserves_source_bytes(tmp_path: Path) -> None:
    archive = tmp_path / "source.zip"
    _zip_directory(FIXTURE_ROOT, archive)
    extracted = tmp_path / "extracted"
    extract_archive_safely(archive, extracted)

    assert verify_source_against_archive(archive, extracted)["passed"] is True
    (extracted / "data.yaml").write_text("changed: true\n", encoding="utf-8")
    report = verify_source_against_archive(archive, extracted)
    assert report["passed"] is False
    assert report["hash_mismatches"] == ["data.yaml"]


def test_archive_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../escape.txt", "unsafe")

    with pytest.raises(ValueError, match="Unsafe archive member"):
        extract_archive_safely(archive, tmp_path / "extracted")
