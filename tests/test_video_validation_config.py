from __future__ import annotations

from pathlib import Path

from utils.config_loader import load_config
from utils.paths import PROJECT_ROOT


def test_video_validation_config_is_enabled_and_video_only() -> None:
    config = load_config("video_validation")
    validation = config["validation"]

    assert validation["id"] == "P4C-2"
    assert validation["mode"] == "video_only"
    assert validation["execution_enabled"] is True
    assert validation["inference"]["config"] == "configs/inference.yaml"
    assert validation["output"]["directory"] == "artifacts/validation/P4C-2"
    assert not Path(validation["input"]["source"]).is_absolute()


def test_video_validation_matches_frozen_inference_contract() -> None:
    declared = load_config("video_validation")["validation"]["inference"]
    frozen = load_config("inference")["inference"]

    assert frozen["execution_enabled"] is False
    assert declared["checkpoint"] == frozen["model"]["path"]
    assert declared["checkpoint_sha256"] == frozen["model"]["sha256"]
    assert declared["device"] == frozen["device"]["device"] == "cpu"
    assert (
        declared["confidence_threshold"]
        == frozen["detection"]["conf_threshold"]
    )
    assert declared["iou_threshold"] == frozen["detection"]["iou_threshold"]
    assert declared["imgsz"] == frozen["preprocessing"]["imgsz"]


def test_video_validation_output_is_git_ignored() -> None:
    ignored = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "artifacts/validation/" in ignored
