"""Speech never blocks inference and keeps one engine-owning thread."""
import pytest
pytest.importorskip('fastapi')
import api.main
from threading import Event, get_ident
from time import monotonic
from types import SimpleNamespace
from api.queued_tts import QueuedTTSAdapter
from infra.alerts.tts import TTSAlertAdapter
from infra.tts.tts_service import TTSService
from core.schemas.alerts import AlertMessage
from core.schemas.compliance import ComplianceEventType


def message(identifier):
    return AlertMessage(event_id=identifier, timestamp='2026-10-10T00:00:00Z', track_id=1,
                        alert_type=ComplianceEventType.NO_HELMET, confidence=.8, snapshot=None, message='测试')


def test_slow_speech_nonblocking_and_two_sessions_same_thread():
    release, entered, second = Event(), Event(), Event()
    threads=[]
    def speaker(text):
        threads.append(get_ident())
        entered.set()
        assert release.wait(3)
        if len(threads)==2: second.set()
    worker=QueuedTTSAdapter(TTSAlertAdapter(TTSService(speaker=speaker), cooldown_seconds=30), capacity=1)
    try:
        worker.start_session(lambda: None)
        before=monotonic()
        assert worker.send(message('EVT-first')).error_code=='TTS_QUEUED'
        assert monotonic()-before < .2
        assert entered.wait(2)
        assert worker.result('EVT-first')['status']=='skipped'
        assert worker.send(message('EVT-first')).error_code=='TTS_DUPLICATE_QUEUED'
        worker.start_session(lambda: None)
        worker.send(message('EVT-second'))
        assert worker.send(message('EVT-full')).error_code=='TTS_QUEUE_FULL'
        release.set()
        assert second.wait(2)
        worker.queue.join()
        assert len(set(threads))==1 and threads[0]!=get_ident()
        assert worker.result('EVT-first')['status']=='delivered'
        assert worker.result('EVT-second')['status']=='delivered'
        assert worker.counts()==(1,0)
    finally:
        release.set();worker.close()
    assert not worker.thread.is_alive()


def test_failed_speech_is_not_reported_delivered():
    def fail(text): raise RuntimeError('private')
    worker=QueuedTTSAdapter(TTSAlertAdapter(TTSService(speaker=fail)))
    try:
        worker.send(message('EVT-failed'));worker.queue.join()
        assert worker.result('EVT-failed')['status']=='failed'
        assert worker.counts()==(0,1)
        application=SimpleNamespace(state=SimpleNamespace(queued_tts=worker,monitoring=SimpleNamespace(
            status=lambda:SimpleNamespace(to_dict=lambda:{'recent_events':[{'event_id':'EVT-failed','alerts':[{'adapter':'tts','error_code':'TTS_QUEUED'}]}]}))))
        result=api.main.event_alerts(application,'EVT-failed')
        assert result['items'][0]['status']=='failed'
        assert 'private' not in str(result)
    finally: worker.close()


def test_cooldown_remains_enforced_inside_one_session():
    spoken=[]
    worker=QueuedTTSAdapter(TTSAlertAdapter(TTSService(speaker=spoken.append),cooldown_seconds=30))
    try:
        worker.send(message('EVT-one'));worker.queue.join()
        worker.send(message('EVT-two'));worker.queue.join()
        assert worker.result('EVT-two')['error_code']=='TTS_COOLDOWN'
        assert len(spoken)==1
    finally:worker.close()
