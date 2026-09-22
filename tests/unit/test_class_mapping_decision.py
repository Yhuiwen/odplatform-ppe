from pathlib import Path
import json
import re

import pytest

from services.dataset_service import DatasetService
from utils.dataset_utils import sha256_file
from utils.paths import PROJECT_ROOT


DECISION_DOC = PROJECT_ROOT / "docs" / "14_CLASS_MAPPING_DECISION.md"
DESIGN_DOC = PROJECT_ROOT / "docs" / "13_CLASS_MAPPING_DESIGN.md"
DATASET_CARD = PROJECT_ROOT / "docs" / "06_DATASET_CARD.md"
ADR_DOC = PROJECT_ROOT / "docs" / "03_TECHNICAL_DECISIONS.md"
RISK_DOC = PROJECT_ROOT / "docs" / "08_RISK_REGISTER.md"
PHASE_DOC = PROJECT_ROOT / "docs" / "phases" / "PHASE_01_DATA.md"
CHARTER_DOC = PROJECT_ROOT / "docs" / "00_PROJECT_CHARTER.md"
SOURCE_DATA_YAML = (
    PROJECT_ROOT / "data" / "external" / "css-v27-yolov8" / "source" / "data.yaml"
)
SOURCE_METADATA = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "css-v27-yolov8"
    / "metadata"
    / "source.json"
)

FROZEN_DATA_YAML_SHA256 = (
    "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34"
)
EXPECTED_MAPPING = {
    0: ("person", (5,)),
    1: ("hardhat", (0,)),
    2: ("no_hardhat", (2,)),
    3: ("vest", (7,)),
    4: ("no_vest", (4,)),
    5: ("machinery", (8,)),
    6: ("vehicle", (9,)),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_final_training_classes(content: str) -> dict[int, tuple[str, tuple[int, ...]]]:
    pattern = re.compile(
        r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`\[([0-9,\s]+)\]`\s*\|$",
        re.MULTILINE,
    )
    mapping: dict[int, tuple[str, tuple[int, ...]]] = {}
    for match in pattern.finditer(content):
        new_id = int(match.group(1))
        name = match.group(2)
        source_ids = tuple(
            int(value.strip())
            for value in match.group(3).split(",")
            if value.strip()
        )
        mapping[new_id] = (name, source_ids)
    return mapping


def test_mapping_decision_document_exists_with_required_sections() -> None:
    assert DECISION_DOC.is_file()
    content = _read(DECISION_DOC)
    for heading in (
        "# Class Mapping Decision",
        "## Final Decision",
        "## Original Classes",
        "## Final Training Classes",
        "## Mapping Table",
        "## Discard Policy",
        "## Rationale",
        "## Impact Analysis",
    ):
        assert heading in content, heading
    assert "Strategy C" in content
    assert "Decision status: FROZEN" in content


def test_selected_class_ids_are_unique_and_exactly_frozen() -> None:
    mapping = _parse_final_training_classes(_read(DECISION_DOC))
    assert mapping == EXPECTED_MAPPING
    assert list(mapping) == list(range(7))
    source_ids = [source_id for _, ids in mapping.values() for source_id in ids]
    assert len(source_ids) == len(set(source_ids))


def test_discard_policy_is_explicit_and_complete() -> None:
    content = _read(DECISION_DOC)
    assert "Frozen discard set:" in content
    assert "1, 3, 6" in content
    for fragment in (
        "`Mask`",
        "`NO-Mask`",
        "`Safety Cone`",
        "not part of the locked V1 PPE compliance surface",
        "No approved V1 rule, event, or report consumer",
        "original source labels remain untouched",
    ):
        assert fragment in content, fragment


def test_source_fingerprint_remains_unchanged_when_snapshot_is_present() -> None:
    if not SOURCE_DATA_YAML.is_file() or not SOURCE_METADATA.is_file():
        pytest.skip("Git-ignored external snapshot is not present")

    metadata = json.loads(_read(SOURCE_METADATA))
    assert metadata["source_data_yaml_sha256"] == FROZEN_DATA_YAML_SHA256
    assert sha256_file(SOURCE_DATA_YAML) == FROZEN_DATA_YAML_SHA256
    assert FROZEN_DATA_YAML_SHA256 in _read(DATASET_CARD)


def test_p1c_conversion_is_implemented_without_starting_training() -> None:
    contract = PROJECT_ROOT / "docs" / "dataset_contracts" / (
        "CSS-PPE-10-V1-MAPPING.yaml"
    )
    conversion_service = PROJECT_ROOT / "services" / "dataset_conversion_service.py"
    assert contract.is_file()
    assert conversion_service.is_file()
    phase = _read(PHASE_DOC)
    assert "| P1C-2 | Dataset Conversion Implementation |" in phase
    assert (
        "| P1D | Deduplication & Quality Validation | "
        "已经实现 / QUALITY ASSESSED |"
    ) in phase
    assert "| P2 | Training |" not in phase


def test_decision_adr_risk_and_governance_are_recorded() -> None:
    adr = _read(ADR_DOC)
    assert "## ADR-014" in adr
    assert "V1 training class mapping decision" in adr
    assert "Training dataset classes are derived from `CSS-PPE-10-V1`" in adr
    assert "Original dataset remains immutable" in adr

    risk = _read(RISK_DOC)
    assert "RISK-016" in risk
    assert "Mapping frozen before conversion." in risk

    phase = _read(PHASE_DOC)
    assert "| P1C-1 | Class Mapping Decision Gate | 已经实现 / FROZEN |" in phase
    assert "| P1C-1-G1 |" in phase

    charter = _read(CHARTER_DOC)
    assert (
        "| M-001 | CSS 数据集下载、类别转换、Train/Val/Test 管理 | "
        "可复现地获取并转换 CSS；五类映射正确；训练、验证、测试清单可审计且"
        "无交叉泄漏 | 待实现 |"
    ) in charter
    assert "No final selection is made" in _read(DESIGN_DOC)
