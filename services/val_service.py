"""Model validation service boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class ValService:
    def evaluate(self, config: dict[str, Any]) -> None:
        raise NotImplementedError(
            "Model evaluation belongs to Phase 3 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
