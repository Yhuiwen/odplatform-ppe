"""Focused coverage for the monitored CPU profile and its artifact boundary."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from core.inference.detector import CheckpointIntegrityError, YOLODetector
from utils.config_loader import load_config


class _Model:
    names = {0: "person", 1: "hardhat", 2: "no_hardhat", 3: "vest", 4: "no_vest"}

    def predict(self, **kwargs):
        return []


def _detector(tmp_path: Path) -> tuple[YOLODetector, Path, Path]:
    config = load_config("configs/inference_cpu_fast.yaml")
    source = tmp_path / "best.pt"
    source.write_bytes(b"frozen-source")
    export = tmp_path / "best_cpu_416_openvino_model"
    export.mkdir()
    hashes = {}
    for name in ("best.xml", "best.bin", "metadata.yaml"):
        content = name.encode()
        (export / name).write_bytes(content)
        hashes[name] = hashlib.sha256(content).hexdigest()
    model = config["inference"]["model"]
    model.update(
        path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        size_bytes=source.stat().st_size, export_path=str(export), export_sha256=hashes,
    )
    path = tmp_path / "inference.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    detector = YOLODetector(path, execution_enabled=True, model_factory=lambda _: _Model())
    return detector, source, export


def test_monitoring_uses_fast_profile_and_original_stays_640() -> None:
    monitoring = load_config("configs/monitoring.yaml")["monitoring"]
    fast = load_config(monitoring["inference_config"])["inference"]
    original = load_config("configs/inference.yaml")["inference"]
    assert fast["runtime"]["backend"] == "openvino"
    assert fast["preprocessing"]["imgsz"] == 416
    assert original["preprocessing"]["imgsz"] == 640
    assert original["model"]["sha256"] == fast["model"]["sha256"]


def test_export_integrity_is_checked_before_first_frame(tmp_path: Path) -> None:
    detector, _, export = _detector(tmp_path)
    (export / "best.xml").write_bytes(b"changed")
    with pytest.raises(CheckpointIntegrityError, match="OpenVINO export SHA256 mismatch"):
        detector.detect_frame(object(), frame_id=0, timestamp=0, source="test")


def test_source_checkpoint_is_checked_once_for_loaded_export(tmp_path: Path) -> None:
    detector, source, _ = _detector(tmp_path)
    detector.detect_frame(object(), frame_id=0, timestamp=0, source="test")
    source.write_bytes(b"changed-source")
    detector.detect_frame(object(), frame_id=1, timestamp=1, source="test")
