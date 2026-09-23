"""Adapt Phase 5 association output into the Phase 6 compliance contract."""

from __future__ import annotations

from core.schemas.association import AssociationResult
from core.schemas.compliance import ComplianceInput

__all__ = ["AssociationAdapter", "AssociationAdapterError"]


class AssociationAdapterError(ValueError):
    """Raised when an input cannot be adapted without losing identity."""


class AssociationAdapter:
    """Convert one Phase 5 frame result without mutating its contents."""

    def adapt(self, result: AssociationResult) -> ComplianceInput:
        """Return a validated, immutable ``ComplianceInput`` copy."""

        if not isinstance(result, AssociationResult):
            raise AssociationAdapterError(
                "AssociationAdapter input must be an AssociationResult"
            )
        try:
            return ComplianceInput.from_association_result(result)
        except (TypeError, ValueError) as exc:
            raise AssociationAdapterError(
                "AssociationResult is not valid for compliance input"
            ) from exc
