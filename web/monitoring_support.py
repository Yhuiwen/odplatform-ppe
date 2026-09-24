"""Session-scoped assembly for the Phase 7 realtime monitoring service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.events.event_engine import EventEngine
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.json_event_store import JSONEventStore
from infra.storage.snapshot_storage import SnapshotStorage
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService
from services.event_service import EventService
from services.inference_service import InferenceService
from services.monitoring_service import MonitoringService
from services.snapshot_service import SnapshotService
from utils.config_loader import load_config
from web.dashboard_support import get_runtime

__all__ = ["MonitoringRuntime", "get_monitoring_runtime"]


@dataclass(frozen=True, slots=True)
class MonitoringRuntime:
    service: MonitoringService


def _settings() -> dict[str, Any]:
    config = load_config("monitoring")
    monitoring = config.get("monitoring")
    if not isinstance(monitoring, dict):
        raise ValueError("configs/monitoring.yaml requires a monitoring mapping")
    return monitoring


def build_monitoring_runtime(st: Any) -> MonitoringRuntime:
    """Build one service-owned session around the existing pipeline boundaries."""

    monitoring = _settings()
    database = Database()
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    snapshot_storage = SnapshotStorage()
    dashboard_runtime = get_runtime(st)
    service = MonitoringService(
        inference_service=InferenceService(
            config_path="configs/inference.yaml",
            execution_enabled=bool(monitoring.get("execution_enabled", False)),
        ),
        tracker=ByteTrackPersonTrackingAdapter(),
        association_adapter=PPEPersonAssociationAdapter(),
        compliance_service=ComplianceService(),
        event_service=EventService(
            engine=EventEngine(),
            store=JSONEventStore(),
        ),
        ingest_service=EventIngestService(event_repository),
        snapshot_service=SnapshotService(
            event_repository,
            snapshot_repository,
            snapshot_storage,
        ),
        alert_service=dashboard_runtime.alert_service,
        event_loader=event_repository.get,
        execution_enabled=bool(monitoring.get("execution_enabled", False)),
        stop_timeout_seconds=float(
            monitoring.get("stop_timeout_seconds", 5.0)
        ),
        max_recent_events=int(monitoring.get("max_recent_events", 20)),
    )
    return MonitoringRuntime(service=service)


def get_monitoring_runtime(st: Any) -> MonitoringRuntime:
    """Return one Streamlit-session-scoped monitoring runtime."""

    key = "_odplatform_monitoring_runtime"
    runtime = st.session_state.get(key)
    if runtime is None:
        runtime = build_monitoring_runtime(st)
        st.session_state[key] = runtime
    if not isinstance(runtime, MonitoringRuntime):
        raise TypeError("monitoring session runtime has an invalid type")
    return runtime
