"""Sequential MP4 inference service built on the frozen image detector."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.inference.detector import (
    InferenceError,
    InferenceExecutionDisabledError,
)
from core.schemas.video import (
    FrameInferenceResult,
    VideoInferenceResult,
)
from core.video.reader import VideoReader
from services.inference_service import InferenceService


class VideoInferenceService:
    """Read one local MP4 and reuse ``InferenceService`` for every frame."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        inference_service: InferenceService | None = None,
        reader_factory: type[VideoReader] = VideoReader,
    ) -> None:
        self.inference_service = inference_service or InferenceService(
            config_path=config_path
        )
        self.reader_factory = reader_factory
        self.execution_enabled = bool(
            getattr(self.inference_service, "execution_enabled", False)
        )

    def infer_video(self, source: str | Path) -> VideoInferenceResult:
        """Return ordered structured frame results without framework objects."""

        path = VideoReader.validate_source(source)
        if not self.execution_enabled:
            raise InferenceExecutionDisabledError(
                "Video inference is disabled by configs/inference.yaml"
            )

        with self.reader_factory(path) as reader:
            metadata = reader.metadata
            if metadata is None:
                raise InferenceError("Video reader did not expose metadata")

            frame_results: list[FrameInferenceResult] = []
            for frame in reader:
                detections = self.inference_service.infer_frame(
                    frame,
                    source=metadata.source,
                )
                self._validate_detection_context(
                    frame.frame_id,
                    frame.timestamp,
                    metadata.source,
                    detections,
                )
                frame_results.append(
                    FrameInferenceResult(
                        frame_id=frame.frame_id,
                        timestamp=frame.timestamp,
                        detections=tuple(detections),
                    )
                )

        return VideoInferenceResult(
            metadata=metadata,
            frames=tuple(frame_results),
        )

    @staticmethod
    def _validate_detection_context(
        frame_id: int,
        timestamp: float,
        source: str,
        detections: Any,
    ) -> None:
        for detection in detections:
            if (
                detection.frame_id != frame_id
                or detection.timestamp != timestamp
                or detection.source != source
            ):
                raise InferenceError(
                    "Detector returned a detection for the wrong video frame"
                )
