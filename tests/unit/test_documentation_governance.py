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


def test_charter_contains_all_locked_must_items_as_pending() -> None:
    charter = (PROJECT_ROOT / "docs/00_PROJECT_CHARTER.md").read_text(
        encoding="utf-8"
    )
    for index in range(1, 27):
        item = f"M-{index:03d}"
        assert item in charter
    for index in range(1, 13):
        item = f"E-{index:03d}"
        assert item in charter
    assert charter.count("待实现") >= 38
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


def test_phase_zero_has_not_downloaded_large_assets() -> None:
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
        assert files == [".gitkeep"], directory
