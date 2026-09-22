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
AUGMENTATION_CONFIG_PATH = (
    PROJECT_ROOT / "experiments" / "configs" / "augmentation.yaml"
)
STRATEGY_PATH = PROJECT_ROOT / "docs" / "18_TRAINING_STRATEGY.md"
EXPERIMENTS_ROOT = PROJECT_ROOT / "experiments"
REPORTS_ROOT = PROJECT_ROOT / "docs" / "reports"
CONFIG_FREEZE_PATH = REPORTS_ROOT / "P2-5.1_CONFIGURATION_FREEZE.md"
CONFIG_FREEZE_REPORT_PATH = (
    PROJECT_ROOT / "P2-5.1_CONFIGURATION_FREEZE_REPORT.md"
)
WEIGHT_PATH = PROJECT_ROOT / "models" / "pretrained" / "yolo11n.pt"
WEIGHT_MANIFEST_PATH = (
    PROJECT_ROOT / "docs" / "weights" / "EXP-001_WEIGHT_MANIFEST.yaml"
)
WEIGHT_REPORT_PATH = (
    PROJECT_ROOT / "P2-5.2_WEIGHT_REGISTRATION_REPORT.md"
)
REMOTE_WEIGHT_REPORT_PATH = (
    REPORTS_ROOT / "EXP-001_REMOTE_WEIGHT_VERIFY.md"
)
DEPENDENCY_LOCK_ROOT = PROJECT_ROOT / "locks" / "EXP-001"
CONDA_ENV_LOCK_PATH = DEPENDENCY_LOCK_ROOT / "conda-environment.yml"
CONDA_EXPLICIT_LOCK_PATH = DEPENDENCY_LOCK_ROOT / "conda-explicit.lock"
PIP_FREEZE_LOCK_PATH = DEPENDENCY_LOCK_ROOT / "pip-freeze-all.txt"
RUNTIME_FINGERPRINT_PATH = (
    DEPENDENCY_LOCK_ROOT / "runtime-fingerprint.yaml"
)
DEPENDENCY_FREEZE_PATH = REPORTS_ROOT / "P2-5.3_DEPENDENCY_FREEZE.md"
DEPENDENCY_FREEZE_REPORT_PATH = (
    PROJECT_ROOT / "P2-5.3_DEPENDENCY_FREEZE_REPORT.md"
)
AUTHORIZATION_CHECKLIST_PATH = (
    REPORTS_ROOT / "P2-2_TRAINING_AUTHORIZATION.md"
)
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
        "weights_provenance",
        "pretrained",
        "class_count",
        "classes",
        "epochs",
        "imgsz",
        "batch",
        "optimizer",
        "learning_rate",
        "lr_strategy",
        "lr_final_fraction",
        "weight_decay",
        "warmup_epochs",
        "patience",
        "augmentation",
        "seed",
        "hyperparameter_status",
        "device",
        "device_strategy",
        "workers",
        "deterministic",
        "amp",
        "cache",
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
        *(EXPERIMENTS_ROOT / "configs").glob("*.yaml"),
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


def test_p2_5_1_configuration_is_frozen_and_training_is_disabled() -> None:
    run_entries = {path.name for path in (EXPERIMENTS_ROOT / "runs").iterdir()}
    report_entries = {
        path.name for path in (EXPERIMENTS_ROOT / "reports").iterdir()
    }
    assert run_entries.issubset({".gitkeep", "EXP-001"})
    assert report_entries.issubset({".gitkeep", "EXP-001"})
    assert ".gitkeep" in run_entries
    assert ".gitkeep" in report_entries

    pt_files = set(PROJECT_ROOT.rglob("*.pt"))
    approved_pt_files = {
        WEIGHT_PATH,
        PROJECT_ROOT / "models" / "checkpoints" / "EXP-001" / "best.pt",
        PROJECT_ROOT / "models" / "checkpoints" / "EXP-001" / "last.pt",
        PROJECT_ROOT / "experiments" / "runs" / "EXP-001" / "weights" / "best.pt",
        PROJECT_ROOT / "experiments" / "runs" / "EXP-001" / "weights" / "last.pt",
    }
    assert pt_files.issubset(approved_pt_files)
    assert not list(PROJECT_ROOT.rglob("*.pth"))
    assert not list(PROJECT_ROOT.rglob("*.weights"))
    baseline = _load_yaml(BASELINE_CONFIG_PATH)
    augmentation = _load_yaml(AUGMENTATION_CONFIG_PATH)
    assert baseline["status"] == "CONFIGURATION_FROZEN"
    assert baseline["execution_enabled"] is False
    assert baseline["review_status"] == (
        "P2-5.1 COMPLETE / CONFIGURATION FROZEN / TRAINING NOT AUTHORIZED"
    )
    assert baseline["model"] == "YOLO11n"
    assert baseline["model_version"] == "8.4.157"
    assert baseline["weights"] == "yolo11n.pt"
    assert baseline["dataset"] == "CSS-PPE-10-V1"
    assert baseline["class_count"] == 7
    assert baseline["imgsz"] == 640
    assert baseline["epochs"] == 100
    assert baseline["batch"] == 16
    assert baseline["optimizer"] == "AdamW"
    assert baseline["learning_rate"] == 0.001
    assert baseline["lr_strategy"] == "cosine"
    assert baseline["seed"] == 42
    assert baseline["device"] == "cuda:0"
    assert baseline["workers"] == 8
    assert baseline["hyperparameter_status"] == "FROZEN_P2_5_1"
    assert augmentation["status"] == "CONFIGURATION_FROZEN"
    assert augmentation["augmentation"]["enabled"] is True
    assert augmentation["augmentation"]["parameters"]["mosaic"] == 1.0
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
    assert "STATUS: CONFIGURATION FROZEN / EXECUTED" in runbook
    assert "TRAINING EXECUTION: COMPLETED" in runbook
    assert "configs/training/exp001_baseline.yaml" in runbook
    assert "experiments/runs/EXP-001" in runbook


