import re
from pathlib import Path

import pytest

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
    must = _section(charter, r"2\. MUST 功能")
    must_rows = [row for row in _rows(must) if re.fullmatch(r"M-\d{3}", row[0])]
    expected_ids = {f"M-{index:03d}" for index in range(1, 27)}
    assert len(must_rows) == len(expected_ids), "MUST IDs must be unique"
    assert {row[0] for row in must_rows} == expected_ids
    for row in must_rows:
        assert len(row) == 4, f"Malformed MUST row: {row}"
        assert row[1] and row[2], f"Missing definition or acceptance criteria: {row}"
        assert row[3] in {"待实现", "实现中", "已经实现"}, f"Invalid MUST status: {row}"
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


def test_phase4_offline_scope_adjustment_is_documented() -> None:
    adr_log = (PROJECT_ROOT / "docs/03_TECHNICAL_DECISIONS.md").read_text(
        encoding="utf-8"
    )
    master_plan = (PROJECT_ROOT / "docs/01_MASTER_PLAN.md").read_text(
        encoding="utf-8"
    )
    phase = (
        PROJECT_ROOT / "docs/phases/PHASE_04_INFERENCE.md"
    ).read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## ADR-018" in adr_log
    assert "phase-4-offline-inference-complete" in adr_log
    assert "Camera/RTSP" in adr_log
    assert "M-008" in adr_log
    assert "Offline Inference COMPLETE" in master_plan
    assert "Offline Inference COMPLETE" in phase
    assert "Phase 4 — Offline Inference" in readme
    camera_status = next(
        line for line in readme.splitlines()
        if re.search(r"Camera\s*/\s*RTSP\s*[:：]", line, re.I)
    )
    assert re.search(r"deferred.*must", camera_status, re.I)
    assert re.search(r"M-008\s+PENDING", camera_status, re.I)


def _section(content: str, heading_pattern: str) -> str:
    """Read one Markdown section, including its nested subsections."""
    heading = re.search(rf"^(#+) +(?:{heading_pattern})[^\n]*$", content, re.M)
    assert heading, f"Missing section: {heading_pattern}"
    following = content[heading.end():]
    end = re.search(rf"^#{{1,{len(heading.group(1))}}} +", following, re.M)
    return following[:end.start()] if end else following


