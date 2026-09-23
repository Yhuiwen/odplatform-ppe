"""Shared read-only runtime assembly for Streamlit dashboard pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from services.alert_service import AlertService
from services.event_query_service import EventQueryService

__all__ = ["DashboardRuntime", "build_runtime", "get_runtime", "event_rows"]


@dataclass(frozen=True, slots=True)
class DashboardRuntime:
    query_service: EventQueryService
    alert_service: AlertService
    web_alerts: WebAlertAdapter


def build_runtime(
    *,
    database_path: str | Path | None = None,
    snapshot_root: str | Path | None = None,
) -> DashboardRuntime:
    """Create the service graph without opening SQLite at import time."""

    database = Database(database_path)
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    storage = SnapshotStorage(snapshot_root)
    web_alerts = WebAlertAdapter()
    return DashboardRuntime(
        query_service=EventQueryService(
            event_repository,
            snapshot_repository,
            storage,
        ),
        alert_service=AlertService(
            (
                ConsoleAlertAdapter(),
                web_alerts,
            )
        ),
        web_alerts=web_alerts,
    )


def get_runtime(st: Any) -> DashboardRuntime:
    """Return one session-scoped runtime from Streamlit session state."""

    key = "_odplatform_dashboard_runtime"
    runtime = st.session_state.get(key)
    if runtime is None:
        runtime = build_runtime()
        st.session_state[key] = runtime
    if not isinstance(runtime, DashboardRuntime):
        raise TypeError("dashboard session runtime has an invalid type")
    return runtime


def event_rows(page: Any) -> list[dict[str, Any]]:
    """Convert one EventPage into serializable table rows."""

    return [event.to_dict() for event in page.items]
