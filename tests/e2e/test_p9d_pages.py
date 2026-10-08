"""P9-D Streamlit presentation smoke on an empty local database."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from web.dashboard_support import build_runtime
from web.ui.formatting import available_date_range, format_confidence, format_event_status, format_event_type, short_event_id


ROOT = Path(__file__).resolve().parents[2]
PAGES = ("Home.py", "pages/0_Overview.py", "pages/1_Event_Explorer.py", "pages/1_实时监控.py", "pages/2_Evidence_Viewer.py", "pages/3_Statistics.py", "pages/6_AI报告.py", "pages/7_AI助手.py")


def test_chinese_titled_pages_have_english_url_paths():
    tree = ast.parse((ROOT / "web" / "Home.py").read_text(encoding="utf-8"))
    paths = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "Page":
            continue
        if not isinstance(node.args[0], ast.Constant):
            continue
        keywords = {item.arg: item.value for item in node.keywords}
        if "url_path" in keywords:
            paths[node.args[0].value] = ast.literal_eval(keywords["url_path"])
    assert paths == {
        "pages/1_实时监控.py": "Monitoring",
        "pages/6_AI报告.py": "AI_Report",
        "pages/7_AI助手.py": "AI_Assistant",
    }
    assert all(path.isascii() for path in paths.values())


@pytest.mark.parametrize("page", PAGES)
def test_page_loads_without_exception(page, tmp_path, monkeypatch):
    monkeypatch.setenv("ODPLATFORM_P9B_VALIDATION_ROOT", str(tmp_path))
    app = AppTest.from_file(str(ROOT / "web" / page), default_timeout=30)
    app.session_state["_odplatform_dashboard_runtime"] = build_runtime(database_path=tmp_path / "events.sqlite3", snapshot_root=tmp_path / "snapshots")
    app.run()
    assert not app.exception
    if page.endswith("1_实时监控.py"):
        assert any(
            'alt="实时处理后的检测画面"' in item.value
            and "/preview/" in item.value
            for item in app.markdown
        )


def test_presentation_labels_and_available_dates():
    from core.schemas.events import EventStatistics

    statistics = EventStatistics(total_count=1, by_type=(), by_status=(), by_source=(), by_day=(), earliest_at="2026-09-23T13:58:26Z", latest_at="2026-09-23T13:58:26Z", generated_at="2026-10-07T00:00:00Z")
    assert format_event_type("PPE_UNKNOWN") == "PPE 状态未知"
    assert format_event_status("open") == "待处理"
    assert format_confidence(0, "PPE_UNKNOWN") == "—"
    assert format_confidence(0.86, "NO_HELMET") == "86%"
    assert short_event_id("EVT-9a4985b7-123456") == "EVT-9a4985b7..."
    start, end = available_date_range(statistics)
    assert start.isoformat() == end.isoformat() == "2026-09-23"
