"""Violation snapshot storage boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SnapshotStorage:
    def save(self, image: Any, destination: str | Path) -> Path:
        raise NotImplementedError(
            "Violation snapshot evidence storage belongs to Phase 7 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
