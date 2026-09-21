"""Local LLM fallback boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class TemplateFallback:
    def generate(self, analytics: dict[str, Any]) -> str:
        raise NotImplementedError(
            "Local template fallback belongs to Phase 8 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
