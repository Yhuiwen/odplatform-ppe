import hashlib
from pathlib import Path

import pytest
import yaml

from services.train_service import (
    TrainService,
    TrainingAuthorizationError,
    TrainingConfigurationError,
)


CLASSES = [
    "person",
    "hardhat",
    "no_hardhat",
    "vest",
    "no_vest",
    "machinery",
    "vehicle",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def _training_fixture(tmp_path: Path) -> tuple[dict, Path, Path, Path, Path]:
    config_path = tmp_path / "exp001_baseline.yaml"
    authorization_path = tmp_path / "exp001_authorization.yaml"
    data_yaml_path = tmp_path / "data.yaml"
    weights_path = tmp_path / "yolo11n.pt"
    augmentation_path = tmp_path / "augmentation.yaml"
    run_dir = tmp_path / "runs" / "EXP-001"
    log_dir = tmp_path / "logs" / "EXP-001"
    report_dir = tmp_path / "reports" / "EXP-001"
    checkpoint_dir = tmp_path / "checkpoints" / "EXP-001"

    config = {
        "status": "CONFIGURATION_FROZEN",
        "experiment_id": "EXP-001",
        "dataset": "CSS-PPE-10-V1",
        "dataset_contract": str(tmp_path / "contract.yaml"),
        "processed_dataset": str(tmp_path / "dataset"),
        "model": "YOLO11n",
        "model_version": "8.4.157",
        "weights": "yolo11n.pt",
        "class_count": 7,
        "classes": CLASSES,
        "epochs": 1,
        "imgsz": 640,
        "batch": 16,
        "optimizer": "AdamW",
        "learning_rate": 0.001,
        "lr_strategy": "cosine",
        "lr_final_fraction": 0.01,
        "weight_decay": 0.0005,
        "warmup_epochs": 3.0,
        "patience": 20,
        "augmentation": str(augmentation_path),
        "seed": 42,
        "device": "cuda:0",
        "workers": 8,
        "deterministic": True,
        "amp": True,
        "cache": False,
        "output_path": str(run_dir),
        "logs_path": str(log_dir),
        "reports_path": str(report_dir),
        "checkpoint_path": str(checkpoint_dir),
    }
    _write_yaml(config_path, config)
    _write_yaml(
        data_yaml_path,
        {"path": str(tmp_path / "dataset"), "nc": 7, "names": CLASSES},
    )
    _write_yaml(
        augmentation_path,
        {
            "augmentation": {
                "parameters": {
                    "image_scale": 0.5,
                    "translation": 0.1,
                    "horizontal_flip": 0.5,
                    "color_jitter": 0.2,
                    "mosaic": 1.0,
                    "close_mosaic": 10,
                }
            }
        },
    )
    weights_path.write_bytes(b"registered-yolo11n")
    _write_yaml(
        authorization_path,
        {
            "status": "GRANTED",
            "experiment_id": "EXP-001",
            "training_execution_enabled": True,
            "configuration_sha256": _sha256(config_path),
            "data_yaml_path": str(data_yaml_path),
            "weight_path": str(weights_path),
            "weight_sha256": _sha256(weights_path),
        },
    )
    return (
        config,
        config_path,
        authorization_path,
        data_yaml_path,
        weights_path,
    )


def test_training_requires_granted_authorization(tmp_path: Path) -> None:
    config, config_path, authorization_path, data_yaml_path, weights_path = (
        _training_fixture(tmp_path)
    )
    authorization = yaml.safe_load(
        authorization_path.read_text(encoding="utf-8")
    )
    authorization["status"] = "DENIED"
    _write_yaml(authorization_path, authorization)

    with pytest.raises(TrainingAuthorizationError):
        TrainService().train(
            config,
            config_path=config_path,
            authorization_path=authorization_path,
            data_yaml_path=data_yaml_path,
            weights_path=weights_path,
        )


def test_training_rejects_configuration_hash_mismatch(tmp_path: Path) -> None:
    config, config_path, authorization_path, data_yaml_path, weights_path = (
        _training_fixture(tmp_path)
    )
    authorization = yaml.safe_load(
        authorization_path.read_text(encoding="utf-8")
    )
    authorization["configuration_sha256"] = "0" * 64
    _write_yaml(authorization_path, authorization)

    with pytest.raises(TrainingAuthorizationError):
        TrainService().train(
            config,
            config_path=config_path,
            authorization_path=authorization_path,
            data_yaml_path=data_yaml_path,
            weights_path=weights_path,
        )


def test_training_rejects_dataset_class_order_mismatch(tmp_path: Path) -> None:
    config, config_path, authorization_path, data_yaml_path, weights_path = (
        _training_fixture(tmp_path)
    )
    _write_yaml(
        data_yaml_path,
        {"path": str(tmp_path / "dataset"), "nc": 7, "names": CLASSES[::-1]},
    )

    with pytest.raises(TrainingConfigurationError):
        TrainService().train(
            config,
            config_path=config_path,
            authorization_path=authorization_path,
            data_yaml_path=data_yaml_path,
            weights_path=weights_path,
        )


def test_authorized_training_passes_frozen_parameters_to_runner(
    tmp_path: Path,
) -> None:
    config, config_path, authorization_path, data_yaml_path, weights_path = (
        _training_fixture(tmp_path)
    )
    captured: dict = {}

    def runner(payload: dict) -> None:
        captured.update(payload)
        run_dir = Path(payload["params"]["project"]) / payload["params"]["name"]
        (run_dir / "weights").mkdir(parents=True)
        (run_dir / "weights" / "best.pt").write_bytes(b"best")
        (run_dir / "weights" / "last.pt").write_bytes(b"last")

    result = TrainService().train(
        config,
        config_path=config_path,
        authorization_path=authorization_path,
        data_yaml_path=data_yaml_path,
        weights_path=weights_path,
        runner=runner,
    )

    params = captured["params"]
    assert captured["weights"] == str(weights_path)
    assert params["epochs"] == 1
    assert params["imgsz"] == 640
    assert params["batch"] == 16
    assert params["optimizer"] == "AdamW"
    assert params["lr0"] == 0.001
    assert params["lrf"] == 0.01
    assert params["cos_lr"] is True
    assert params["seed"] == 42
    assert params["device"] == "cuda:0"
    assert params["scale"] == 0.5
    assert params["translate"] == 0.1
    assert params["fliplr"] == 0.5
    assert params["hsv_h"] == 0.2
    assert params["hsv_s"] == 0.2
    assert params["hsv_v"] == 0.2
    assert params["mosaic"] == 1.0
    assert params["close_mosaic"] == 10
    assert result.run_dir == Path(config["output_path"])
    assert result.best_checkpoint == Path(config["checkpoint_path"]) / "best.pt"
    assert result.last_checkpoint == Path(config["checkpoint_path"]) / "last.pt"
    assert result.best_checkpoint.read_bytes() == b"best"
    assert result.last_checkpoint.read_bytes() == b"last"
