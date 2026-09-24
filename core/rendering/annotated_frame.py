"""Pure frame-annotation contract for the M-007 demo video tool."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from core.schemas.detection import DetectionResult
from core.schemas.video import FrameData

__all__ = [
    "AnnotationSpec",
    "AnnotatedFrameRenderer",
    "AnnotatedRenderingError",
    "FrameDrawingBackend",
    "OpenCVFrameDrawingBackend",
]


class AnnotatedRenderingError(RuntimeError):
    """Raised when a frame cannot be rendered under the frozen contract."""

    code = "annotated_rendering_failed"


@dataclass(frozen=True, slots=True)
class AnnotationSpec:
    """One deterministic annotation ready for a drawing backend."""

    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]
    color: tuple[int, int, int]
    label: str


class FrameDrawingBackend(Protocol):
    """Small drawing surface kept injectable for deterministic tests."""

    def copy(self, image: Any) -> Any:
        """Return an independent frame image."""

    def rectangle(
        self,
        image: Any,
        bbox: tuple[int, int, int, int],
        color: tuple[int, int, int],
    ) -> None:
        """Draw one clipped axis-aligned box."""

    def label(
        self,
        image: Any,
        text: str,
        origin: tuple[int, int],
        color: tuple[int, int, int],
        image_width: int,
        image_height: int,
    ) -> None:
        """Draw one label with a solid background."""


class OpenCVFrameDrawingBackend:
    """OpenCV-backed drawing implementation loaded only when rendering runs."""

    _FONT = None

    def _cv2(self) -> Any:
        try:
            import cv2
        except ImportError as exc:
            raise AnnotatedRenderingError(
                "OpenCV is not installed in the frozen rendering runtime"
            ) from exc
        if self._FONT is None:
            self._FONT = cv2.FONT_HERSHEY_SIMPLEX
        return cv2

    def copy(self, image: Any) -> Any:
        if image is None or not hasattr(image, "copy"):
            raise AnnotatedRenderingError("Frame image must support copying")
        return image.copy()

    def rectangle(
        self,
        image: Any,
        bbox: tuple[int, int, int, int],
        color: tuple[int, int, int],
    ) -> None:
        cv2 = self._cv2()
        x1, y1, x2, y2 = bbox
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

    def label(
        self,
        image: Any,
        text: str,
        origin: tuple[int, int],
        color: tuple[int, int, int],
        image_width: int,
        image_height: int,
    ) -> None:
        cv2 = self._cv2()
        x, y = origin
        (text_width, text_height), baseline = cv2.getTextSize(
            text,
            self._FONT,
            0.5,
            1,
        )
        label_height = text_height + baseline + 6
        top = max(0, y - label_height)
        bottom = min(image_height - 1, top + label_height)
        right = min(image_width - 1, max(x + text_width + 6, x + 1))
        cv2.rectangle(image, (x, top), (right, bottom), color, -1)
        cv2.putText(
            image,
            text,
            (x + 3, bottom - baseline - 2),
            self._FONT,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )


DEFAULT_CLASS_COLORS: tuple[tuple[int, int, int], ...] = (
    (0, 165, 255),
    (0, 200, 80),
    (0, 0, 255),
    (255, 200, 0),
    (255, 0, 200),
)


class AnnotatedFrameRenderer:
    """Draw current-frame detections without tracking or event overlays."""

    def __init__(
        self,
        class_names: Sequence[str],
        *,
        colors: Mapping[int, tuple[int, int, int]] | None = None,
        drawing_backend: FrameDrawingBackend | None = None,
    ) -> None:
        if isinstance(class_names, (str, bytes)):
            raise AnnotatedRenderingError("class_names must be a sequence")
        normalized_names = tuple(str(name).strip() for name in class_names)
        if not normalized_names or any(not name for name in normalized_names):
            raise AnnotatedRenderingError("class_names cannot be empty")
        self.class_names = normalized_names
        self.colors = self._normalize_colors(colors)
        self.drawing_backend = drawing_backend or OpenCVFrameDrawingBackend()

    def annotation_plan(
        self,
        detections: Sequence[DetectionResult],
        *,
        width: int,
        height: int,
    ) -> tuple[AnnotationSpec, ...]:
        """Return clipped deterministic annotations in detector order."""

        if width <= 0 or height <= 0:
            raise AnnotatedRenderingError("Frame dimensions must be positive")

        plan: list[AnnotationSpec] = []
        for detection in detections:
            if not isinstance(detection, DetectionResult):
                raise AnnotatedRenderingError(
                    "detections must contain DetectionResult objects"
                )
            class_id = detection.class_id
            if (
                isinstance(class_id, bool)
                or not isinstance(class_id, int)
                or class_id < 0
                or class_id >= len(self.class_names)
            ):
                raise AnnotatedRenderingError(
                    f"Detection class ID is outside the frozen class order: {class_id}"
                )
            expected_name = self.class_names[class_id]
            if detection.class_name != expected_name:
                raise AnnotatedRenderingError(
                    "Detection class name does not match the frozen class order"
                )

            bbox = self._clip_bbox(
                detection.bbox.as_tuple(),
                width=width,
                height=height,
            )
            if bbox is None:
                continue
            plan.append(
                AnnotationSpec(
                    class_id=class_id,
                    class_name=expected_name,
                    confidence=detection.confidence,
                    bbox=bbox,
                    color=self.colors[class_id],
                    label=f"{expected_name} {detection.confidence:.2f}",
                )
            )
        return tuple(plan)

    def render(
        self,
        frame: FrameData,
        detections: Sequence[DetectionResult],
    ) -> Any:
        """Return one annotated copy of ``frame.image``."""

        if not isinstance(frame, FrameData):
            raise AnnotatedRenderingError("frame must be FrameData")
        shape = getattr(frame.image, "shape", None)
        if shape is None or len(shape) < 2:
            raise AnnotatedRenderingError(
                "Frame image must expose a height/width shape"
            )
        height = int(shape[0])
        width = int(shape[1])
        plan = self.annotation_plan(detections, width=width, height=height)

        try:
            rendered = self.drawing_backend.copy(frame.image)
        except AnnotatedRenderingError:
            raise
        except Exception as exc:
            raise AnnotatedRenderingError(
                "Could not copy the source frame for rendering"
            ) from exc

        try:
            for annotation in plan:
                self.drawing_backend.rectangle(
                    rendered,
                    annotation.bbox,
                    annotation.color,
                )
                self.drawing_backend.label(
                    rendered,
                    annotation.label,
                    (annotation.bbox[0], annotation.bbox[1]),
                    annotation.color,
                    width,
                    height,
                )
        except AnnotatedRenderingError:
            raise
        except Exception as exc:
            raise AnnotatedRenderingError(
                "Drawing backend failed while annotating a frame"
            ) from exc

        rendered_shape = getattr(rendered, "shape", None)
        if rendered_shape is None or tuple(rendered_shape[:2]) != (height, width):
            raise AnnotatedRenderingError(
                "Rendered frame dimensions do not match the source frame"
            )
        return rendered

    def _normalize_colors(
        self,
        colors: Mapping[int, tuple[int, int, int]] | None,
    ) -> dict[int, tuple[int, int, int]]:
        normalized: dict[int, tuple[int, int, int]] = {}
        for class_id in range(len(self.class_names)):
            raw = (
                colors[class_id]
                if colors is not None and class_id in colors
                else DEFAULT_CLASS_COLORS[class_id % len(DEFAULT_CLASS_COLORS)]
            )
            if (
                not isinstance(raw, (tuple, list))
                or len(raw) != 3
                or any(
                    isinstance(channel, bool)
                    or not isinstance(channel, int)
                    or not 0 <= channel <= 255
                    for channel in raw
                )
            ):
                raise AnnotatedRenderingError(
                    "Class colors must be BGR integer triples in [0, 255]"
                )
            normalized[class_id] = (int(raw[0]), int(raw[1]), int(raw[2]))
        return normalized

    @staticmethod
    def _clip_bbox(
        bbox: tuple[float, float, float, float],
        *,
        width: int,
        height: int,
    ) -> tuple[int, int, int, int] | None:
        x1, y1, x2, y2 = (float(value) for value in bbox)
        if not all(math.isfinite(value) for value in (x1, y1, x2, y2)):
            raise AnnotatedRenderingError("Detection coordinates must be finite")

        clipped = (
            max(0, min(width - 1, int(math.floor(x1)))),
            max(0, min(height - 1, int(math.floor(y1)))),
            max(0, min(width - 1, int(math.ceil(x2)))),
            max(0, min(height - 1, int(math.ceil(y2)))),
        )
        if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
            return None
        return clipped
