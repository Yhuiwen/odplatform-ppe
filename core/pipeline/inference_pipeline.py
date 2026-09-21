"""Inference pipeline boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class InferencePipeline:
    """Contract for future image, video, and stream processing."""

    def run(self, source: Any) -> Any:
        raise NotImplementedError(
            "Inference pipeline behavior belongs to Phase 4 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
