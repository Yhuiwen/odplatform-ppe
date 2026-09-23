from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from core.inference.detector import (
    CheckpointIntegrityError,
    ImageNotFoundError,
    InferenceExecutionDisabledError,
    InvalidImageFormatError,
    YOLODetector,
)
from core.schemas.detection import DetectionResult
from scripts.run_image_inference import main
from services.inference_service import InferenceService
from utils.config_loader import load_config


class _Values:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class _Boxes:
    def __init__(self):
        self.xyxy = _Values([[10.0, 20.0, 50.0, 80.0]])
        self.cls = _Values([1.0])
        self.conf = _Values([0.91])

    def __len__(self) -> int:
        return 1


class _Result:
    boxes = _Boxes()


class _Model:
    names = {
        0: "person",
        1: "hardhat",
        2: "no_hardhat",
        3: "vest",
        4: "no_vest",
        5: "machinery",
        6: "vehicle",
    }

    def __init__(self):
        self.predict_kwargs = None

    def predict(self, **kwargs):
        self.predict_kwargs = kwargs
        return [_Result()]


def _valid_image(tmp_path: Path) -> Path:
    path = tmp_path / "sample.jpg"
    path.write_bytes(b"not-a-real-image-but-path-valid")
    return path


def _fake_checkpoint(tmp_path: Path) -> Path:
    path = tmp_path / "best.pt"
    path.write_bytes(b"fake-checkpoint")
    return path


def _enabled_config(tmp_path: Path, checkpoint: Path) -> Path:
    config = load_config("inference")
    config["inference"]["execution_enabled"] = True
    config["inference"]["model"]["path"] = str(checkpoint)
    config["inference"]["model"]["size_bytes"] = checkpoint.stat().st_size
    config["inference"]["model"]["sha256"] = hashlib.sha256(
        checkpoint.read_bytes()
    ).hexdigest()
    path = tmp_path / "enabled-inference.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def test_invalid_input_is_rejected_before_model_loading(tmp_path: Path) -> None:
    calls = 0

    def fail_if_called(_: Path):
        nonlocal calls
        calls += 1
        raise AssertionError("model factory must not be called")

    service = InferenceService(detector=YOLODetector(model_factory=fail_if_called))

    with pytest.raises(ImageNotFoundError, match="does not exist"):
        service.infer_image(tmp_path / "missing.jpg")

    unsupported = tmp_path / "sample.txt"
    unsupported.write_text("not an image", encoding="utf-8")
    with pytest.raises(InvalidImageFormatError, match="Unsupported image format"):
        service.infer_image(unsupported)

    assert calls == 0


def test_execution_disabled_is_explicit_without_loading_model(tmp_path: Path) -> None:
    calls = 0

    def fail_if_called(_: Path):
        nonlocal calls
        calls += 1
        raise AssertionError("model factory must not be called")

    service = InferenceService(detector=YOLODetector(model_factory=fail_if_called))
    with pytest.raises(InferenceExecutionDisabledError) as exc_info:
        service.infer_image(_valid_image(tmp_path))

    assert exc_info.value.code == "execution_disabled"
    assert calls == 0


def test_explicit_execution_override_does_not_change_frozen_config(
    tmp_path: Path,
) -> None:
    checkpoint = _fake_checkpoint(tmp_path)
    config_path = _enabled_config(tmp_path, checkpoint)
    config = load_config(config_path)
    config["inference"]["execution_enabled"] = False
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    calls = 0

    def model_factory(_: Path):
        nonlocal calls
        calls += 1
        return _Model()

    service = InferenceService(
        config_path=config_path,
        execution_enabled=True,
        detector=YOLODetector(
            config_path,
            execution_enabled=True,
            model_factory=model_factory,
            image_loader=lambda _: object(),
        ),
    )

    results = service.infer_image(_valid_image(tmp_path))

    assert calls == 1
    assert len(results) == 1


def test_model_is_lazy_and_schema_output_has_no_framework_objects(
    tmp_path: Path,
) -> None:
    checkpoint = _fake_checkpoint(tmp_path)
    config_path = _enabled_config(tmp_path, checkpoint)
    calls = 0
    model = _Model()

    def model_factory(path: Path):
        nonlocal calls
        calls += 1
        assert path == checkpoint
        return model

    detector = YOLODetector(
        config_path,
        model_factory=model_factory,
        image_loader=lambda _: object(),
    )
    assert calls == 0

    results = detector.detect_image(_valid_image(tmp_path))

    assert calls == 1
    assert all(isinstance(result, DetectionResult) for result in results)
    assert model.predict_kwargs["device"] == "cpu"
    assert model.predict_kwargs["imgsz"] == 640
    assert model.predict_kwargs["conf"] == 0.25
    assert model.predict_kwargs["iou"] == 0.45
    assert model.predict_kwargs["classes"] == [0, 1, 2, 3, 4]

    payload = results[0].to_dict()
    assert json.loads(json.dumps(payload)) == {
        "frame_id": 0,
        "timestamp": 0.0,
        "source": "image:sample.jpg",
        "class_id": 1,
        "class_name": "hardhat",
        "confidence": 0.91,
        "bbox": {"x1": 10.0, "y1": 20.0, "x2": 50.0, "y2": 80.0},
    }


def test_checkpoint_integrity_error_is_explicit(tmp_path: Path) -> None:
    checkpoint = _fake_checkpoint(tmp_path)
    config_path = _enabled_config(tmp_path, checkpoint)
    config = load_config(config_path)
    config["inference"]["model"]["sha256"] = "0" * 64
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    detector = YOLODetector(
        config_path,
        model_factory=lambda _: _Model(),
        image_loader=lambda _: object(),
    )
    with pytest.raises(CheckpointIntegrityError, match="SHA256 mismatch"):
        detector.detect_image(_valid_image(tmp_path))


def test_cli_prints_execution_disabled_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(_valid_image(tmp_path))])

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out) == {
        "status": "error",
        "error": "execution_disabled",
        "message": "Image inference is disabled by configs/inference.yaml",
    }
