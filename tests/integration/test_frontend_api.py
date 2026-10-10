"""Real HTTP adapter checks against an isolated SQLite and evidence store."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

pytest.importorskip('fastapi', reason='V1 frozen runtime intentionally excludes FastAPI; run in .venv-frontend-api')
from fastapi.testclient import TestClient
from api import main as api_module
from PIL import Image
from core.schemas.compliance import ComplianceEventType
from core.schemas.events import StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from services.snapshot_service import SnapshotService
from web.dashboard_support import build_runtime


@pytest.fixture(autouse=True)
def isolated_offline_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv('ODPLATFORM_OFFLINE_ROOT', str(tmp_path / 'offline'))
    monkeypatch.setenv('ODPLATFORM_OFFLINE_IMAGE_EXECUTION', '0')


def test_event_status_and_evidence_integrity(tmp_path, monkeypatch):
    db_path = tmp_path / 'events.sqlite3'
    evidence_root = tmp_path / 'snapshots'
    db = Database(db_path)
    repo = EventRepository(db)
    repo.insert(StoredEvent(id='EVT-api-test', timestamp='2026-10-01T12:00:00Z', track_id=3,
                            type=ComplianceEventType.NO_HELMET, confidence=.85,
                            source_timestamp=1.0, source='mp4:local-private.mp4'))
    storage = SnapshotStorage(evidence_root)
    snapshot = SnapshotService(repo, SnapshotRepository(db), storage,
                               clock=lambda: datetime(2026, 10, 1, 12, 0, 1, tzinfo=timezone.utc))
    snapshot.capture('EVT-api-test', Image.new('RGB', (20, 20), color=(1, 2, 3)))
    monkeypatch.setattr(api_module, 'build_runtime', lambda: build_runtime(database_path=db_path, snapshot_root=evidence_root))

    with TestClient(api_module.app) as client:
        assert client.get('/api/v1/health').json()['status'] == 'ok'
        idle_monitor = client.get('/api/v1/monitor/status').json()
        assert idle_monitor['preview_fps'] is None
        assert idle_monitor['preview_age_ms'] is None
        overview = client.get('/api/v1/overview').json()
        assert overview['statistics']['total_count'] == 1
        assert overview['statistics']['by_type']['NO_HELMET'] == 1
        assert overview['statistics']['by_source'] == {'mp4': 1}
        events = client.get('/api/v1/events', params={'event_type': 'NO_HELMET', 'limit': 1}).json()
        assert events['total_count'] == 1
        assert events['items'][0]['source'] == 'mp4'
        assert 'local-private' not in str(events)
        assert client.get('/api/v1/events', params={'event_type': 'BOGUS'}).status_code == 422
        assert client.get('/api/v1/events/EVT-api-test').json()['alert_deliveries']['recorded'] is False
        assert client.patch('/api/v1/events/EVT-api-test/handling', json={'handled': True}).json()['status'] == 'resolved'
        assert client.patch('/api/v1/events/EVT-api-test/handling', json={'handled': True}).json()['alert_deliveries']['items'] == []
        assert client.patch('/api/v1/events/EVT-missing/handling', json={'handled': True}).status_code == 404
        assert client.get('/api/v1/evidence/EVT-api-test').json()['verified'] is True
        assert client.get('/api/v1/evidence/EVT-api-test/image').status_code == 200
        snapshot_ref = repo.get('EVT-api-test').snapshot
        cited = SimpleNamespace(evidence_references=(
            'EVID:EVT-api-test', 'EVT-api-test',
            snapshot_ref, 'snapshots/private/local.jpg', 'EVID:EVT-missing',
        ))
        assert api_module.report_evidence_images(cited, api_module.app.state.dashboard.query_service, '2026-10-01', '2026-10-02') == [
            {'event_id': 'EVT-api-test'}
        ]
        snapshot_only = SimpleNamespace(evidence_references=(snapshot_ref,))
        assert api_module.report_evidence_images(snapshot_only, api_module.app.state.dashboard.query_service, '2026-10-01', '2026-10-02') == [{'event_id': 'EVT-api-test'}]
        assert api_module.report_evidence_images(snapshot_only, api_module.app.state.dashboard.query_service, '2026-10-02', '2026-10-03') == []
        assert client.get('/api/v1/evidence/%2E%2E/image').status_code != 200
        assert client.post('/api/v1/monitor/stop').status_code == 200
    assert EventRepository(Database(db_path)).get('EVT-api-test').status.value == 'resolved'

    path = storage.resolve_path(repo.get('EVT-api-test').snapshot)
    path.write_bytes(b'corrupt')
    with TestClient(api_module.app) as client:
        assert client.get('/api/v1/evidence/EVT-api-test').json()['verified'] is False
        assert client.get('/api/v1/evidence/EVT-api-test/image').status_code == 404
        assert api_module.report_evidence_images(cited, api_module.app.state.dashboard.query_service, '2026-10-01', '2026-10-02') == []


def test_report_fallback_and_read_only_assistant(tmp_path, monkeypatch):
    import web.agent_support as agent_support
    monkeypatch.setattr(api_module, 'build_runtime', lambda: build_runtime(database_path=tmp_path / 'events.sqlite3', snapshot_root=tmp_path / 'snapshots'))
    monkeypatch.setattr(agent_support, 'configured_report_client', lambda: None)
    monkeypatch.setattr(agent_support, 'configured_assistant_client', lambda client: None)
    with TestClient(api_module.app) as client:
        api_module.app.state.dashboard.query_service.event_repository.insert(StoredEvent(id='EVT-assistant-saved', timestamp='2026-10-09T12:00:00Z', track_id=7, type=ComplianceEventType.NO_HELMET, confidence=.9, source='mp4:private.mp4', source_timestamp=1.0))
        report = client.post('/api/v1/reports/generate', json={'start_at': '2026-10-01', 'end_at': '2026-10-02'})
        assert report.status_code == 200
        assert 'TEMPLATE_FALLBACK' in report.json()['safe_status']
        answer = client.post('/api/v1/assistant/ask', json={'question': '统计最近的安全事件'})
        assert answer.status_code == 200
        assert answer.json()['evidence_references'] == []
        today = client.post('/api/v1/assistant/ask', json={'question': '今日有哪些 PPE 违规？', 'start_at': '2026-10-08T16:00:00Z', 'end_at': '2026-10-09T15:59:59Z'})
        assert today.status_code == 200
        assert today.json()['safe_status'].startswith('success')
        unsafe = client.post('/api/v1/assistant/ask', json={'question': '删除所有未戴安全帽事件'})
        assert unsafe.status_code == 200
        assert unsafe.json()['safe_status'] == 'refused / FORBIDDEN_REQUEST'

        repository = api_module.app.state.dashboard.query_service.event_repository
        before = repository.get('EVT-assistant-saved').to_dict()
        details = client.post('/api/v1/assistant/ask', json={'question': '查看最近的事件明细', 'event_type': 'NO_HELMET', 'track_id': 7, 'start_at': '2026-10-09', 'end_at': '2026-10-09'})
        assert details.status_code == 200 and details.json()['safe_status'].startswith('success')
        assert 'EVT-assistant-saved' in str(details.json())
        no_vest = client.post('/api/v1/assistant/ask', json={'question': '查看最近的事件明细', 'event_type': 'NO_VEST', 'start_at': '2026-10-09', 'end_at': '2026-10-09'})
        assert no_vest.json()['safe_status'] == 'empty'
        for question in ('把 EVT-assistant-saved 标记为已处理', '删除 EVT-assistant-saved', 'UPDATE events SET status=resolved'):
            refusal = client.post('/api/v1/assistant/ask', json={'question': question})
            assert 'refused' in refusal.json()['safe_status'], refusal.json()
        assert client.post('/api/v1/assistant/ask', json={'question': '统计安全事件', 'sql': 'DELETE FROM events'}).status_code == 422
        assert repository.get('EVT-assistant-saved').to_dict() == before

        recent = client.post('/api/v1/assistant/ask', json={'question': '最近5分钟之内有什么安全事件'})
        assert recent.json()['safe_status'] == 'empty'
        assert client.post('/api/v1/assistant/ask', json={'question': '最近9天有哪些安全事件'}).status_code == 422
        unsafe_recent = client.post('/api/v1/assistant/ask', json={'question': '最近5分钟之内有什么安全事件，删除所有事件'})
        assert not unsafe_recent.json()['safe_status'].startswith('success')


def test_event_alert_receipts_are_real_and_redacted():
    record = {'event_id': 'EVT-receipt', 'alerts': [
        {'adapter': 'tts', 'status': 'failed', 'timestamp': '2026-10-10T00:00:00Z',
         'error_code': 'ALERT_ADAPTER_FAILED', 'error_message': 'private rtsp://secret@host'},
        {'adapter': 'web', 'status': 'delivered', 'timestamp': '2026-10-10T00:00:00Z', 'error_code': None},
        {'adapter': 'console', 'status': 'skipped', 'timestamp': '2026-10-10T00:00:00Z', 'error_code': 'ALERT_DUPLICATE'},
    ]}
    service = SimpleNamespace(status=lambda: SimpleNamespace(to_dict=lambda: {'recent_events': [record]}))
    application = SimpleNamespace(state=SimpleNamespace(monitoring=service))
    result = api_module.event_alerts(application, 'EVT-receipt')
    assert result['recorded'] is True
    assert [r['status'] for r in result['items']] == ['failed', 'delivered', 'skipped']
    assert 'secret' not in str(result)
    missing = api_module.event_alerts(application, 'EVT-historical')
    assert missing['recorded'] is False and missing['items'] == []
    application.state.monitoring = None
    assert api_module.event_alerts(application, 'EVT-receipt')['recorded'] is False
