"""Application orchestration for Phase 6 compliance evaluation."""

from __future__ import annotations

from pathlib import Path

from core.adapters.association_adapter import AssociationAdapter
from core.rules.compliance_engine import ComplianceEngine
from core.schemas.association import AssociationResult
from core.schemas.compliance import ComplianceResult

__all__ = ["ComplianceService"]


class ComplianceService:
    """Adapt one association result and delegate rules to the core engine."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        execution_enabled: bool | None = None,
        adapter: AssociationAdapter | None = None,
        engine: ComplianceEngine | None = None,
    ) -> None:
        self.adapter = adapter or AssociationAdapter()
        self.engine = engine or ComplianceEngine(
            config_path,
            execution_enabled=execution_enabled,
        )

    def evaluate(self, result: AssociationResult) -> ComplianceResult:
        """Return one frame of model-independent compliance findings."""

        compliance_input = self.adapter.adapt(result)
        return self.engine.evaluate(compliance_input)
