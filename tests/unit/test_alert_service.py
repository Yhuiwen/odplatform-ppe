import json
from datetime import datetime, timezone

from core.schemas.alerts import AlertMessage, AlertResult, AlertStatus
from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus, PersistedEvent
from infra.alerts.console import ConsoleAlertAdapter
from infra.alerts.web import WebAlertAdapter
from services.alert_service import AlertService


def _event() -> PersistedEvent:
    return PersistedEvent(
        id="EVT-01",
        timestamp="2026-09-23T12:34:56Z",
        track_id=7,
        type=ComplianceEventType.NO_HELMET,
        confidence=0.91,
        snapshot="20260923/event_EVT-01.jpg",
        status=EventStatus.OPEN,
    )


def _clock() -> datetime:
    return datetime(2026, 9, 23, 12, 35, 0, tzinfo=timezone.utc)


def test_console_and_web_adapters_deliver_and_deduplicate() -> None:
    console_lines: list[str] = []
    published: list[AlertMessage] = []
    console = ConsoleAlertAdapter(sink=console_lines.append, clock=_clock)
    web = WebAlertAdapter(publisher=published.append, clock=_clock)
    service = AlertService((console, web), clock=_clock)
    event = _event()

    first = service.dispatch_event(event)
    second = service.dispatch_event(event)

    assert [result.status for result in first] == [
        AlertStatus.DELIVERED,
        AlertStatus.DELIVERED,
    ]
    assert [result.status for result in second] == [
        AlertStatus.SKIPPED,
        AlertStatus.SKIPPED,
    ]
    assert json.loads(console_lines[0])["event_id"] == event.id
    assert published == [AlertMessage(
        event_id=event.id,
        timestamp=event.timestamp,
        track_id=event.track_id,
        alert_type=event.type,
        confidence=event.confidence,
        snapshot=event.snapshot,
        message="track 7: 未佩戴安全帽 (0.91)",
    )]
    assert web.history()[0].event_id == event.id


def test_alert_service_isolates_adapter_failure() -> None:
    class FailingAdapter:
        name = "failing"

        def send(self, message: AlertMessage) -> AlertResult:
            raise RuntimeError("adapter unavailable")

    class RecordingAdapter:
        name = "recording"

        def __init__(self) -> None:
            self.messages: list[AlertMessage] = []

        def send(self, message: AlertMessage) -> AlertResult:
            self.messages.append(message)
            return AlertResult(
                event_id=message.event_id,
                adapter=self.name,
                status=AlertStatus.DELIVERED,
                timestamp="2026-09-23T12:35:00Z",
            )

    recorder = RecordingAdapter()
    service = AlertService((FailingAdapter(), recorder), clock=_clock)
    results = service.dispatch_event(_event())

    assert results[0].status is AlertStatus.FAILED
    assert results[0].error_code == "ALERT_ADAPTER_FAILED"
    assert results[1].status is AlertStatus.DELIVERED
    assert len(recorder.messages) == 1


def test_web_adapter_reports_publisher_failure_without_history() -> None:
    def fail_publish(message: AlertMessage) -> None:
        raise OSError("browser unavailable")

    adapter = WebAlertAdapter(publisher=fail_publish, clock=_clock)
    result = adapter.send(
        AlertMessage(
            event_id="EVT-01",
            timestamp="2026-09-23T12:34:56Z",
            track_id=7,
            alert_type=ComplianceEventType.NO_VEST,
            confidence=0.8,
            snapshot=None,
            message="track 7: 未穿反光背心 (0.80)",
        )
    )

    assert result.status is AlertStatus.FAILED
    assert result.error_code == "ALERT_ADAPTER_FAILED"
    assert adapter.history() == ()
