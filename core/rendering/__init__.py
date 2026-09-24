"""Deterministic rendering boundaries for project-owned media outputs."""

from core.rendering.annotated_frame import (
    AnnotationSpec,
    AnnotatedFrameRenderer,
    AnnotatedRenderingError,
    FrameDrawingBackend,
    OpenCVFrameDrawingBackend,
)

__all__ = [
    "AnnotationSpec",
    "AnnotatedFrameRenderer",
    "AnnotatedRenderingError",
    "FrameDrawingBackend",
    "OpenCVFrameDrawingBackend",
]
