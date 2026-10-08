"""Shared read-only runtime assembly for Streamlit dashboard pages."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.tts import TTSAlertAdapter
from infra.alerts.web import WebAlertAdapter
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from infra.tts.tts_service import TTSService
from services.alert_service import AlertService
from services.event_query_service import EventQueryService
from services.event_status_service import EventStatusService
from utils.config_loader import load_config

__all__ = ["DashboardRuntime", "build_runtime", "get_runtime", "event_rows"]


def _validation_path(relative: str) -> Path | None:
    """Keep a manually launched P9-B browser check out of release evidence."""
    root = os.environ.get("ODPLATFORM_P9B_VALIDATION_ROOT")
    return Path(root).resolve() / relative if root else None


@dataclass(frozen=True, slots=True)
class DashboardRuntime:
    query_service: EventQueryService
    status_service: EventStatusService
    alert_service: AlertService
    web_alerts: WebAlertAdapter
    tts_alerts: TTSAlertAdapter


def build_runtime(
    *,
    database_path: str | Path | None = None,
    snapshot_root: str | Path | None = None,
) -> DashboardRuntime:
    """Create the service graph without opening SQLite at import time."""

    database = Database(database_path or _validation_path("database/events.sqlite3"))
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    storage = SnapshotStorage(snapshot_root or _validation_path("snapshots"))
    web_alerts = WebAlertAdapter()
    monitoring_config = load_config("monitoring").get("monitoring", {})
    tts_config = (
        monitoring_config.get("tts", {})
        if isinstance(monitoring_config, dict)
        else {}
    )
    if not isinstance(tts_config, dict):
        tts_config = {}
    tts_alerts = TTSAlertAdapter(
        TTSService(
            rate=int(tts_config.get("rate", 180)),
            volume=float(tts_config.get("volume", 1.0)),
        ),
        enabled=bool(tts_config.get("enabled", True)),
        cooldown_seconds=float(tts_config.get("cooldown_seconds", 30.0)),
    )
    return DashboardRuntime(
        query_service=EventQueryService(
            event_repository,
            snapshot_repository,
            storage,
        ),
        status_service=EventStatusService(event_repository),
        alert_service=AlertService(
            (
                ConsoleAlertAdapter(),
                web_alerts,
                tts_alerts,
            )
        ),
        web_alerts=web_alerts,
        tts_alerts=tts_alerts,
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