def test_p2_5_1_configuration_freeze_documents_exist() -> None:
    for path in (CONFIG_FREEZE_PATH, CONFIG_FREEZE_REPORT_PATH):
        assert path.is_file(), path

    freeze_record = CONFIG_FREEZE_PATH.read_text(encoding="utf-8")
    freeze_report = CONFIG_FREEZE_REPORT_PATH.read_text(encoding="utf-8")
    assert "CONFIGURATION FREEZE: COMPLETE" in freeze_record
    assert "TRAINING AUTHORIZATION: NOT GRANTED" in freeze_record
    assert "P2-5.1 CONFIGURATION FREEZE REPORT" in freeze_report
    assert "TRAINING: NOT AUTHORIZED" in freeze_report


def test_p2_5_2_weight_registration_manifest_is_complete() -> None:
    assert WEIGHT_MANIFEST_PATH.is_file()
    assert WEIGHT_REPORT_PATH.is_file()

    manifest = _load_yaml(WEIGHT_MANIFEST_PATH)
    assert manifest["status"] == "REGISTERED"
    assert manifest["experiment_id"] == "EXP-001"
    assert manifest["model_variant"] == "YOLO11n"
    assert manifest["filename"] == "yolo11n.pt"
    assert manifest["local_path"] == "models/pretrained/yolo11n.pt"
    assert manifest["git_tracked"] is False
    assert manifest["source"]["provider"] == "Ultralytics"
    assert manifest["source"]["release"] == "v8.3.0"
    assert manifest["artifact"]["size_bytes"] == 5613764
    assert manifest["artifact"]["sha256"] == (
        "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
    )
    assert manifest["registration"]["training_executed"] is False
    assert manifest["registration"]["dataset_modified"] is False
    assert manifest["registration"]["mapping_modified"] is False
    assert manifest["registration"]["exp001_config_modified"] is False

    report = WEIGHT_REPORT_PATH.read_text(encoding="utf-8")
    assert "Final status: **READY**" in report
    assert "Training authorization: NOT GRANTED" in report
    assert manifest["artifact"]["sha256"] in report


def test_p2_5_2_registered_weight_matches_manifest_when_present() -> None:
    if not WEIGHT_PATH.is_file():
        pytest.skip("registered pretrained weight is not present in this checkout")
    manifest = _load_yaml(WEIGHT_MANIFEST_PATH)
    assert WEIGHT_PATH.stat().st_size == manifest["artifact"]["size_bytes"]
    assert _sha256_file(WEIGHT_PATH) == manifest["artifact"]["sha256"]


def test_p2_5_4_remote_weight_verification_is_recorded() -> None:
    assert REMOTE_WEIGHT_REPORT_PATH.is_file()
    manifest = _load_yaml(WEIGHT_MANIFEST_PATH)
    assert manifest["remote_training_copy"] == "VERIFIED"
    remote = manifest["remote_training"]
    assert remote["path"] == (
        "/root/autodl-tmp/models/pretrained/yolo11n.pt"
    )
    assert remote["size_bytes"] == manifest["artifact"]["size_bytes"]
    assert remote["sha256"] == manifest["artifact"]["sha256"]
    assert remote["destination_preexisting"] is False
    assert remote["verification_report"] == (
        "docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md"
    )

    report = REMOTE_WEIGHT_REPORT_PATH.read_text(encoding="utf-8")
    assert "Final status: **READY**" in report
    assert "Training authorization: NOT GRANTED" in report
    assert "| File exists | YES | YES | PASS |" in report
    assert "| Size | `5,613,764` bytes | `5,613,764` bytes | PASS |" in report
    assert manifest["artifact"]["sha256"] in report

    authorization = AUTHORIZATION_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "## P2-5.4 Remote Weight Transfer Verification Update" in authorization
    assert "| Remote weight copy | VERIFIED |" in authorization


