"""SQLite database boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from pathlib import Path


class Database:
    def connect(self, path: str | Path) -> None:
        raise NotImplementedError(
            "SQLite business persistence belongs to Phase 7 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
