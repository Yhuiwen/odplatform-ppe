from pathlib import Path

from utils.paths import PROJECT_ROOT


EVIDENCE_DOC = PROJECT_ROOT / "docs" / "10_DATA_SOURCE_EVIDENCE.md"
DATASET_CARD = PROJECT_ROOT / "docs" / "06_DATASET_CARD.md"
PHASE_DOC = PROJECT_ROOT / "docs" / "phases" / "PHASE_01_DATA.md"
CURRENT_STATUS = PROJECT_ROOT / "docs" / "02_CURRENT_STATUS.md"
MASTER_PLAN = PROJECT_ROOT / "docs" / "01_MASTER_PLAN.md"
CHARTER = PROJECT_ROOT / "docs" / "00_PROJECT_CHARTER.md"
ADR_DOC = PROJECT_ROOT / "docs" / "03_TECHNICAL_DECISIONS.md"
RISK_DOC = PROJECT_ROOT / "docs" / "08_RISK_REGISTER.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_data_source_evidence_document_contains_required_evidence() -> None:
    content = _read(EVIDENCE_DOC)
    required_fragments = [
        "Source A: Roboflow Universe Original Project",
        "https://universe.roboflow.com/roboflow-universe-projects/"
        "construction-site-safety",
        "Version 27",
        "2,801 images",
        "2,605",
        "114",
        "82",
        "CC BY 4.0",
        "Dataset license evidence URL",
        "License legal terms URL",
        "The Roboflow Construction Site Safety project page directly states",
        "https://creativecommons.org/licenses/by/4.0/",
        "Person",
        "Hardhat",
        "NO-Hardhat",
        "Safety Vest",
        "NO-Safety Vest",
        "Source annotation task",
        "Selected export",
        "Target training framework",
        "yolov8",
        "UNVERIFIED / NOT FROZEN",
        "2023-01-10T14:21:19.209Z",
        "SOURCE VERIFIED",
        "NOT DOWNLOADED",
        "RESOLVED FOR V1 SOURCE SELECTION",
    ]
    for fragment in required_fragments:
        assert fragment in content, fragment


def test_dataset_card_keeps_dataset_not_downloaded() -> None:
    content = _read(DATASET_CARD)
    required_fragments = [
        "Dataset ID | CSS-V1",
        "SOURCE VERIFIED / NOT DOWNLOADED",
        "Attribution 4.0 International (CC BY 4.0)",
        "Roboflow version 27",
        "2,801",
        "train 2,605 / valid 114 / test 82",
        "Reported Annotation Count | UNVERIFIED / NOT FROZEN",
        "Source Annotation Task | Bounding-box object detection",
        "Selected Export | Ultralytics YOLO / `yolov8`",
        "Target Training Framework | YOLO11",
        "Downloaded | NO",
        "Local Dataset Hash | NOT AVAILABLE — NOT DOWNLOADED",
    ]
    for fragment in required_fragments:
        assert fragment in content, fragment


def test_adr_freezes_css_source_and_download_mechanism() -> None:
    content = _read(ADR_DOC)
    assert "## ADR-009" in content
    assert "CSS is the V1 primary dataset source" in content
    assert "roboflow-universe-projects/construction-site-safety" in content
    assert "version=27" in content
    assert "`yolov8`" in content
    assert "Annotation total" in content
    assert "UNVERIFIED / NOT FROZEN" in content
    assert "Kaggle" in content
    assert "RISK-013" in content


def test_annotation_count_is_not_frozen_without_direct_total_evidence() -> None:
    evidence = _read(EVIDENCE_DOC)
    dataset_card = _read(DATASET_CARD)
    assert "no direct single total-annotation-count field was found" in evidence
    assert "UNVERIFIED / NOT FROZEN" in evidence
    assert "UNVERIFIED / NOT FROZEN" in dataset_card
    assert "6,201" not in evidence
    assert "6,201" not in dataset_card


def test_license_evidence_is_separate_from_license_terms() -> None:
    for content in (_read(EVIDENCE_DOC), _read(DATASET_CARD), _read(ADR_DOC)):
        assert "Dataset license evidence" in content or "License basis" in content
        assert "https://universe.roboflow.com/roboflow-universe-projects/" \
            "construction-site-safety" in content
        assert "https://creativecommons.org/licenses/by/4.0/" in content


def test_source_task_export_and_target_framework_are_distinct() -> None:
    evidence = _read(EVIDENCE_DOC)
    dataset_card = _read(DATASET_CARD)
    assert "Source annotation task | Bounding-box object detection" in evidence
    assert "Selected export | Ultralytics YOLO / `yolov8`" in evidence
    assert "Target training framework | YOLO11" in evidence
    assert "Source Annotation Task | Bounding-box object detection" in dataset_card
    assert "Selected Export | Ultralytics YOLO / `yolov8`" in dataset_card
    assert "Target Training Framework | YOLO11" in dataset_card


def test_phase_1a_is_complete_but_phase_1b_has_not_started() -> None:
    phase = _read(PHASE_DOC)
    assert "| P1A | Source & License Gate | 已经实现 |" in phase
    assert "| P1B | Download & Raw Snapshot | 待实现 |" in phase
    assert "尚未下载、转换或生成任何 processed dataset" in phase

    status = _read(CURRENT_STATUS)
    assert "Phase 1 — Data Engineering" in status
    assert "Phase 1 实现中" in status
    assert "P1A — Dataset Source & License Gate: COMPLETED" in status
    assert "P1B 尚未开始" in status
    assert "M-001 保持 `待实现`" in status

    master_plan = _read(MASTER_PLAN)
    assert "| P1 | Data | 数据获取、格式统一、质量检查、数据报告 | 实现中 |" in master_plan


def test_m001_remains_pending_in_charter() -> None:
    charter = _read(CHARTER)
    assert (
        "| M-001 | CSS 数据集下载、类别转换、Train/Val/Test 管理 | "
        "可复现地获取并转换 CSS；五类映射正确；训练、验证、测试清单可审计且"
        "无交叉泄漏 | 待实现 |"
    ) in charter


def test_provenance_risk_is_recorded() -> None:
    content = _read(RISK_DOC)
    assert "RISK-013" in content
    assert "Dataset license/source provenance ambiguity" in content


def test_source_evidence_contains_no_machine_paths_or_credentials() -> None:
    content = _read(EVIDENCE_DOC)
    forbidden_fragments = [
        "C:\\",
        "E:\\",
        "ROBOFLOW_API_KEY=",
        "api_key=",
        "AIza",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in content, fragment


def test_no_phase_1b_dataset_artifacts_exist() -> None:
    forbidden_suffixes = {".zip", ".tar", ".7z", ".pt", ".pth", ".db"}
    findings: list[str] = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(PROJECT_ROOT).parts
        if any(
            part in {".git", ".pytest_cache", "__pycache__"}
            for part in relative_parts
        ):
            continue
        if path.suffix.lower() in forbidden_suffixes:
            findings.append(path.relative_to(PROJECT_ROOT).as_posix())
    assert findings == []
