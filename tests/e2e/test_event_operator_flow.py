"""Operator status writes and evidence selection from the event list."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus, StoredEvent
from web.dashboard_support import build_runtime


ROOT = Path(__file__).resolve().parents[2]


def test_event_status_selection_persists_and_page_refreshes(tmp_path, monkeypatch):
    monkeypatch.setenv("ODPLATFORM_P9B_VALIDATION_ROOT", str(tmp_path))
    runtime = build_runtime(
        database_path=tmp_path / "events.sqlite3",
        snapshot_root=tmp_path / "snapshots",
    )
    event_id = "EVT-operator-flow"
    runtime.status_service.repository.insert(StoredEvent(
        id=event_id,
        timestamp="2026-10-07T12:34:56Z",
        track_id=6,
        type=ComplianceEventType.NO_HELMET,
        confidence=0.8,
        source_timestamp=1.0,
        source="mp4:test.mp4",
    ))
    app = AppTest.from_file(str(ROOT / "web/pages/1_Event_Explorer.py"))
    app.session_state["_odplatform_dashboard_runtime"] = runtime
    app.run()
    assert not app.exception
    assert any(button.label == "查看详情" for button in app.button)
    assert not any("事件详情" in item.value for item in app.markdown)

    selector = next(item for item in app.selectbox if item.key == f"event_status_{event_id}")
    selector.set_value("已处理").run()
    assert not app.exception
    assert runtime.query_service.get_event(event_id).status is EventStatus.RESOLVED

    selector = next(item for item in app.selectbox if item.key == f"event_status_{event_id}")
    selector.set_value("待处理").run()
    assert not app.exception
    assert runtime.query_service.get_event(event_id).status is EventStatus.OPEN

    next(button for button in app.button if button.label == "查看详情").click().run()
    assert app.session_state["selected_evidence_event_id"] == event_id


def test_evidence_page_selects_requested_event(tmp_path, monkeypatch):
    monkeypatch.setenv("ODPLATFORM_P9B_VALIDATION_ROOT", str(tmp_path))
    runtime = build_runtime(
        database_path=tmp_path / "events.sqlite3",
        snapshot_root=tmp_path / "snapshots",
    )
    event_id = "EVT-requested-evidence"
    runtime.status_service.repository.insert(StoredEvent(
        id=event_id,
        timestamp="2026-10-07T12:34:56Z",
        track_id=6,
        type=ComplianceEventType.NO_VEST,
        confidence=0.8,
        source_timestamp=1.0,
        source="mp4:test.mp4",
    ))
    app = AppTest.from_file(str(ROOT / "web/pages/2_Evidence_Viewer.py"))
    app.session_state["_odplatform_dashboard_runtime"] = runtime
    app.session_state["selected_evidence_event_id"] = event_id
    app.run()
    assert not app.exception
    assert app.selectbox[0].value == event_id
    assert any("证据图片不可用" in item.value for item in app.markdown)
