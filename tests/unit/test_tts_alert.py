from datetime import datetime, timedelta, timezone

import pytest

from core.schemas.alerts import AlertMessage, AlertStatus
from core.schemas.compliance import ComplianceEventType
from infra.alerts.tts import TTSAlertAdapter
from infra.tts.tts_service import (
    TTSBackendError,
    TTSService,
    TTSUnavailableError,
)


def _message(
    event_id: str = "EVT-tts-01",
    *,
    track_id: int = 7,
) -> AlertMessage:
    return AlertMessage(
        event_id=event_id,
        timestamp="2026-09-23T12:34:56Z",
        track_id=track_id,
        alert_type=ComplianceEventType.NO_HELMET,
        confidence=0.91,
        snapshot="20260923/event_EVT-tts-01.jpg",
        message="track 7: 未佩戴安全帽 (0.91)",
    )


def test_tts_service_uses_injected_speaker_without_native_backend() -> None:
    spoken: list[str] = []
    service = TTSService(speaker=spoken.append)

    service.speak("  未佩戴安全帽  ")

    assert spoken == ["未佩戴安全帽"]


def test_tts_service_reports_missing_optional_backend() -> None:
    def unavailable(rate: int, volume: float):
        raise ImportError("pyttsx3 unavailable")

    service = TTSService(engine_factory=unavailable)

    with pytest.raises(TTSUnavailableError) as exc_info:
        service.speak("未佩戴安全帽")

    assert exc_info.value.code == "TTS_UNAVAILABLE"


def test_tts_service_wraps_speaker_failure() -> None:
    def failing_speaker(message: str) -> None:
        raise OSError("audio device unavailable")

    service = TTSService(speaker=failing_speaker)

    with pytest.raises(TTSBackendError) as exc_info:
        service.speak("未佩戴安全帽")

    assert exc_info.value.code == "TTS_BACKEND_FAILED"


def test_tts_alert_adapter_delivers_and_deduplicates() -> None:
    spoken: list[str] = []
    adapter = TTSAlertAdapter(
        TTSService(speaker=spoken.append),
        cooldown_seconds=0,
    )
    message = _message()

    first = adapter.send(message)
    second = adapter.send(message)

    assert first.status is AlertStatus.DELIVERED
    assert second.status is AlertStatus.SKIPPED
    assert second.error_code == "ALERT_DUPLICATE"
    assert spoken == [message.message]


def test_tts_alert_adapter_applies_track_type_cooldown() -> None:
    spoken: list[str] = []
    now = [datetime(2026, 9, 23, 12, 35, 0, tzinfo=timezone.utc)]
    adapter = TTSAlertAdapter(
        TTSService(speaker=spoken.append),
        cooldown_seconds=30,
        clock=lambda: now[0],
    )

    first = adapter.send(_message("EVT-tts-01"))
    now[0] += timedelta(seconds=10)
    second = adapter.send(_message("EVT-tts-02"))

    assert first.status is AlertStatus.DELIVERED
    assert second.status is AlertStatus.SKIPPED
    assert second.error_code == "TTS_COOLDOWN"
    assert spoken == [_message().message]


def test_tts_alert_adapter_isolates_backend_failure() -> None:
    adapter = TTSAlertAdapter(
        TTSService(speaker=lambda _: (_ for _ in ()).throw(OSError("no audio"))),
        cooldown_seconds=0,
    )

    result = adapter.send(_message())

    assert result.status is AlertStatus.FAILED
    assert result.error_code == "TTS_BACKEND_FAILED"
    assert result.error_message is not None


def test_tts_alert_adapter_can_be_disabled() -> None:
    spoken: list[str] = []
    adapter = TTSAlertAdapter(
        TTSService(speaker=spoken.append),
        enabled=False,
    )

    result = adapter.send(_message())

    assert result.status is AlertStatus.SKIPPED
    assert result.error_code == "TTS_DISABLED"
    assert spoken == []