def _rows(content: str) -> list[list[str]]:
    return [
        [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        for line in content.splitlines() if line.lstrip().startswith("|")
    ]


def _extension_classifications(content: str) -> list[str]:
    """Recognize affirmative classifications, not mere word co-occurrence.

    This deliberately checks documented English/Chinese classification forms;
    it is not a general natural-language semantic parser.
    """
    subject = r"(?:M-00[78]|Camera\s*/\s*RTSP|annotated(?:\s+video)?\s+rendering)"
    relation = (
        r"(?:(?:(?:is|are)\s+)?(?:classified|defined)\s+as|[:：=]|is|are|remains?|"
        r"converted\s+to|被归类为|属于|归类为|定义为|降级为|转换为|延期为|是)"
    )
    pattern = re.compile(
        rf"{subject}\s*{relation}\s*(?:(?:a|an|deferred|optional)\s+)*"
        r"(?:as\s+)?Extensions?\b", re.I,
    )
    normalized = re.sub(r"[`*]", "", content)
    matches = [match.group() for match in pattern.finditer(normalized)]
    # A table classification cell is also authoritative without a linking verb.
    for row in _rows(normalized):
        if row and re.search(subject, row[0], re.I):
            if any(re.fullmatch(r"(?:deferred\s+)?extensions?", cell, re.I)
                   for cell in row[1:]):
                matches.append(" | ".join(row))
    return matches


@pytest.mark.parametrize("requirement", ["M-007", "M-008"])
def test_deferred_requirements_keep_charter_must_classification(requirement: str) -> None:
    charter = (PROJECT_ROOT / "docs/00_PROJECT_CHARTER.md").read_text(encoding="utf-8")
    must = _section(charter, r"2\. MUST 功能")
    extensions = _section(charter, r"3\. EXTENSION")
    rows = [row for row in _rows(must) if row[0] == requirement]
    assert len(rows) == 1, f"{requirement} must occur once in the MUST table"
    assert len(rows[0]) == 4
    assert rows[0][-1] == "待实现", f"Deferred requirement prematurely completed: {rows[0]}"
    assert not any(requirement in cell for row in _rows(extensions) for cell in row)
    assert not _extension_classifications(charter)


@pytest.mark.parametrize(
    ("requirement", "topic"),
    [("M-007", r"Annotated Video Rendering"), ("M-008", r"Camera\s*/\s*RTSP")],
)
def test_deferred_ownership_and_status_agree(requirement: str, topic: str) -> None:
    adr = (PROJECT_ROOT / "docs/03_TECHNICAL_DECISIONS.md").read_text(encoding="utf-8")
    decision = _section(adr, r"ADR-019\b")
    policy = _section(decision, topic)
    assert re.search(rf"{requirement}\s+remains\s+(?:a\s+)?V1\s+MUST", policy, re.I)
    assert re.search(r"deferred|延期", policy, re.I)
    owners = [row for row in _rows(decision) if row[0].startswith(requirement)]
    assert len(owners) == 1 and len(owners[0]) == 3
    assert re.search(r"Phase\s+7\b", owners[0][1])
    assert re.search(r"Phase\s+9\b", owners[0][2])
    status = (PROJECT_ROOT / "docs/02_CURRENT_STATUS.md").read_text(encoding="utf-8")
    ownership = _section(status, r"Deferred MUST ownership")
    item = re.search(rf"^- {requirement}\b[^\n]*(?:\n[ \t]+[^\n]+)*", ownership, re.M)
    assert item, f"Missing status ownership for {requirement}"
    assert re.search(r"Phase\s+7\b", item.group())
    assert re.search(r"Phase\s+9\b", item.group())
    assert re.search(
        rf"^- {requirement}\b[^\n]*?:\s*`待实现`(?=\s*[;；]|\s*$)",
        ownership,
        re.M,
    ), f"{requirement} must remain pending in its own status entry"
    assert re.search(r"Offline\s+Inference\s+COMPLETE", status)
    assert re.search(r"Phase\s+5\s+WAITING", status)


def test_governance_documents_do_not_downgrade_deferred_musts() -> None:
    paths = ["README.md", *REQUIRED_DOCS,
             *(f"docs/phases/{name}" for name in PHASE_DOCS)]
    for name in paths:
        content = (PROJECT_ROOT / name).read_text(encoding="utf-8")
        assert not _extension_classifications(content), name


@pytest.mark.parametrize("statement", [
    "M-008: Deferred Extension",
    "M-007 = Extension",
    "M-008 is an Extension.",
    "M-008 is classified as an Extension.",
    "M-007 is deferred as Extension work.",
    "M-007 被归类为 Extension",
    "Camera/RTSP：DEFERRED EXTENSION",
    "Annotated video rendering is an Extension.",
    "M-008 is\nan Extension.",
    "| M-007 | Extension | 待实现 |",
    "M-008 is not an Extension. M-007 is an Extension.",
])
def test_downgrade_detector_rejects_affirmative_classifications(statement: str) -> None:
    assert _extension_classifications(statement)


@pytest.mark.parametrize("statement", [
    "M-008 is NOT an Extension.",
    "M-007 remains a V1 MUST; it is not an Extension.",
    "M-008 不是 Extension。",
    "M-007 不得转换为 Extension。",
    "M-008 and annotated rendering remain MUST work. Neither is an Extension.",
    "M-008 is deferred. Extension E-001 is unrelated.",
    "ADR-019 corrects the prior Extension classification; M-008 remains MUST.",
])
def test_downgrade_detector_allows_negation_and_unrelated_mentions(statement: str) -> None:
    assert not _extension_classifications(statement)
