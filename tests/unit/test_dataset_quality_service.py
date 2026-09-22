from io import BytesIO
import json
from pathlib import Path

from PIL import Image
import yaml

from services.dataset_quality_service import DatasetQualityService
from utils.dataset_utils import build_manifest
from utils.paths import PROJECT_ROOT


QUALITY_PLAN = PROJECT_ROOT / "docs" / "16_DATASET_QUALITY_PLAN.md"
QUALITY_REPORT = PROJECT_ROOT / "docs" / "17_DATASET_QUALITY_REPORT.md"
ADR_DOC = PROJECT_ROOT / "docs" / "03_TECHNICAL_DECISIONS.md"
RISK_DOC = PROJECT_ROOT / "docs" / "08_RISK_REGISTER.md"
PHASE_DOC = PROJECT_ROOT / "docs" / "phases" / "PHASE_01_DATA.md"
CURRENT_STATUS = PROJECT_ROOT / "docs" / "02_CURRENT_STATUS.md"

CLASS_NAMES = (
    "person",
    "hardhat",
    "no_hardhat",
    "vest",
    "no_vest",
    "machinery",
    "vehicle",
)


def _image_bytes(color: tuple[int, int, int]) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (24, 24), color=color).save(
        buffer,
        format="JPEG",
        quality=90,
    )
    return buffer.getvalue()


