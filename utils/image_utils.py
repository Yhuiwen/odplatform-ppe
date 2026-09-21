"""Image helpers are intentionally deferred until the inference phase.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def read_image(path: str | Path) -> Any:
    """Read an image using the Phase 4 inference stack."""

    raise NotImplementedError(
        "Image reading and preprocessing belong to Phase 4 "
        "(NOT IMPLEMENTED - FUTURE PHASE)"
    )
