"""Violation video storage boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class VideoStorage:
    def save_clip(self, frames: list[Any], destination: str | Path) -> Path:
        raise NotImplementedError(
            "Violation video evidence storage belongs to Extension E-005 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
