"""Lazy YOLO11 single-image detector using the frozen Phase 4B-0 config."""

from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Callable, Iterable

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult
from utils.config_loader import load_config
from utils.paths import PROJECT_ROOT


class InferenceError(RuntimeError):
    """Base error with a stable machine-readable code."""

    code = "inference_error"


class InferenceConfigurationError(InferenceError):
    code = "invalid_inference_configuration"


class InferenceExecutionDisabledError(InferenceError):
    code = "execution_disabled"


class InferenceRuntimeError(InferenceError):
    code = "runtime_unavailable"


class CheckpointIntegrityError(InferenceError):
    code = "checkpoint_integrity_failed"


class InvalidImageError(InferenceError):
    code = "invalid_image"


class ImageNotFoundError(InvalidImageError):
    code = "image_not_found"


class InvalidImageFormatError(InvalidImageError):
    code = "invalid_image_format"


ModelFactory = Callable[[Path], Any]
ImageLoader = Callable[[Path], Any]


class YOLODetector:
    """Detect objects on one validated image path.

    The Ultralytics model and image runtime are imported only when
    ``detect_image`` reaches the execution-enabled path.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        execution_enabled: bool | None = None,
        model_factory: ModelFactory | None = None,
        image_loader: ImageLoader | None = None,
    ) -> None:
        config = load_config(config_path or "inference")
        inference = config.get("inference")
        if not isinstance(inference, dict):
            raise InferenceConfigurationError(
                "Inference configuration must contain an 'inference' mapping"
            )

        self._config = inference
        self._execution_enabled = (
            bool(inference.get("execution_enabled", False))
            if execution_enabled is None
            else bool(execution_enabled)
        )
        self._model_factory = model_factory
        self._image_loader = image_loader
        self._model: Any | None = None

        runtime = self._required_mapping("runtime")
        model_config = self._required_mapping("model")
        device = self._required_mapping("device")
        preprocessing = self._required_mapping("preprocessing")
        detection = self._required_mapping("detection")
        input_config = self._required_mapping("input")

        self.runtime_id = str(runtime.get("id", ""))
        self.expected_ultralytics = str(runtime.get("ultralytics", ""))
        self.expected_torch = str(runtime.get("torch", ""))

        model_path = Path(str(model_config.get("path", ""))).expanduser()
        self.model_path = (
            model_path if model_path.is_absolute() else PROJECT_ROOT / model_path
        )
        self.expected_model_sha256 = str(model_config.get("sha256", "")).lower()
        self.expected_model_size = int(model_config.get("size_bytes", -1))
        if bool(model_config.get("auto_download", True)):
            raise InferenceConfigurationError(
                "Frozen inference configuration must disable model downloads"
            )

        self.device_policy = str(device.get("policy", ""))
        self.device = str(device.get("device", ""))
        if (
            self.device_policy != "cpu_only"
            or self.device != "cpu"
            or bool(device.get("auto", True))
            or bool(device.get("cuda_authorized", True))
        ):
            raise InferenceConfigurationError(
                "Frozen inference configuration must use the CPU-only device policy"
            )

        self.imgsz = int(preprocessing.get("imgsz", 0))
        self.conf_threshold = float(detection.get("conf_threshold", -1.0))
        self.iou_threshold = float(detection.get("iou_threshold", -1.0))
        self.max_det = int(detection.get("max_det", 0))
        self.class_filter = tuple(int(item) for item in detection.get("class_filter", ()))
        self.class_names = tuple(str(item) for item in detection.get("class_names", ()))
        self.image_extensions = tuple(
            str(item).lower() for item in input_config.get("image_extensions", ())
        )

        self._validate_config_values()

    def _required_mapping(self, key: str) -> dict[str, Any]:
        value = self._config.get(key)
        if not isinstance(value, dict):
            raise InferenceConfigurationError(
                f"Inference configuration requires a '{key}' mapping"
            )
        return value

    def _validate_config_values(self) -> None:
        if not self.runtime_id:
            raise InferenceConfigurationError("Runtime ID is required")
        if self.expected_model_size <= 0:
            raise InferenceConfigurationError("Checkpoint size must be positive")
        if len(self.expected_model_sha256) != 64:
            raise InferenceConfigurationError("Checkpoint SHA256 is invalid")
        if self.imgsz <= 0:
            raise InferenceConfigurationError("imgsz must be positive")
        if not 0.0 <= self.conf_threshold <= 1.0:
            raise InferenceConfigurationError("conf_threshold must be in [0, 1]")
        if not 0.0 <= self.iou_threshold <= 1.0:
            raise InferenceConfigurationError("iou_threshold must be in [0, 1]")
        if self.max_det <= 0:
            raise InferenceConfigurationError("max_det must be positive")
        if not self.class_filter:
            raise InferenceConfigurationError("class_filter cannot be empty")
        if len(self.class_names) != len(self.class_filter):
            raise InferenceConfigurationError(
                "class_names must match the class_filter length"
            )
        if not self.image_extensions:
            raise InferenceConfigurationError("image_extensions cannot be empty")

    def detect_image(self, image_path: str | Path) -> list[DetectionResult]:
        """Run detection on one image and return project schemas only."""

        self._ensure_execution_enabled()
        path = Path(image_path).expanduser().resolve()
        image = self._load_image(path)
        return self.detect_frame(
            image,
            frame_id=0,
            timestamp=0.0,
            source=f"image:{path.name}",
        )

    def detect_frame(
        self,
        image: Any,
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> list[DetectionResult]:
        """Run detection on one decoded frame using the frozen image policy."""

        self._ensure_execution_enabled()
        if image is None:
            raise InvalidImageError("Frame image cannot be None")
        self._verify_checkpoint()
        model = self._load_model()

        results = model.predict(
            source=image,
            imgsz=self.imgsz,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            device=self.device,
            classes=list(self.class_filter),
            max_det=self.max_det,
            verbose=False,
        )
        return self._parse_results(
            results,
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
        )

    def _ensure_execution_enabled(self) -> None:
        if not self._execution_enabled:
            raise InferenceExecutionDisabledError(
                "Image inference is disabled by configs/inference.yaml"
            )

    def _load_image(self, path: Path) -> Any:
        if self._image_loader is not None:
            return self._image_loader(path)
        try:
            from PIL import Image
        except ImportError as exc:
            raise InferenceRuntimeError("Pillow is not installed") from exc

        try:
            with Image.open(path) as image:
                return image.convert("RGB")
        except Exception as exc:
            raise InvalidImageError(f"Could not decode image: {path.name}") from exc

    def _verify_checkpoint(self) -> None:
        if not self.model_path.is_file():
            raise CheckpointIntegrityError(
                f"Frozen checkpoint does not exist: {self.model_path}"
            )
        actual_size = self.model_path.stat().st_size
        if actual_size != self.expected_model_size:
            raise CheckpointIntegrityError(
                "Checkpoint size mismatch: "
                f"expected {self.expected_model_size}, observed {actual_size}"
            )

        digest = hashlib.sha256()
        with self.model_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        actual_sha256 = digest.hexdigest()
        if actual_sha256 != self.expected_model_sha256:
            raise CheckpointIntegrityError(
                "Checkpoint SHA256 mismatch: "
                f"expected {self.expected_model_sha256}, observed {actual_sha256}"
            )

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        self._validate_runtime_versions()
        if self._model_factory is not None:
            model = self._model_factory(self.model_path)
        else:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise InferenceRuntimeError(
                    "Ultralytics is not installed in the frozen runtime"
                ) from exc
            try:
                model = YOLO(str(self.model_path), task="detect")
            except Exception as exc:
                raise InferenceRuntimeError(
                    f"Could not load frozen checkpoint: {self.model_path.name}"
                ) from exc

        self._validate_model_class_names(model)
        self._model = model
        return model

    def _validate_runtime_versions(self) -> None:
        if self._model_factory is not None:
            return
        for package, expected in (
            ("torch", self.expected_torch),
            ("ultralytics", self.expected_ultralytics),
        ):
            if package == "torch":
                try:
                    import torch
                except ImportError as exc:
                    raise InferenceRuntimeError(
                        "torch is not installed in the frozen runtime"
                    ) from exc
                observed = str(torch.__version__)
            else:
                try:
                    observed = version(package)
                except PackageNotFoundError as exc:
                    raise InferenceRuntimeError(
                        f"{package} is not installed in the frozen runtime"
                    ) from exc
            if observed != expected:
                raise InferenceRuntimeError(
                    f"{package} version mismatch: expected {expected}, observed {observed}"
                )

    def _validate_model_class_names(self, model: Any) -> None:
        names = getattr(model, "names", None)
        if names is None:
            raise InferenceConfigurationError("Loaded model does not expose class names")

        if isinstance(names, dict):
            try:
                observed = [str(names[index]) for index in self.class_filter]
            except KeyError as exc:
                raise InferenceConfigurationError(
                    "Loaded model is missing a filtered class index"
                ) from exc
        else:
            try:
                observed = [str(names[index]) for index in self.class_filter]
            except (IndexError, TypeError) as exc:
                raise InferenceConfigurationError(
                    "Loaded model class names are invalid"
                ) from exc

        if observed != list(self.class_names):
            raise InferenceConfigurationError(
                "Loaded model class order does not match the frozen class filter"
            )

    def _parse_results(
        self,
        results: Iterable[Any],
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> list[DetectionResult]:
        parsed: list[DetectionResult] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None or len(boxes) == 0:
                continue

            xyxy_values = self._as_list(boxes.xyxy, "xyxy")
            class_values = self._as_list(boxes.cls, "cls")
            confidence_values = self._as_list(boxes.conf, "conf")
            if not (
                len(xyxy_values) == len(class_values) == len(confidence_values)
            ):
                raise InferenceRuntimeError(
                    "Detector returned mismatched box, class and confidence counts"
                )

            for coordinates, raw_class_id, confidence in zip(
                xyxy_values, class_values, confidence_values
            ):
                if len(coordinates) != 4:
                    raise InferenceRuntimeError(
                        "Detector returned a box without four coordinates"
                    )
                class_id = int(raw_class_id)
                if class_id not in self.class_filter:
                    continue
                class_position = self.class_filter.index(class_id)
                bbox = BoundingBox(
                    float(coordinates[0]),
                    float(coordinates[1]),
                    float(coordinates[2]),
                    float(coordinates[3]),
                )
                parsed.append(
                    DetectionResult(
                        frame_id=frame_id,
                        timestamp=timestamp,
                        source=source,
                        detection=Detection(
                            bbox=bbox,
                            class_id=class_id,
                            class_name=self.class_names[class_position],
                            confidence=float(confidence),
                        ),
                    )
                )
        return parsed

    @staticmethod
    def _as_list(values: Any, field_name: str) -> list[Any]:
        if hasattr(values, "tolist"):
            values = values.tolist()
        if not isinstance(values, list):
            raise InferenceRuntimeError(
                f"Detector returned an invalid {field_name} payload"
            )
        return values
