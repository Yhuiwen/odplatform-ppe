from __future__ import annotations

from pathlib import Path

from utils.config_loader import load_config
from utils.paths import PROJECT_ROOT


def test_validation_config_is_enabled_and_image_only() -> None:
    config = load_config("validation")
    validation = config["validation"]

    assert validation["id"] == "P4C-1"
    assert validation["mode"] == "image_only"
    assert validation["execution_enabled"] is True
    assert validation["inference_config"] == "configs/inference.yaml"
    assert validation["output"]["directory"] == "artifacts/validation/P4C-1"
    assert not Path(validation["input"]["source"]).is_absolute()


def test_frozen_inference_config_remains_disabled() -> None:
    inference = load_config("inference")["inference"]

    assert inference["execution_enabled"] is False
    assert inference["model"]["path"] == "models/checkpoints/EXP-001/best.pt"
    assert inference["device"]["policy"] == "cpu_only"


def test_validation_output_is_git_ignored() -> None:
    ignored = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "artifacts/validation/" in ignored
