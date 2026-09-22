import re
from pathlib import Path

from utils.paths import PROJECT_ROOT


REQUIRED_DOCS = [
    "docs/00_PROJECT_CHARTER.md",
    "docs/01_MASTER_PLAN.md",
    "docs/02_CURRENT_STATUS.md",
    "docs/03_TECHNICAL_DECISIONS.md",
    "docs/04_CHANGELOG.md",
    "docs/05_TEST_GATES.md",
    "docs/06_DATASET_CARD.md",
    "docs/07_OPEN_SOURCE_USAGE.md",
    "docs/08_RISK_REGISTER.md",
    "docs/09_REFERENCE_ASSETS.md",
    "docs/10_DATA_SOURCE_EVIDENCE.md",
    "docs/16_DATASET_QUALITY_PLAN.md",
    "docs/17_DATASET_QUALITY_REPORT.md",
    "docs/18_TRAINING_STRATEGY.md",
]

PHASE_DOCS = [
    "PHASE_00_FOUNDATION.md",
    "PHASE_01_DATA.md",
    "PHASE_02_TRAINING.md",
    "PHASE_03_EVALUATION.md",
    "PHASE_04_INFERENCE.md",
    "PHASE_05_TRACKING_ASSOCIATION.md",
    "PHASE_06_COMPLIANCE_EVENTS.md",
    "PHASE_07_WEB_ALERTS.md",
    "PHASE_08_LLM_AGENT.md",
    "PHASE_09_INTEGRATION_DELIVERY.md",
]

PHASE_SECTIONS = [
    "## 1. 阶段目标",
    "## 2. 进入条件",
    "## 3. 当前子任务",
    "## 4. 实现设计",
    "## 5. 测试要求",
    "## 6. Gate",
    "## 7. 已知问题",
    "## 8. 开发记录",
]


def test_required_governance_documents_exist() -> None:
    for relative_path in REQUIRED_DOCS:
        assert (PROJECT_ROOT / relative_path).is_file(), relative_path


def test_all_phase_documents_have_required_sections() -> None:
    for filename in PHASE_DOCS:
        path = PROJECT_ROOT / "docs" / "phases" / filename
        assert path.is_file(), filename
        content = path.read_text(encoding="utf-8")
        for section in PHASE_SECTIONS:
            assert section in content, f"{filename} missing {section}"
        assert "【LOCKED】" in content


def test_charter_contains_all_locked_items_with_only_proven_status_changes() -> None:
    charter = (PROJECT_ROOT / "docs/00_PROJECT_CHARTER.md").read_text(
        encoding="utf-8"
    )
    for index in range(1, 27):
        item = f"M-{index:03d}"
        assert item in charter
    for index in range(1, 13):
        item = f"E-{index:03d}"
        assert item in charter
    assert charter.count("待实现") >= 37
    assert (
        "| M-004 | YOLO11n 至少完成一轮可复现训练 | "
        "固定配置、数据和随机种子后至少完成一轮训练；产出权重、日志、配置快照"
        "和复现实验命令 | 已经实现 |"
    ) in charter
    assert "PROJECT CHARTER — LOCKED TARGET DOCUMENT" in charter
    assert "MUST 功能" in charter
    assert "明确不属于 V1 MUST" in charter


def test_open_source_record_declares_no_copied_code() -> None:
    content = (PROJECT_ROOT / "docs/07_OPEN_SOURCE_USAGE.md").read_text(
        encoding="utf-8"
    )
    assert "Copied third-party business code: NO." in content
    assert "AGPL-3.0" in content
    assert "TO VERIFY" in content


def test_risk_register_contains_required_risks() -> None:
    content = (PROJECT_ROOT / "docs/08_RISK_REGISTER.md").read_text(
        encoding="utf-8"
    )
    for index in range(1, 11):
        assert f"RISK-{index:03d}" in content


def test_local_markdown_links_do_not_point_to_missing_files() -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    markdown_files = list(PROJECT_ROOT.rglob("*.md"))
    for markdown_file in markdown_files:
        content = markdown_file.read_text(encoding="utf-8")
        for target in link_pattern.findall(content):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_target = target.split("#", maxsplit=1)[0]
            resolved = (markdown_file.parent / local_target).resolve()
            assert resolved.exists(), f"{markdown_file}: broken link {target}"


def test_phase_zero_has_not_downloaded_unregistered_large_assets() -> None:
    expected_files = {
        "models/pretrained": {".gitkeep", "yolo11n.pt"},
    }
    for directory in (
        "data/external",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/samples",
        "models/pretrained",
        "models/checkpoints",
        "models/best",
        "models/exports",
    ):
        files = [
            path.name
            for path in (PROJECT_ROOT / directory).iterdir()
            if path.is_file()
        ]
        assert set(files) == expected_files.get(directory, {".gitkeep"}), directory
