"""One click must update the realtime start/stop controls."""

from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from core.schemas.video import SourceType
from services.monitoring_service import MonitoringState, MonitoringStatus
import web.monitoring_support as monitoring_support


class _Service:
    def __init__(self) -> None:
        self.current = MonitoringStatus()

    def status(self) -> MonitoringStatus:
        return self.current

    def start(self, request) -> MonitoringStatus:
        self.current = MonitoringStatus(
            state=MonitoringState.RUNNING, source_type=request.source_type,
        )
        return self.current

    def stop(self) -> MonitoringStatus:
        self.current = MonitoringStatus(state=MonitoringState.STOPPED)
        return self.current


def test_usb_start_and_stop_buttons_update_after_one_click(monkeypatch):
    service = _Service()
    monkeypatch.setattr(
        monitoring_support, "get_monitoring_runtime",
        lambda st: SimpleNamespace(service=service, preview_url="http://127.0.0.1/preview/test"),
    )
    page = Path(__file__).resolve().parents[2] / "web/pages/1_实时监控.py"
    app = AppTest.from_file(str(page))
    app.run()
    app.selectbox[0].set_value("USB 摄像头").run()

    next(button for button in app.button if button.label == "开始监控").click().run()
    assert not app.exception
    assert service.current.source_type is SourceType.USB_CAMERA
    assert next(button for button in app.button if button.label == "开始监控").disabled
    assert not next(button for button in app.button if button.label == "停止监控").disabled

    next(button for button in app.button if button.label == "停止监控").click().run()
    assert not app.exception
    assert service.current.state is MonitoringState.STOPPED
    assert not next(button for button in app.button if button.label == "开始监控").disabled
    assert next(button for button in app.button if button.label == "停止监控").disabled
