import hashlib
import json
from pathlib import Path
import re

import pytest

from services.dataset_service import DatasetService
from utils.dataset_utils import sha256_file
from utils.paths import PROJECT_ROOT


DESIGN_DOC = PROJECT_ROOT / "docs" / "13_CLASS_MAPPING_DESIGN.md"
FREEZE_DOC = PROJECT_ROOT / "docs" / "12_DATASET_FREEZE_DECISION.md"
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

ORIGINAL_CLASSES = (
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
FROZEN_DATA_YAML_SHA256 = (
    "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34"
)
EXPECTED_CHARTER_LOCK_HASH = (
    "9e48d2d5b3960b82cfbe5a93ae67c0ac035702bfd1a022865763fc19fe6d464c"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalize_charter_for_lock_check(text: str) -> str:
    normalized_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\| (?:M|E)-\d{3} \|", line):
            cells = line.split("|")
            cells[-2] = " STATUS "
            line = "|".join(cells)
        normalized_lines.append(line)
    return "\n".join(normalized_lines)


def test_class_mapping_design_document_exists_with_required_sections() -> None:
    assert DESIGN_DOC.is_file()
    content = _read(DESIGN_DOC)
    for heading in (
        "# Class Mapping Design",
        "## 1. Frozen Dataset",
        "## 2. Project Objective",
        "## 3. Candidate Mapping A",
        "## 4. Candidate Mapping B",
        "## 5. Candidate Mapping C",
        "## 6. Comparison Table",
        "## 7. Recommendation Criteria",
        "## 8. Open Questions",
    ):
        assert heading in content, heading
    assert "NO FINAL SELECTION" in content


def test_original_classes_are_documented_in_frozen_order() -> None:
    content = _read(DESIGN_DOC)
    for class_name in ORIGINAL_CLASSES:
        assert f"`{class_name}`" in content
    positions = [content.index(f"`{name}`") for name in ORIGINAL_CLASSES]
    assert positions == sorted(positions)
    assert "data.yaml SHA256" in _read(FREEZE_DOC)
    assert FROZEN_DATA_YAML_SHA256 in _read(DATASET_CARD)


def test_frozen_source_file_is_unchanged_when_snapshot_is_present() -> None:
    if not SOURCE_DATA_YAML.is_file() or not SOURCE_METADATA.is_file():
        pytest.skip("Git-ignored external snapshot is not present")

    metadata = json.loads(_read(SOURCE_METADATA))
    assert metadata["source_data_yaml_sha256"] == FROZEN_DATA_YAML_SHA256
    assert sha256_file(SOURCE_DATA_YAML) == FROZEN_DATA_YAML_SHA256
    assert metadata["original_class_names"] == list(ORIGINAL_CLASSES)


def test_p1c_conversion_contract_exists_and_m001_remains_pending() -> None:
    contract = PROJECT_ROOT / "docs" / "dataset_contracts" / (
        "CSS-PPE-10-V1-MAPPING.yaml"
    )
    assert contract.is_file()
    assert "CSS-PPE-10-V1" in _read(contract)
    assert "PPE-MAPPING-V1" in _read(contract)
    assert (
        "| M-001 | CSS 数据集下载、类别转换、Train/Val/Test 管理 | "
        "可复现地获取并转换 CSS；五类映射正确；训练、验证、测试清单可审计且"
        "无交叉泄漏 | 待实现 |"
    ) in _read(CHARTER_DOC)


def test_m001_remains_pending_and_charter_lock_is_unchanged() -> None:
    charter = _read(CHARTER_DOC)
    assert (
        "| M-001 | CSS 数据集下载、类别转换、Train/Val/Test 管理 | "
        "可复现地获取并转换 CSS；五类映射正确；训练、验证、测试清单可审计且"
        "无交叉泄漏 | 待实现 |"
    ) in charter
    normalized = _normalize_charter_for_lock_check(charter)
    actual_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    assert actual_hash == EXPECTED_CHARTER_LOCK_HASH
    assert "| P1C-2 | Dataset Conversion Implementation |" in _read(PHASE_DOC)


def test_mapping_decision_and_risk_are_recorded() -> None:
    adr = _read(ADR_DOC)
    assert "## ADR-013" in adr
    assert "Class mapping must be frozen before dataset conversion" in adr
    assert "label conversion" in adr
    assert "processed dataset generation" in adr
    assert "model training" in adr

    risk = _read(RISK_DOC)
    assert (
        "RISK-016 | Incorrect class mapping reduces PPE compliance detection "
        "quality"
    ) in risk
    assert "| Medium | High |" in risk
    assert "evaluate mapping before conversion" in risk
    assert "freeze mapping decision" in risk
    assert "keep original snapshot immutable" in risk
