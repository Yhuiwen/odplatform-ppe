import hashlib
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from utils.paths import PROJECT_ROOT


CONTRACT_PATH = (
    PROJECT_ROOT
    / "docs"
    / "dataset_contracts"
    / "CSS-PPE-10-V1-TRAINING.yaml"
)
SCHEMA_PATH = PROJECT_ROOT / "configs" / "training" / "schema.yaml"
BASELINE_CONFIG_PATH = (
    PROJECT_ROOT / "configs" / "training" / "exp001_baseline.yaml"
)
STRATEGY_PATH = PROJECT_ROOT / "docs" / "18_TRAINING_STRATEGY.md"
EXPERIMENTS_ROOT = PROJECT_ROOT / "experiments"
REPORTS_ROOT = PROJECT_ROOT / "docs" / "reports"
CONTRACT_AUDIT_PATH = REPORTS_ROOT / "P1E-1_TRAINING_CONTRACT_AUDIT.md"
CONFIG_AUDIT_PATH = REPORTS_ROOT / "P1E-1_EXPERIMENT_CONFIG_AUDIT.md"
ENVIRONMENT_AUDIT_PATH = REPORTS_ROOT / "P1E-1_TRAINING_ENVIRONMENT_AUDIT.md"
CHECKLIST_PATH = REPORTS_ROOT / "P1E-1_REPRODUCIBILITY_CHECKLIST.md"
RUNBOOK_PATH = REPORTS_ROOT / "EXP-001_TRAINING_RUNBOOK.md"
SOURCE_DATA_YAML = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "css-v27-yolov8"
    / "source"
    / "data.yaml"
)
SOURCE_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "css-v27-yolov8"
    / "metadata"
    / "checksums.sha256"
)
PROCESSED_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "css-ppe-10-v1"
    / "metadata"
    / "checksums.sha256"
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_training_config_schema_exists_and_is_non_executable() -> None:
    assert SCHEMA_PATH.is_file()
    assert STRATEGY_PATH.is_file()
    schema = _load_yaml(SCHEMA_PATH)
    assert schema["schema_version"] == "training-config-v1"
    assert schema["status"] == "DESIGN_FROZEN"
    assert schema["execution_enabled"] is False
    assert schema["training_execution"]["allowed"] is False
    for field in (
        "experiment_id",
        "dataset",
        "dataset_contract",
        "processed_dataset",
        "model",
        "model_family",
        "model_variant",
        "model_version",
        "weights",
        "epochs",
        "imgsz",
        "batch",
        "optimizer",
        "learning_rate",
        "augmentation",
        "seed",
        "hyperparameter_status",
        "device",
        "device_strategy",
        "output_path",
        "logs_path",
        "reports_path",
        "checkpoint_path",
        "metrics",
    ):
        assert field in schema["required_fields"]


def test_dataset_training_contract_exists_with_frozen_identity() -> None:
    assert CONTRACT_PATH.is_file()
    contract = _load_yaml(CONTRACT_PATH)
    assert contract["dataset_id"] == "CSS-PPE-10-V1"
    assert contract["processed_dataset"] == "css-ppe-10-v1"
    assert contract["mapping"] == "PPE-MAPPING-V1"
    assert contract["classes"] == {
        0: "person",
        1: "hardhat",
        2: "no_hardhat",
        3: "vest",
        4: "no_vest",
        5: "machinery",
        6: "vehicle",
    }
    assert contract["fingerprint"] == {
        "source_data_yaml_sha256": (
            "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34"
        ),
        "source_manifest_sha256": (
            "ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795"
        ),
        "processed_manifest_sha256": (
            "dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c"
        ),
    }
    assert contract["quality_report"] == "17_DATASET_QUALITY_REPORT.md"
    assert contract["quality_status"] == "PASS"
    assert contract["release"]["training_started"] is False


def test_experiment_ids_match_frozen_format() -> None:
    experiment_ids: list[str] = []
    config_paths = [
        *EXPERIMENTS_ROOT.rglob("*.yaml"),
        BASELINE_CONFIG_PATH,
    ]
    for path in config_paths:
        data = _load_yaml(path)
        if isinstance(data, dict) and "experiment_id" in data:
            experiment_ids.append(str(data["experiment_id"]))
        if isinstance(data, dict):
            augmentation = data.get("augmentation")
            if isinstance(augmentation, dict):
                experiment_id = augmentation.get("experiment_id")
                if experiment_id is not None:
                    experiment_ids.append(str(experiment_id))
    assert experiment_ids == ["EXP-001"]
    assert all(re.fullmatch(r"EXP-\d{3}", item) for item in experiment_ids)
    baseline_template = _load_yaml(
        EXPERIMENTS_ROOT / "configs" / "baseline.yaml"
    )
    assert baseline_template["template_for"] == "EXP-001"
    assert baseline_template["canonical_config"] == (
        "configs/training/exp001_baseline.yaml"
    )
    strategy = STRATEGY_PATH.read_text(encoding="utf-8")
    assert "| Experiment ID | `EXP-001` |" in strategy
    assert "| Model | `YOLO11n` |" in strategy
    assert "mAP50-95" in strategy


