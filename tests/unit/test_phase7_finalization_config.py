from pathlib import Path

import pytest
import yaml

from services.monitoring_service import (
    MonitoringConfigurationError,
    MonitoringSourceRequest,
)
from utils.paths import PROJECT_ROOT


def _load(relative_path: str) -> dict:
    with (PROJECT_ROOT / relative_path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_monitoring_runtime_config_is_frozen_and_fails_closed() -> None:
    config = _load("configs/monitoring.yaml")["monitoring"]
    processing = config["processing"]

    assert config["subphase"] == "7-6"
    assert config["execution_enabled"] is True
    assert processing["background_worker"] is True
    assert processing["sequential_frames"] is True
    assert processing["frame_skipping"] is False
    assert processing["batch_inference"] is False
    assert processing["persist_before_alert"] is True
    assert config["sources"]["local_video_fallback"] is False
    assert config["sources"]["synthetic_frames"] is False
    assert config["errors"]["fail_closed"] is True
    assert config["errors"]["isolate_alert_failures"] is True


def test_p7_6_camera_rtsp_validation_is_design_only_and_checkpoint_frozen() -> None:
    config = _load("configs/p7_6_validation.yaml")["validation"]
    inference = _load("configs/inference.yaml")["inference"]

    assert config["subphase"] == "7-6"
    assert config["execution_enabled"] is False
    assert config["source"]["accepted_kinds"] == ["usb_camera", "rtsp"]
    assert config["source"]["local_video_fallback"] is False
    assert config["runtime"]["checkpoint"] == inference["model"]["path"]
    assert (
        config["runtime"]["checkpoint_sha256"]
        == inference["model"]["sha256"]
    )
    assert config["runtime"]["device_policy"] == "cpu_only"
    assert config["errors"]["fail_closed"] is True
    assert config["errors"]["synthetic_frame_on_disconnect"] is False
    assert config["errors"]["silent_reconnect"] is False


def test_monitoring_source_request_rejects_invalid_locations() -> None:
    with pytest.raises(MonitoringConfigurationError):
        MonitoringSourceRequest(source_type="mp4", location=" ")
    with pytest.raises(MonitoringConfigurationError):
        MonitoringSourceRequest(source_type="usb_camera", location=-1)
    with pytest.raises(MonitoringConfigurationError):
        MonitoringSourceRequest(source_type="invalid", location="x")


def test_p7_6_evidence_path_is_git_ignored() -> None:
    ignore_file = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    evidence_path = Path("artifacts/validation")

    assert f"{evidence_path.as_posix()}/" in ignore_file