def _write_quality_fixture(tmp_path: Path, *, invalid_bbox: bool = False) -> Path:
    root = tmp_path / "quality-fixture"
    for split in ("train", "valid", "test"):
        (root / split / "images").mkdir(parents=True)
        (root / split / "labels").mkdir(parents=True)

    data_yaml = {
        "train": "../train/images",
        "val": "../valid/images",
        "test": "../test/images",
        "nc": len(CLASS_NAMES),
        "names": list(CLASS_NAMES),
    }
    (root / "data.yaml").write_text(
        yaml.safe_dump(data_yaml, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )

    shared_bytes = _image_bytes((120, 80, 40))
    (root / "train" / "images" / "shared.jpg").write_bytes(shared_bytes)
    (root / "valid" / "images" / "shared.jpg").write_bytes(shared_bytes)
    (root / "train" / "images" / "empty.jpg").write_bytes(
        _image_bytes((200, 200, 200))
    )
    (root / "test" / "images" / "unique.jpg").write_bytes(
        _image_bytes((10, 180, 40))
    )

    train_label = (
        "0 0.50 0.50 0.20 0.20\n"
        "1 0.25 0.25 0.02 0.02\n"
    )
    if invalid_bbox:
        train_label += "7 -0.10 0.50 1.20 0.00\n"
    (root / "train" / "labels" / "shared.txt").write_text(
        train_label,
        encoding="utf-8",
        newline="\n",
    )
    (root / "train" / "labels" / "empty.txt").write_text(
        "",
        encoding="utf-8",
        newline="\n",
    )
    (root / "valid" / "labels" / "shared.txt").write_text(
        "0 0.50 0.50 0.10 0.10\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "test" / "labels" / "unique.txt").write_text(
        "6 0.50 0.50 0.40 0.40\n",
        encoding="utf-8",
        newline="\n",
    )
    return root


def test_quality_plan_exists_with_required_sections() -> None:
    assert QUALITY_PLAN.is_file()
    content = QUALITY_PLAN.read_text(encoding="utf-8")
    for heading in (
        "# Dataset Quality Validation Plan",
        "## Dataset",
        "## Validation Principles",
        "## Q1 Structure",
        "## Q2 Class Distribution",
        "## Q3 Empty Labels",
        "## Q4 Bounding Boxes",
        "## Q5 Small Objects",
        "## Q6 Duplicates",
        "## Q7 Leakage",
        "## Q8 Label Consistency",
        "## Output Report Format",
        "## Forbidden Actions",
    ):
        assert heading in content, heading
    assert "Status: DESIGN FROZEN / EXECUTED BY P1D-1" in content
    assert "`small` | `area < 0.01`" in content
    assert "`medium` | `0.01 <= area < 0.09`" in content
    assert "No quality report is generated from the real dataset during P1D-0." in content


def test_p1d1_governance_state_records_real_validation_without_data_changes() -> None:
    phase = PHASE_DOC.read_text(encoding="utf-8")
    status = CURRENT_STATUS.read_text(encoding="utf-8")
    assert (
        "| P1D-0 | Dataset Quality Validation Design | "
        "已经实现 / DESIGN FROZEN |"
    ) in phase
    assert (
        "| P1D-1 | Real Dataset Quality Validation | "
        "已经实现 / PASS |"
    ) in phase
    assert (
        "| P1D | Deduplication & Quality Validation | "
        "已经实现 / QUALITY ASSESSED |"
    ) in phase
    assert "| P1D-0-G1 |" in phase
    assert "| P1D-0-G7 |" in phase
    assert "| G1D1-1 |" in phase
    assert "| G1D1-10 |" in phase
    assert "P1D-1 已完成真实数据集质量验证" in status
    assert "P1E-1 — Baseline Training Preparation Review" in status
    assert "实现状态：COMPLETED / REVIEW PASS" in status
    assert "数据修改：NONE" in status
    assert "M-001 保持 `待实现`" in status


def test_real_quality_report_records_required_p1d1_evidence() -> None:
    report = QUALITY_REPORT.read_text(encoding="utf-8")
    for fragment in (
        "# Dataset Quality Report",
        "Dataset: `CSS-PPE-10-V1`",
        "Mapping: `PPE-MAPPING-V1`",
        "bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b",
        "Structure status: `PASS`",
        "Total boxes: `30375`",
        "| Invalid bboxes | 0 |",
        "Exact cross-split leakage groups: `0`",
        "Perceptual cross-split candidate groups: `2`",
        "QUALITY ASSESSED / PAYLOAD IMMUTABLE",
        "Quality assessed.",
    ):
        assert fragment in report, fragment
    assert "dataset cleaned" not in report.lower()


def test_validator_does_not_modify_dataset(tmp_path: Path) -> None:
    root = _write_quality_fixture(tmp_path)
    before = build_manifest(root)
    DatasetQualityService().analyze(root)
    after = build_manifest(root)
    assert after == before


def test_bbox_validator_detects_invalid_fixture(tmp_path: Path) -> None:
    root = _write_quality_fixture(tmp_path, invalid_bbox=True)
    report = DatasetQualityService().analyze(root)
    bbox_report = report["bounding_boxes"]
    assert bbox_report["invalid_count"] == 1
    issue = bbox_report["issues"][0]
    assert issue["label"] == "train/labels/shared.txt"
    assert issue["line"] == 3
    assert set(issue["issues"]) == {
        "unknown_class_id",
        "x_center_out_of_range",
        "width_out_of_range",
        "height_out_of_range",
    }


def test_class_distribution_is_deterministic(tmp_path: Path) -> None:
    root = _write_quality_fixture(tmp_path)
    service = DatasetQualityService()
    first = service.analyze(root)["class_distribution"]
    second = service.analyze(root)["class_distribution"]
    assert first == second
    assert first["train"] == {
        "person": 1,
        "hardhat": 1,
        "no_hardhat": 0,
        "vest": 0,
        "no_vest": 0,
        "machinery": 0,
        "vehicle": 0,
    }
    assert first["valid"]["person"] == 1
    assert first["test"]["vehicle"] == 1
    assert first["total"] == {
        "person": 2,
        "hardhat": 1,
        "no_hardhat": 0,
        "vest": 0,
        "no_vest": 0,
        "machinery": 0,
        "vehicle": 1,
    }


def test_duplicate_detection_is_deterministic(tmp_path: Path) -> None:
    root = _write_quality_fixture(tmp_path)
    service = DatasetQualityService()
    first = service.analyze(root)["duplicates"]
    second = service.analyze(root)["duplicates"]
    assert first == second
    groups = first["exact_images"]["duplicate_groups"]
    assert len(groups) == 1
    assert groups[0]["paths"] == [
        "train/images/shared.jpg",
        "valid/images/shared.jpg",
    ]
    perceptual = first["perceptual"]
    assert perceptual["status"] == "EXECUTED"
    assert perceptual["decoder_failures"] == []
    assert perceptual["candidate_pair_count"] >= 1
    assert perceptual["cross_split_candidate_pair_count"] >= 1


def test_quality_analysis_does_not_change_dataset_hash(tmp_path: Path) -> None:
    root = _write_quality_fixture(tmp_path)
    before = build_manifest(root)
    report = DatasetQualityService().analyze(root)
    after = build_manifest(root)
    assert after == before
    assert report["dataset_hash"]["unchanged"] is True
    assert report["dataset_hash"]["before"] == report["dataset_hash"]["after"]


def test_quality_leakage_and_observation_only_governance_are_recorded(
    tmp_path: Path,
) -> None:
    root = _write_quality_fixture(tmp_path)
    report = DatasetQualityService().analyze(root)
    assert report["dataset"]["observation_only"] is True
    assert report["duplicates"]["perceptual"]["mutation_allowed"] is False
    assert report["leakage"]["detected"] is True
    assert report["leakage"]["group_count"] == 1
    assert report["leakage"]["cross_split_exact_image_groups"][0]["splits"] == [
        "train",
        "valid",
    ]
    assert report["leakage"]["perceptual_detected"] is True
    assert "## ADR-015" in ADR_DOC.read_text(encoding="utf-8")
    assert "RISK-017" in RISK_DOC.read_text(encoding="utf-8")


def test_quality_report_schema_and_markdown_are_valid(tmp_path: Path) -> None:
    root = _write_quality_fixture(tmp_path)
    service = DatasetQualityService()
    report = service.analyze(root)

    assert report["report_schema_version"] == "p1d-quality-report-v1"
    for key in (
        "dataset_hash_before",
        "dataset_hash_after",
        "class_counts",
        "bbox_stats",
        "duplicate_stats",
        "risk_flags",
    ):
        assert key in report
    assert report["dataset_hash_before"] == report["dataset_hash_after"]
    assert report["dataset_hash"]["scope"] == "payload_only"

    markdown = service.render_markdown_report(report)
    for heading in (
        "# Dataset Quality Report",
        "## 1 Dataset Identity",
        "## 2 Validation Method",
        "## 3 Dataset Structure",
        "## 4 Class Distribution",
        "## 5 Empty Labels",
        "## 6 Bounding Box Quality",
        "## 7 Small Object Analysis",
        "## 8 Duplicate Analysis",
        "## 9 Leakage Analysis",
        "## 10 Risks",
        "## 11 Conclusion",
    ):
        assert heading in markdown, heading
    assert "dataset cleaned" not in markdown.lower()

    json_path = tmp_path / "reports" / "quality_report.json"
    markdown_path = tmp_path / "reports" / "quality_report.md"
    service.write_reports(
        report,
        json_output_path=json_path,
        markdown_output_path=markdown_path,
    )
    assert json.loads(json_path.read_text(encoding="utf-8"))[
        "report_schema_version"
    ] == "p1d-quality-report-v1"
    assert markdown_path.read_text(encoding="utf-8") == markdown