def test_p2_5_3_dependency_freeze_locks_and_fingerprint_are_complete() -> None:
    for path in (
        CONDA_ENV_LOCK_PATH,
        CONDA_EXPLICIT_LOCK_PATH,
        PIP_FREEZE_LOCK_PATH,
        RUNTIME_FINGERPRINT_PATH,
        DEPENDENCY_FREEZE_PATH,
        DEPENDENCY_FREEZE_REPORT_PATH,
    ):
        assert path.is_file(), path

    conda_environment = _load_yaml(CONDA_ENV_LOCK_PATH)
    conda_dependencies = conda_environment["dependencies"]
    conda_packages = [
        dependency
        for dependency in conda_dependencies
        if isinstance(dependency, str)
    ]
    pip_section = next(
        dependency["pip"]
        for dependency in conda_dependencies
        if isinstance(dependency, dict) and "pip" in dependency
    )
    assert conda_environment["name"] == "ppe-exp001"
    assert len(conda_packages) == 29
    assert len(pip_section) == 52
    assert any(value.startswith("python=3.10.21=") for value in conda_packages)
    assert "torch==2.5.1+cu124" in pip_section
    assert "ultralytics==8.4.157" in pip_section
    assert "prefix:" not in CONDA_ENV_LOCK_PATH.read_text(encoding="utf-8")

    explicit_urls = [
        line
        for line in CONDA_EXPLICIT_LOCK_PATH.read_text(encoding="utf-8").splitlines()
        if line.startswith("https://")
    ]
    assert len(explicit_urls) == 32
    assert "@EXPLICIT" in CONDA_EXPLICIT_LOCK_PATH.read_text(encoding="utf-8")

    pip_freeze = PIP_FREEZE_LOCK_PATH.read_text(encoding="utf-8")
    assert "torch==2.5.1+cu124" in pip_freeze
    assert "ultralytics==8.4.157" in pip_freeze
    assert "pip @ file:///home/task_178792879927882/" in pip_freeze
    assert len(pip_freeze.splitlines()) == 53

    runtime = _load_yaml(RUNTIME_FINGERPRINT_PATH)
    assert runtime["status"] == "FROZEN"
    assert runtime["experiment_id"] == "EXP-001"
    assert runtime["provider"]["instance_id"] == "bcb849a74f-38320766"
    assert runtime["gpu"]["uuid"] == (
        "GPU-ad5f1f4a-5bdb-4a26-9b62-5eb190196bb4"
    )
    assert runtime["cuda"]["nvidia_driver_version"] == "560.35.03"
    assert runtime["cuda"]["driver_api_version"] == "12.6"
    assert runtime["cuda"]["pytorch_runtime_version"] == "12.4"
    assert runtime["runtime"]["torch"] == "2.5.1+cu124"
    assert runtime["runtime"]["ultralytics"] == "8.4.157"
    assert runtime["runtime"]["pip_check"] == "PASS"

    expected_hashes = {
        "conda_environment": (
            CONDA_ENV_LOCK_PATH,
            "95b03d3dfc57f4124dcf370b9bd42cadab86f1701649d3610824c74a86f88fc3",
        ),
        "conda_explicit": (
            CONDA_EXPLICIT_LOCK_PATH,
            "599ed7c0e6b9ee9817517d140488c382066fc2e9d7e2a14315deefb43f3438d5",
        ),
        "pip_freeze_all": (
            PIP_FREEZE_LOCK_PATH,
            "34c9b668095029732f1c4c084b81185309c64614fe25e88b69328e1f9b91599e",
        ),
    }
    for key, (path, expected_hash) in expected_hashes.items():
        assert runtime["lock_files"][key]["sha256"] == expected_hash
        assert _sha256_file(path) == expected_hash

    freeze_record = DEPENDENCY_FREEZE_PATH.read_text(encoding="utf-8")
    freeze_report = DEPENDENCY_FREEZE_REPORT_PATH.read_text(encoding="utf-8")
    assert "Dependency freeze: COMPLETE" in freeze_record
    assert "TRAINING: NOT AUTHORIZED" in freeze_record
    assert "Final status: **READY**" in freeze_report
    assert "Training authorization: NOT GRANTED" in freeze_report

    authorization = AUTHORIZATION_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "| Dependencies | FROZEN / VERIFIED |" in authorization
    assert "locks/EXP-001/conda-environment.yml" in authorization
    assert "| Authorization | NOT GRANTED |" in authorization


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


def test_charter_locked_body_is_unchanged_against_phase_zero_tag() -> None:
    result = subprocess.run(
        ["git", "show", "charter-v1:docs/00_PROJECT_CHARTER.md"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        pytest.skip("charter-v1 tag is unavailable in this checkout")

    def normalize_statuses(text: str) -> str:
        lines: list[str] = []
        for line in text.splitlines():
            if re.match(r"^\| (?:M|E)-\d{3} \|", line):
                cells = line.split("|")
                cells[-2] = " STATUS "
                line = "|".join(cells)
            lines.append(line)
        return "\n".join(lines)

    current = (PROJECT_ROOT / "docs" / "00_PROJECT_CHARTER.md").read_text(
        encoding="utf-8"
    )
    assert normalize_statuses(current) == normalize_statuses(result.stdout)
