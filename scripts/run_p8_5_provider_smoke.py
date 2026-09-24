"""Run at most one real Phase 8 provider smoke request.

The script requires explicit endpoint, model and API-key environment
configuration. It never writes credentials or raw provider output.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus
from core.schemas.safety import (
    SafetyAnalyticsResult,
    SafetyAnalyticsQuery,
    UnavailableField,
)
from infra.llm.chat_transport import OpenAICompatibleChatTransport
from infra.llm.config import LLMConfigurationError, LLMProviderConfig
from infra.llm.llm_client import SafetyLLMClient
from infra.llm.request_builder import ProviderRequestBuilder
from services.report_service import ReportService
from services.safety_context_builder import SafetyContextBuilder


@dataclass(frozen=True, slots=True)
class SmokeReport:
    status: str
    reason: str
    provider_ref: str | None = None
    model_ref: str | None = None
    generation_path: str | None = None
    degraded: bool | None = None
    grounding_status: str | None = None
    safe_error_code: str | None = None
    schema_diagnostics: list[dict[str, object]] | None = None
    schema_diagnostics_truncated: bool | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "provider_ref": self.provider_ref,
            "model_ref": self.model_ref,
            "generation_path": self.generation_path,
            "degraded": self.degraded,
            "grounding_status": self.grounding_status,
            "safe_error_code": self.safe_error_code,
            "schema_diagnostics": self.schema_diagnostics,
            "schema_diagnostics_truncated": (
                self.schema_diagnostics_truncated
            ),
        }


def _empty_context():
    query = SafetyAnalyticsQuery(
        start_at="2026-09-24T00:00:00Z",
        end_at="2026-09-24T23:59:59Z",
    )
    analytics = SafetyAnalyticsResult(
        query=query,
        facts=(),
        counts_by_type=tuple(
            (event_type, 0) for event_type in ComplianceEventType
        ),
        counts_by_status=tuple((status, 0) for status in EventStatus),
        counts_by_track=(),
        counts_by_day=(),
        counts_by_source_ref=(),
        first_occurrence=None,
        last_occurrence=None,
        evidence_available_count=0,
        evidence_missing_count=0,
        unavailable_fields=(
            UnavailableField(
                field="metrics.violation_duration",
                reason_code="NO_PERSISTED_DURATION_FIELD",
                reason="No persisted violation-duration field exists.",
            ),
        ),
    )
    return SafetyContextBuilder(
        clock=lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)
    ).build(analytics)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one Phase 8 provider smoke validation."
    )
    parser.add_argument("--config", default="llm.yaml")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Allow exactly one real provider call.",
    )
    args = parser.parse_args(argv)

    try:
        config = LLMProviderConfig.from_file(args.config)
    except LLMConfigurationError as exc:
        print(
            json.dumps(
                SmokeReport(
                    status="NOT_EXECUTED",
                    reason=str(exc),
                ).to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0

    if not args.execute:
        print(
            json.dumps(
                SmokeReport(
                    status="NOT_EXECUTED",
                    reason="explicit --execute flag was not provided",
                    provider_ref=config.provider_ref,
                    model_ref=config.model_ref,
                ).to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0

    client = SafetyLLMClient(
        transport=OpenAICompatibleChatTransport(config=config),
        request_builder=ProviderRequestBuilder(
            provider_ref=config.provider_ref,
            model_ref=config.model_ref,
            timeout_seconds=config.timeout_seconds,
            maximum_response_bytes=config.maximum_response_bytes,
        ),
    )
    result = ReportService().generate_provider_or_fallback(
        _empty_context(),
        client,
    )
    diagnostics = (
        None
        if result.safe_error is None
        or result.safe_error.schema_diagnostics is None
        else [
            item.to_dict()
            for item in result.safe_error.schema_diagnostics.diagnostics
        ]
    )
    diagnostics_truncated = (
        None
        if result.safe_error is None
        or result.safe_error.schema_diagnostics is None
        else result.safe_error.schema_diagnostics.truncated
    )
    print(
        json.dumps(
            SmokeReport(
                status=result.status.value,
                reason=(
                    "real provider call completed"
                    if result.status.value == "PROVIDER_VALIDATED"
                    else "provider path used safe fallback"
                ),
                provider_ref=(
                    None
                    if result.provider_metadata is None
                    else result.provider_metadata.provider_ref
                ),
                model_ref=(
                    None
                    if result.provider_metadata is None
                    else result.provider_metadata.model_ref
                ),
                generation_path=result.generation_path.value,
                degraded=result.degraded,
                grounding_status=(
                    None
                    if result.grounding_status is None
                    else result.grounding_status.value
                ),
                safe_error_code=(
                    None
                    if result.safe_error is None
                    else result.safe_error.code
                ),
                schema_diagnostics=diagnostics,
                schema_diagnostics_truncated=diagnostics_truncated,
            ).to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.report is not None else 1


if __name__ == "__main__":
    sys.exit(main())
