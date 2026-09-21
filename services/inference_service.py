"""Inference service boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class InferenceService:
    def infer_image(self, source: Any) -> None:
        raise NotImplementedError(
            "Image inference belongs to Phase 4 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )

    def infer_video(self, source: Any) -> None:
        raise NotImplementedError(
            "Video inference belongs to Phase 4 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )

    def infer_stream(self, source: Any) -> None:
        raise NotImplementedError(
            "Camera and RTSP inference belong to Phase 4 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
