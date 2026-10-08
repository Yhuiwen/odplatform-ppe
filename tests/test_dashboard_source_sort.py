"""Dashboard source labels and database-backed time ordering."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventQuery, StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from services.event_query_service import EventQueryService
from web.dashboard_support import build_runtime
from web.ui.components import event_table_rows
from web.ui.formatting import format_source_label, source_group_counts


def _record(event_id: str, timestamp: str, source: str) -> StoredEvent:
    return StoredEvent(
        id=event_id, timestamp=timestamp, track_id=1,
        type=ComplianceEventType.NO_HELMET, confidence=0.8,
        source_timestamp=1.0, source=source,
    )


def test_time_sort_and_grouped_source_filter_apply_before_pagination(tmp_path):
    repository = EventRepository(Database(tmp_path / "events.sqlite3"))
    for event_id, timestamp, source in (
        ("EVT-1", "2026-10-07T10:00:00Z", "mp4:first.mp4"),
        ("EVT-2", "2026-10-07T11:00:00Z", "usb:0"),
        ("EVT-3", "2026-10-07T12:00:00Z", "mp4:second.mp4"),
        ("EVT-4", "2026-10-07T13:00:00Z", "rtsp:camera.example"),
    ):
        repository.insert(_record(event_id, timestamp, source))
    service = EventQueryService(repository)

    assert [item.id for item in service.list_events(limit=2, sort_order="asc").items] == ["EVT-1", "EVT-2"]
    assert [item.id for item in service.list_events(limit=2, sort_order="desc").items] == ["EVT-4", "EVT-3"]
    assert [item.id for item in service.list_events(source_group="mp4", sort_order="asc").items] == ["EVT-1", "EVT-3"]
    assert [item.id for item in service.list_events(source_group="usb0").items] == ["EVT-2"]
    assert [item.id for item in service.list_events(source_group="rtsp").items] == ["EVT-4"]
    page = service.list_events(limit=4)
    rows = event_table_rows(page.items, include_source=True, sources=service.sources_for_events(page.items))
    assert all("事件 ID" not in row and "id" not in row for row in rows)
    assert {row["来源"] for row in rows} == {"mp4", "usb0", "rtsp"}


def test_source_labels_aggregate_without_exposing_location():
    assert format_source_label("mp4:workers.mp4") == "mp4"
    assert format_source_label("usb:12") == "usb12"
    assert format_source_label("rtsp:user@camera.example") == "rtsp"
    assert source_group_counts((("mp4:a.mp4", 2), ("mp4:b.mp4", 3), ("usb:0", 1))) == {"mp4": 5, "usb0": 1}


def test_overview_with_events_renders_trend_and_no_id_column(tmp_path, monkeypatch):
    monkeypatch.setenv("ODPLATFORM_P9B_VALIDATION_ROOT", str(tmp_path))
    runtime = build_runtime(
        database_path=tmp_path / "events.sqlite3",
        snapshot_root=tmp_path / "snapshots",
    )
    runtime.status_service.repository.insert(
        _record("EVT-overview", "2026-10-07T10:00:00Z", "mp4:private-name.mp4")
    )
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "web/pages/0_Overview.py"), default_timeout=30)
    app.session_state["_odplatform_dashboard_runtime"] = runtime
    app.run()
    assert not app.exception
    table = app.table[0].value
    assert "事件 ID" not in table.columns
    assert table.iloc[0]["来源"] == "mp4"
