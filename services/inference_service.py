"""Application service for Phase 4 inference."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.inference.detector import (
    ImageNotFoundError,
    InferenceConfigurationError,
    InferenceExecutionDisabledError,
    InvalidImageError,
    InvalidImageFormatError,
    YOLODetector,
)
from core.schemas.detection import DetectionResult
from core.schemas.video import FrameData
from utils.config_loader import load_config


class InferenceService:
    """Validate one image input and delegate detection to ``YOLODetector``."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        execution_enabled: bool | None = None,
        detector: YOLODetector | None = None,
    ) -> None:
        config = load_config(config_path or "inference")
        inference = config.get("inference")
        if not isinstance(inference, dict):
            raise InferenceConfigurationError(
                "Inference configuration must contain an 'inference' mapping"
            )

        input_config = inference.get("input")
        if not isinstance(input_config, dict):
            raise InferenceConfigurationError(
                "Inference configuration requires an 'input' mapping"
            )
        self.image_extensions = tuple(
            str(item).lower() for item in input_config.get("image_extensions", ())
        )
        self.execution_enabled = (
            bool(inference.get("execution_enabled", False))
            if execution_enabled is None
            else bool(execution_enabled)
        )
        self.detector = detector or YOLODetector(
            config_path=config_path,
            execution_enabled=execution_enabled,
        )

    def infer_image(self, source: str | Path) -> list[DetectionResult]:
        """Return structured project schemas; never return framework results."""

        image_path = self._validate_image_path(source)
        if not self.execution_enabled:
            raise InferenceExecutionDisabledError(
                "Image inference is disabled by configs/inference.yaml"
            )
        return self.detector.detect_image(image_path)

    def infer_frame(
        self,
        frame: FrameData,
        *,
        source: str,
    ) -> list[DetectionResult]:
        """Run one decoded frame through the existing image detector contract."""

        if not self.execution_enabled:
            raise InferenceExecutionDisabledError(
                "Inference is disabled by configs/inference.yaml"
            )
        return self.detector.detect_frame(
            frame.image,
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            source=source,
        )

    def _validate_image_path(self, source: str | Path) -> Path:
        if not isinstance(source, (str, Path)):
            raise InvalidImageError("Image source must be a filesystem path")

        path = Path(source).expanduser()
        if not path.exists():
            raise ImageNotFoundError(f"Image does not exist: {path}")
        if not path.is_file():
            raise InvalidImageError(f"Image source is not a file: {path}")
        if path.suffix.lower() not in self.image_extensions:
            raise InvalidImageFormatError(
                f"Unsupported image format: {path.suffix or '<none>'}"
            )
        return path.resolve()

    def infer_video(self, source: Any) -> None:
        raise NotImplementedError(
            "Video inference belongs to Phase 4B-2 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )

    def infer_stream(self, source: Any) -> None:
        raise NotImplementedError(
            "Camera and RTSP inference belong to a later Phase 4 subphase "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
