from utils.config_loader import load_yaml
from utils.paths import PROJECT_ROOT


def test_tracker_contract_is_frozen_and_person_only() -> None:
    config = load_yaml("tracker")["tracker"]

    assert config["phase"] == 5
    assert config["subphase"] == "5-1"
    assert config["status"] == "frozen"
    assert config["execution_enabled"] is True
    assert config["implementation"]["api"] == "BYTETracker"
    assert config["implementation"]["version"] == "8.4.157"
    assert config["parameters"]["fuse_score"] is True
    assert config["person_filter"] == {
        "class_id": 0,
        "class_name": "person",
        "min_confidence": 0.25,
    }
    assert config["output"]["result_type"] == "TrackResult"


def test_association_contract_is_frozen_and_unknown_safe() -> None:
    config = load_yaml("association")["association"]

    assert config["phase"] == 5
    assert config["subphase"] == "5-2"
    assert config["status"] == "frozen"
    assert config["execution_enabled"] is True
    assert config["input"]["ppe_classes"] == {
        "hardhat": 1,
        "no_hardhat": 2,
        "vest": 3,
        "no_vest": 4,
    }
    assert config["thresholds"] == {
        "min_detection_confidence": 0.25,
        "min_containment_ratio": 0.50,
        "min_iou": 0.10,
        "ambiguity_margin": 0.10,
    }
    assert config["selection"]["allow_nearest_distance"] is False
    assert config["selection"]["max_assignments_per_ppe"] == 1
    assert config["output"]["result_type"] == "AssociationResult"
    assert config["output"]["uncertain_status"] == "unknown"
    assert config["errors"]["synthetic_assignment"] is False


def test_phase5_design_freezes_contracts_without_implementation() -> None:
    design_path = (
        PROJECT_ROOT
        / "docs"
        / "designs"
        / "phase-05"
        / "P5-0_INTERFACE_FREEZE.md"
    )
    assert design_path.is_file()
    design = design_path.read_text(encoding="utf-8")

    required = [
        "DetectionResult",
        "TrackResult",
        "AssociationResult",
        "person only",
        "containment",
        "IoU",
        "confidence",
        "unknown",
        "nearest-distance assignment",
        "Phase 5-1",
        "Phase 5-2",
        "Phase 5-3",
    ]
    for fragment in required:
        assert fragment in design


def test_phase5_freeze_does_not_modify_frozen_training_assets() -> None:
    training_contract = (
        PROJECT_ROOT / "docs" / "dataset_contracts" / "CSS-PPE-10-V1-TRAINING.yaml"
    )
    assert training_contract.is_file()
    contract = load_yaml(training_contract)
    assert contract["dataset_id"] == "CSS-PPE-10-V1"
    assert contract["classes"][0] == "person"
    assert contract["fingerprint"]["source_data_yaml_sha256"] == (
        "5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34"
    )
