"""Compliance service boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class ComplianceService:
    def evaluate(self, associations: list[Any]) -> list[Any]:
        raise NotImplementedError(
            "PPE compliance behavior belongs to Phase 6 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
