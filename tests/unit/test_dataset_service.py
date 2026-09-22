from pathlib import Path
import json
import shutil
import zipfile

from services.dataset_service import DatasetService
from utils.dataset_utils import write_manifest
from utils.paths import PROJECT_ROOT


FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "css_v27_mini"


def _zip_directory(source: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(candidate for candidate in source.rglob("*") if candidate.is_file()):
            bundle.write(path, path.relative_to(source).as_posix())


def test_inspect_source_reads_actual_classes_and_counts() -> None:
    report = DatasetService().inspect_source(FIXTURE_ROOT)

    assert report["source_file_verified"] is True
    assert report["class_count"] == 25
    assert report["required_five_semantics_present"] is True
    assert report["counts"]["total_images"] == 6
    assert report["counts"]["total_labels"] == 6
    assert report["data_yaml"]["nc"] == 25


def test_create_snapshot_writes_metadata_without_absolute_paths(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "css-v27-yolov8.zip"
    _zip_directory(FIXTURE_ROOT, archive)
    output = tmp_path / "snapshot"
    summary = tmp_path / "summary.md"

    report = DatasetService().create_snapshot(
        archive,
        output,
        downloaded_at="2026-09-21T00:00:00+00:00",
        summary_path=summary,
    )

    source_json = output / "metadata" / "source.json"
    counts_json = output / "metadata" / "counts.json"
    manifest = output / "metadata" / "checksums.sha256"
    assert source_json.is_file()
    assert counts_json.is_file()
    assert manifest.is_file()
    assert summary.is_file()

    source_payload = json.loads(source_json.read_text(encoding="utf-8"))
    assert source_payload["dataset_id"] == "CSS-V1"
    assert source_payload["version"] == 27
    assert source_payload["export_format"] == "yolov8"
    assert source_payload["archive_filename"] == "css-v27-yolov8.zip"
    assert source_payload["archive_size_bytes"] > 0
    assert len(source_payload["archive_sha256"]) == 64
    assert source_payload["source_data_yaml"]["nc"] == 25
    assert "api_key" not in source_json.read_text(encoding="utf-8").lower()
    assert str(tmp_path.resolve()) not in source_json.read_text(encoding="utf-8")
    assert str(tmp_path.resolve()) not in summary.read_text(encoding="utf-8")

    assert report["counts"]["total_images"] == 6
    assert report["counts"]["total_labels"] == 6
    assert report["manifest"]["file_count"] == 14


def test_create_snapshot_from_extracted_directory(tmp_path: Path) -> None:
    output = tmp_path / "snapshot"
    summary = tmp_path / "summary.md"

    report = DatasetService().create_snapshot_from_directory(
        FIXTURE_ROOT,
        output,
        downloaded_at="2026-09-21T00:00:00+00:00",
        summary_path=summary,
    )

    source_json = output / "metadata" / "source.json"
    source_payload = json.loads(source_json.read_text(encoding="utf-8"))
    assert source_payload["download_method"] == "Roboflow API"
    assert source_payload["secret_saved"] == "NO"
    assert source_payload["dataset_extracted_directory"] == "css_v27_mini"
    assert source_payload["original_class_count"] == 25
    assert source_payload["snapshot_status"] == "IMMUTABLE"
    assert source_payload["validation_status"].startswith("FAILED")
    assert "Archive: Downloaded via Roboflow API directly" in summary.read_text(
        encoding="utf-8"
    )
    assert str(tmp_path.resolve()) not in source_json.read_text(encoding="utf-8")
    assert str(tmp_path.resolve()) not in summary.read_text(encoding="utf-8")
    assert report["manifest"]["file_count"] == 14


def test_verify_snapshot_checks_manifest_and_archive(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(FIXTURE_ROOT, source)
    (source / "train" / "images" / "missing.jpg").unlink()
    (source / "train" / "labels" / "orphan.txt").unlink()

    archive = tmp_path / "clean.zip"
    _zip_directory(source, archive)
    extracted = tmp_path / "extracted"
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(extracted)
    manifest = tmp_path / "checksums.sha256"
    write_manifest(extracted, manifest)

    report = DatasetService().verify_snapshot(
        extracted,
        archive_path=archive,
        manifest_path=manifest,
        expected_counts={"train": 3, "valid": 1, "test": 1, "total": 5},
    )

    assert report["passed"] is True
    assert report["checks"]["source_matches_archive"] is True
    assert report["checks"]["manifest_matches"] is True


def test_verify_snapshot_reports_expected_count_differences() -> None:
    report = DatasetService().verify_snapshot(FIXTURE_ROOT)

    assert report["passed"] is False
    assert report["expected_count_differences"]["train"] == {
        "expected": 2605,
        "actual": 4,
        "difference": -2601,
    }
