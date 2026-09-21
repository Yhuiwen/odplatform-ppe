"""LLM report service boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class ReportService:
    def generate(self, analytics: dict[str, Any]) -> str:
        raise NotImplementedError(
            "LLM report generation and local fallback belong to Phase 8 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
