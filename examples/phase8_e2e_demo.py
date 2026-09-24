"""Deterministic Phase 8 Agent end-to-end demo and evidence generator."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.agent.tool_registry import ToolRegistry
from core.schemas.agent_api import AgentApiOperation, AgentApiRequest
from core.schemas.agent import AgentTool
from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus, SnapshotReference, StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from services.agent_api_service import AgentApplicationService
from services.agent_audit_service import AgentAuditService
from services.agent_service import AgentService
from services.agent_tool_service import AgentToolService
from services.event_query_service import EventQueryService
from services.llm_planner_adapter import LLMPlannerAdapter
from services.report_service import ReportService
from services.safety_analytics_service import SafetyAnalyticsService
from services.safety_context_builder import SafetyContextBuilder
from utils.paths import PROJECT_ROOT
from web.agent_support import AgentWebAdapter, LocalDemoIdentityProvider

__all__ = [
    "DEMO_SCHEMA_VERSION",
    "EXPECTED_FIXTURE_PATH",
    "INPUT_FIXTURE_PATH",
    "load_demo_input",
    "run_demo",
]

DEMO_SCHEMA_VERSION = "phase8-e2e-demo-v1"
INPUT_FIXTURE_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "phase8_e2e_demo_input.json"
)
EXPECTED_FIXTURE_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "phase8_e2e_demo_expected.json"
)
_FIXED_TIMESTAMP = datetime(2026, 9, 24, 18, 0, 0, tzinfo=timezone.utc)


def _fixed_clock() -> datetime:
    return _FIXED_TIMESTAMP


def load_demo_input(path: str | Path = INPUT_FIXTURE_PATH) -> dict[str, Any]:
    """Load and validate the bounded deterministic demo input fixture."""

    fixture_path = Path(path)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("demo input must be a JSON object")
    if payload.get("schema_version") != "phase8-e2e-demo-input-v1":
        raise ValueError("unsupported demo input schema_version")
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("demo input must contain scenarios")
    return payload


def _seed_database(
    payload: Mapping[str, Any],
) -> tuple[Database, EventQueryService, str]:
    database = Database(":memory:")
    event_data = payload["event"]
    snapshot_data = payload["snapshot"]
    if not isinstance(event_data, Mapping) or not isinstance(
        snapshot_data,
        Mapping,
    ):
        raise ValueError("demo event and snapshot must be mappings")

    event = StoredEvent(
        id=event_data["id"],
        timestamp=event_data["timestamp"],
        track_id=event_data["track_id"],
        type=ComplianceEventType(event_data["type"]),
        confidence=event_data["confidence"],
        source_timestamp=event_data["source_timestamp"],
        source=event_data["source"],
        snapshot=event_data["snapshot"],
        status=EventStatus(event_data["status"]),
        frame_id=event_data.get("frame_id"),
        bbox=event_data.get("bbox"),
    )
    snapshot = SnapshotReference(
        snapshot_id=snapshot_data["snapshot_id"],
        event_id=snapshot_data["event_id"],
        relative_path=snapshot_data["relative_path"],
        sha256=snapshot_data["sha256"],
        width=snapshot_data["width"],
        height=snapshot_data["height"],
        mime_type=snapshot_data["mime_type"],
        captured_at=snapshot_data["captured_at"],
    )
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    event_repository.insert(event)
    snapshot_repository.insert(snapshot)
    return (
        database,
        EventQueryService(event_repository, snapshot_repository),
        event.id,
    )


def _build_adapter(
    query_service: EventQueryService,
) -> tuple[AgentWebAdapter, AgentAuditService]:
    audit_service = AgentAuditService(clock=_fixed_clock)
    tool_service = AgentToolService(
        event_query_service=query_service,
        safety_analytics_service=SafetyAnalyticsService(query_service),
        context_builder=SafetyContextBuilder(clock=_fixed_clock),
        report_service=ReportService(),
        provider_client=None,
    )
    registry = ToolRegistry(
        tuple(
            AgentTool(
                tool_service.registry.resolve(tool_name).descriptor,
                tool_service.registry.resolve(tool_name).handler,
            )
            for tool_name in tool_service.registry.tool_names
        ),
        monotonic=lambda: 0.0,
    )
    planner_adapter = LLMPlannerAdapter(
        registry,
        candidate_client=None,
        audit_service=audit_service,
    )
    application_service = AgentApplicationService(
        AgentService(planner_adapter),
        LocalDemoIdentityProvider(),
    )
    return AgentWebAdapter(application_service), audit_service


def _execute_scenarios(
    adapter: AgentWebAdapter,
    scenarios: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, ...], dict[str, dict[str, Any]]]:
    order: list[str] = []
    projections: dict[str, dict[str, Any]] = {}
    for scenario in scenarios:
        if not isinstance(scenario, Mapping):
            raise ValueError("each demo scenario must be a mapping")
        name = scenario.get("name")
        request_id = scenario.get("request_id")
        if not isinstance(name, str) or not name:
            raise ValueError("each demo scenario requires a name")
        if name in projections:
            raise ValueError("demo scenario names must be unique")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("each demo scenario requires a request_id")

        request = AgentApiRequest(
            request_id=request_id,
            operation=AgentApiOperation(scenario.get("operation")),
            question=scenario.get("question"),
            requested_period=scenario.get("requested_period"),
            filters=scenario.get("filters"),
        )
        projections[name] = adapter.submit(request).to_dict()
        order.append(name)
    return tuple(order), projections


def _source_of_truth(
    query_service: EventQueryService,
    event_id: str,
) -> dict[str, Any]:
    event = query_service.get_event(event_id)
    snapshot = query_service.snapshot_repository.get_by_event(event_id)
    return {
        "event": None if event is None else event.to_dict(),
        "snapshot": None if snapshot is None else snapshot.to_dict(),
    }


def _stable_audit_projection(event: Any) -> dict[str, Any]:
    projected = event.to_dict()
    metadata = dict(projected["safe_metadata"])
    duration_ms = metadata.pop("duration_ms", None)
    projected["safe_metadata"] = metadata
    projected["duration_recorded"] = isinstance(
        duration_ms,
        (int, float),
    )
    return projected


def run_demo(
    *,
    input_path: str | Path = INPUT_FIXTURE_PATH,
) -> dict[str, Any]:
    """Execute the provider-disabled deterministic Phase 8 E2E scenario."""

    payload = load_demo_input(input_path)
    database, query_service, event_id = _seed_database(payload)
    try:
        adapter, audit_service = _build_adapter(query_service)
        before = _source_of_truth(query_service, event_id)
        order, projections = _execute_scenarios(
            adapter,
            payload["scenarios"],
        )
        after = _source_of_truth(query_service, event_id)
        audit_events = [
            _stable_audit_projection(event)
            for event in audit_service.events()
        ]
        report_projection = projections["report"]
        report_status = report_projection["safe_status"]
        refused_projection = projections["refused"]
        return {
            "schema_version": DEMO_SCHEMA_VERSION,
            "scenario_order": list(order),
            "source_event_id": event_id,
            "projections": projections,
            "audit_events": audit_events,
            "invariants": {
                "provider_client": "DISABLED",
                "model_loaded": False,
                "report_generation_path": "TEMPLATE_FALLBACK",
                "report_degraded": True,
                "report_grounded": "grounding=valid" in report_status,
                "refused_result_payload_empty": (
                    refused_projection["summary"] == []
                    and refused_projection["evidence_references"] == []
                    and refused_projection["recommendations"] == []
                ),
                "source_of_truth_unchanged": before == after,
            },
            "source_of_truth": after,
        }
    finally:
        database.close()


def _render(result: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(result),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic Phase 8 Agent E2E demo."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FIXTURE_PATH,
        help="Path to the deterministic demo input fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for atomic JSON output.",
    )
    args = parser.parse_args(argv)

    rendered = _render(run_demo(input_path=args.input))
    if args.output is None:
        print(rendered)
        return 0

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temporary_path.write_text(rendered + "\n", encoding="utf-8")
        temporary_path.replace(output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
