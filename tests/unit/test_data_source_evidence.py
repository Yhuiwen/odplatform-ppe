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
SNAPSHOT_DOC = (
    PROJECT_ROOT / "docs" / "dataset_snapshots" / "CSS_V27_YOLOV8.md"
)
CANDIDATE_EVALUATION = (
    PROJECT_ROOT / "docs" / "11_DATASET_CANDIDATE_EVALUATION.md"
)
FREEZE_DECISION = PROJECT_ROOT / "docs" / "12_DATASET_FREEZE_DECISION.md"


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
        "SNAPSHOT CREATED",
        "BLOCKED / NEEDS FREEZE CORRECTION",
        "P1B.1 Identity Audit",
        "CONFIRMED: export artifact mismatch",
        "Exact Roboflow internal reason: `UNKNOWN`",
        "Phase 1B Download Record",
        "Construction-Site-Safety-27",
        "2,799",
        "2,603",
        "5,601",
        "FAILED - EXPECTED COUNT OR CLASS MISMATCH",
        "RESOLVED FOR V1 SOURCE SELECTION",
    ]
    for fragment in required_fragments:
        assert fragment in content, fragment


def test_dataset_card_records_snapshot_and_validation_failure() -> None:
    content = _read(DATASET_CARD)
    required_fragments = [
        "Dataset ID | CSS-V1",
        "BLOCKED / NEEDS FREEZE CORRECTION",
        "Attribution 4.0 International (CC BY 4.0)",
        "Roboflow version 27",
        "2,801",
        "train 2,605 / valid 114 / test 82",
        "Actual Image Count | 2,799: train 2,603 / valid 114 / test 82",
        "Actual Export Classes | 10 classes",
        "Reported Annotation Count | UNVERIFIED / NOT FROZEN",
        "Source Annotation Task | Bounding-box object detection",
        "Selected Export | Ultralytics YOLO / `yolov8`",
        "Target Training Framework | YOLO11",
        "Downloaded | YES",
        "FAILED - EXPECTED COUNT OR CLASS MISMATCH",
        "CSS-V1.1 Candidate",
        "| Historical status | Candidate, not frozen |",
        "CSS-PPE-10-V1",
        "| Status | FROZEN |",
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


def test_adr_010_requires_complete_export_artifact_fingerprint() -> None:
    content = _read(ADR_DOC)
    assert "## ADR-010" in content
    assert "Dataset freeze requires export artifact fingerprint" in content
    for fragment in (
        "workspace",
        "project",
        "version",
        "export format",
        "`data.yaml` SHA256",
        "class list",
        "manifest SHA256",
        "actual split counts",
    ):
        assert fragment in content, fragment


def test_adr_011_records_v1_dataset_selection_criteria() -> None:
    content = _read(ADR_DOC)
    assert "## ADR-011" in content
    assert "V1 dataset selection criteria" in content
    for fragment in (
        "reproducibility",
        "verified artifact identity",
        "PPE task relevance",
        "license clarity",
        "training feasibility",
        "Maximum class count is not a selection criterion by itself",
    ):
        assert fragment in content, fragment


def test_adr_012_freezes_v1_by_artifact_fingerprint() -> None:
    content = _read(ADR_DOC)
    assert "## ADR-012" in content
    assert "V1 dataset is frozen by artifact fingerprint" in content
    for fragment in (
        "CSS-PPE-10-V1",
        "not only by a Roboflow version number",
        "roboflow-universe-projects",
        "construction-site-safety",
        "version `27`",
        "`yolov8`",
        "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34",
        "ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795",
        "train `2603` / valid `114` / test `82`",
        "total images `2799`",
    ):
        assert fragment in content, fragment


def test_final_dataset_freeze_decision_is_complete() -> None:
    content = _read(FREEZE_DECISION)
    required_fragments = [
        "Selected:",
        "CSS-PPE-10-V1",
        "Rejected candidates:",
        "CSS-V1",
        "Accepted candidate:",
        "CSS-V1.1 Candidate",
        "Artifact fingerprint:",
        "Dataset identity:",
        "Why selected:",
        "Why alternatives rejected:",
        "Training scope:",
        "P1C input:",
        "workspace: roboflow-universe-projects",
        "project: construction-site-safety",
        "version: 27",
        "format: yolov8",
        "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34",
        "ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795",
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
        "2799",
        "train `2603` / valid `114` / test `82`",
        "data/external/css-v27-yolov8/source/",
        "Phase 1C remains not started",
    ]
    for fragment in required_fragments:
        assert fragment in content, fragment


def test_frozen_dataset_identity_is_bound_to_artifact() -> None:
    content = _read(DATASET_CARD)
    assert "## CSS-PPE-10-V1 — Frozen V1 Dataset" in content
    assert "| Status | FROZEN |" in content
    assert "| Workspace | `roboflow-universe-projects` |" in content
    assert "| Project | `construction-site-safety` |" in content
    assert "| Version | `27` |" in content
    assert "| Export | `yolov8` |" in content
    assert (
        "| `data.yaml` SHA256 | "
        "`5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |"
        in content
    )
    assert (
        "| Manifest SHA256 | "
        "`ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |"
        in content
    )
    assert "| Actual images | `2799` |" in content
    assert "| Split counts | train `2603` / valid `114` / test `82` |" in content


def test_candidate_evaluation_compares_css_v1_and_css_v1_1() -> None:
    content = _read(CANDIDATE_EVALUATION)
    required_fragments = [
        "Candidate Comparison",
        "CSS-V1 |",
        "CSS-V1.1 Candidate |",
        "Roboflow Universe workspace",
        "version `27`",
        "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34",
        "ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795",
        "2,801 total",
        "2,799 total",
        "25 source classes",
        "10 exported classes",
        "Person",
        "Hardhat",
        "NO-Hardhat",
        "Safety Vest",
        "NO-Safety Vest",
        "BLOCKED / NEEDS FREEZE CORRECTION",
        "Candidate, not frozen",
        "P1C remains not started",
        "M-001 remains `待实现`",
    ]
    for fragment in required_fragments:
        assert fragment in content, fragment


def test_candidate_gate_history_and_current_conversion_status_are_consistent() -> None:
    evaluation = _read(CANDIDATE_EVALUATION)
    phase = _read(PHASE_DOC)
    status = _read(CURRENT_STATUS)
    assert "P1C remains not started" in evaluation
    assert "| P1C-2 | Dataset Conversion Implementation |" in phase
    assert (
        "| P1D | Deduplication & Quality Validation | "
        "已经实现 / QUALITY ASSESSED |"
    ) in phase
    assert "M-001 保持 `待实现`" in status


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


def test_phase_1a_is_complete_and_phase_1b_needs_freeze_correction() -> None:
    phase = _read(PHASE_DOC)
    assert "| P1A | Source & License Gate | 已经实现 |" in phase
    assert (
        "| P1B | Download & Raw Snapshot | 已经实现 / FROZEN |"
        in phase
    )
    assert "| P1C-2 | Dataset Conversion Implementation |" in phase
    assert "P1C-2 已生成未跟踪的 processed dataset" in phase

    status = _read(CURRENT_STATUS)
    assert "Phase 1 — Data Engineering" in status
    assert "Phase 1 实现中" in status
    assert "P1D-1 已完成真实数据集质量验证" in status
    assert "P1C-2 已从不可变 source 生成 7 类 processed" in status
    assert "P1E-1 — Baseline Training Preparation Review" in status
    assert "实现状态：COMPLETED / REVIEW PASS" in status
    assert "数据修改：NONE" in status
    assert "M-001 保持 `待实现`" in status
    assert "P1D" in status
    assert "P1B dataset freeze completed" in status

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
    assert "RISK-014" in content
    assert (
        "Generated augmentation may appear as perceptual near-duplicates"
        in content
    )
    assert "RISK-015" in content
    assert "Roboflow version metadata differs from materialized export artifact" in content


def test_css_v1_cannot_be_frozen_when_expected_differs_from_observed() -> None:
    content = _read(DATASET_CARD)
    assert "Expected metadata: 25 classes / 2,801 images" in content
    assert "Observed export: 10 classes / 2,799 images" in content
    assert "BLOCKED / NEEDS FREEZE CORRECTION" in content
    assert "| Historical status | Candidate, not frozen |" in content


def test_generated_snapshot_semantics_are_explicit() -> None:
    content = _read(DATASET_CARD)
    assert "FROZEN GENERATED DATASET VERSION" in content
    assert "RAW ORIGINAL CAPTURE DATASET" in content
    assert "unmodified third-party export snapshot" in content
    assert "must not trigger automatic" in content


def test_source_evidence_contains_no_machine_paths_or_credentials() -> None:
    content = _read(EVIDENCE_DOC) + _read(SNAPSHOT_DOC)
    forbidden_fragments = [
        "C:\\",
        "E:\\",
        "ROBOFLOW_API_KEY=",
        "api_key=",
        "AIza",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in content, fragment


def test_snapshot_summary_records_immutable_failed_validation() -> None:
    content = _read(SNAPSHOT_DOC)
    required_fragments = [
        "- Dataset ID: `CSS-V1`",
        "- Version: `27`",
        "- Format: `yolov8`",
        "- Dataset extracted directory: `Construction-Site-Safety-27`",
        "archive unavailable",
        "| train | 2603 | 2603 |",
        "| valid | 114 | 114 |",
        "| test | 82 | 82 |",
        "- Total images: 2799",
        "- Actual original class count: 10",
        "- Snapshot status: `IMMUTABLE`",
        "- Validation status: `FAILED - EXPECTED COUNT OR CLASS MISMATCH`",
    ]
    for fragment in required_fragments:
        assert fragment in content, fragment


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
