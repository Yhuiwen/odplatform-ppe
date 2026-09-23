from pathlib import Path

from utils.paths import PROJECT_ROOT


DASHBOARD_PAGES = (
    "web/pages/0_Overview.py",
    "web/pages/1_Event_Explorer.py",
    "web/pages/2_Evidence_Viewer.py",
    "web/pages/3_Statistics.py",
)


def test_dashboard_pages_exist_and_stay_out_of_pipeline_layers() -> None:
    for relative_path in DASHBOARD_PAGES:
        source = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        assert "event_query_service" not in source
        assert "InferenceService" not in source
        assert "YOLODetector" not in source
        assert "ComplianceEngine" not in source
        assert "EventEngine" not in source
        assert "sqlite3" not in source


def test_dashboard_support_uses_service_boundary() -> None:
    source = (PROJECT_ROOT / "web/dashboard_support.py").read_text(
        encoding="utf-8"
    )
    assert "EventQueryService" in source
    assert "InferenceService" not in source
    assert "YOLODetector" not in source
