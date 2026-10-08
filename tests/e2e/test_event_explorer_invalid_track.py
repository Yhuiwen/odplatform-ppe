"""Invalid Track ID must stop the dashboard query."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from web.dashboard_support import build_runtime


def test_invalid_track_id_fails_closed(tmp_path):
    runtime = build_runtime(
        database_path=tmp_path / "events.sqlite3",
        snapshot_root=tmp_path / "snapshots",
    )
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[2] / "web/pages/1_Event_Explorer.py")
    )
    app.session_state["_odplatform_dashboard_runtime"] = runtime
    app.run()
    app.text_input[0].set_value("abc").run()
    assert not app.exception
    assert any("Track ID 必须是非负整数" in item.value for item in app.error)
    assert len(app.dataframe) == 0
    assert not any("第 " in item.value for item in app.caption)