def test_no_training_run_or_weight_file_was_created() -> None:
    assert sorted(path.name for path in (EXPERIMENTS_ROOT / "runs").iterdir()) == [
        ".gitkeep"
    ]
    assert sorted(
        path.name for path in (EXPERIMENTS_ROOT / "reports").iterdir()
    ) == [".gitkeep"]
    assert not [
        path
        for pattern in ("*.pt", "*.pth", "*.weights")
        for path in PROJECT_ROOT.rglob(pattern)
    ]
    baseline = _load_yaml(BASELINE_CONFIG_PATH)
    assert baseline["execution_enabled"] is False
    assert baseline["review_status"] == (
        "P1E-1 COMPLETED / TRAINING NOT STARTED"
    )
    assert baseline["epochs"] == "PENDING_DESIGN_REVIEW"
    assert baseline["imgsz"] == "PENDING_DESIGN_REVIEW"
    assert baseline["batch"] == "PENDING_DESIGN_REVIEW"
    assert baseline["optimizer"] == "PENDING_DESIGN_REVIEW"
    assert baseline["seed"] == "PENDING_DESIGN_REVIEW"
    assert baseline["hyperparameter_status"] == "PENDING_DESIGN_REVIEW"
    assert baseline["device"] == "PENDING_DESIGN_REVIEW"
    assert baseline["device_strategy"] == "PENDING_DESIGN_REVIEW"
    assert baseline["output_path"] == "experiments/runs/EXP-001"
    assert baseline["logs_path"] == "artifacts/logs/EXP-001"
    assert baseline["reports_path"] == "experiments/reports/EXP-001"
    assert baseline["checkpoint_path"] == "models/checkpoints/EXP-001"


def test_dataset_contract_fingerprints_match_materialized_files() -> None:
    contract = _load_yaml(CONTRACT_PATH)
    fingerprints = contract["fingerprint"]
    if not SOURCE_DATA_YAML.is_file():
        pytest.skip("frozen source data.yaml is not present in this checkout")
    if not SOURCE_MANIFEST.is_file() or not PROCESSED_MANIFEST.is_file():
        pytest.skip("frozen dataset manifests are not present in this checkout")
    assert _sha256_file(SOURCE_DATA_YAML) == fingerprints[
        "source_data_yaml_sha256"
    ]
    assert _sha256_file(SOURCE_MANIFEST) == fingerprints[
        "source_manifest_sha256"
    ]
    assert _sha256_file(PROCESSED_MANIFEST) == fingerprints[
        "processed_manifest_sha256"
    ]


def test_p1e1_reports_and_runbook_record_review_evidence() -> None:
    for path in (
        CONTRACT_AUDIT_PATH,
        CONFIG_AUDIT_PATH,
        ENVIRONMENT_AUDIT_PATH,
        CHECKLIST_PATH,
        RUNBOOK_PATH,
    ):
        assert path.is_file(), path

    contract_audit = CONTRACT_AUDIT_PATH.read_text(encoding="utf-8")
    assert "TRAINING DATA CONTRACT AUDIT REPORT: PASS" in contract_audit
    assert "dataset fingerprint" in contract_audit.lower()

    config_audit = CONFIG_AUDIT_PATH.read_text(encoding="utf-8")
    assert "EXPERIMENT CONFIG AUDIT REPORT: PASS" in config_audit
    assert "Experiment ID uniqueness" in config_audit

    environment_audit = ENVIRONMENT_AUDIT_PATH.read_text(encoding="utf-8")
    assert "NOT READY FOR TRAINING" in environment_audit
    assert "PyTorch | `NOT INSTALLED`" in environment_audit
    assert "Ultralytics | `NOT INSTALLED`" in environment_audit

    checklist = CHECKLIST_PATH.read_text(encoding="utf-8")
    for heading in ("## Dataset", "## Experiment", "## Runtime", "## Artifacts"):
        assert heading in checklist
    assert "REVIEW COMPLETE / TRAINING NOT STARTED" in checklist

    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    assert "STATUS: DESIGN ONLY" in runbook
    assert "TRAINING EXECUTION: NOT STARTED" in runbook
    assert "configs/training/exp001_baseline.yaml" in runbook
    assert "experiments/runs/EXP-001" in runbook


def test_p2_3_provider_selection_keeps_training_unauthorized() -> None:
    report_path = REPORTS_ROOT / "P2-3_CLOUD_PROVIDER_SELECTION.md"
    authorization_path = REPORTS_ROOT / "P2-2_TRAINING_AUTHORIZATION.md"

    assert report_path.is_file()
    report = report_path.read_text(encoding="utf-8")
    assert "| Provider strategy | AutoDL primary |" in report
    assert "| GPU | NVIDIA GeForce RTX 4090 24GB |" in report
    assert "| Maximum planning runtime | 40 GPU-hours" in report
    assert "| Compute budget ceiling | CNY 150" in report
    assert "Provisioning: NOT STARTED" in report
    assert "Training authorization: NOT GRANTED" in report

    authorization = authorization_path.read_text(encoding="utf-8")
    assert "| Environment | DESIGN SELECTED / NOT PROVISIONED |" in authorization
    assert "| GPU | DESIGN SELECTED / NOT VERIFIED |" in authorization
    assert "| Authorization | NOT GRANTED |" in authorization


def test_charter_is_unchanged_against_phase_zero_tag() -> None:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "charter-v1",
            "--",
            "docs/00_PROJECT_CHARTER.md",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode == 128:
        pytest.skip("charter-v1 tag is unavailable in this checkout")
    assert result.returncode == 0
