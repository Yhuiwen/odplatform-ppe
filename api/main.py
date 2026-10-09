"""Loopback FastAPI boundary. Business decisions remain in existing services."""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
from typing import Literal
import os
import sys
import re

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# The API environment owns FastAPI/Starlette; append the frozen V1 business
# runtime after its own site-packages so both version sets remain isolated.
ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PACKAGES = Path(os.environ.get('ODPLATFORM_RUNTIME_SITE_PACKAGES', ROOT / '.venv-final-demo' / 'Lib' / 'site-packages'))
if RUNTIME_PACKAGES.is_dir():
    sys.path.append(str(RUNTIME_PACKAGES))

from core.schemas.events import EventQuery
from core.video.video_source import SourceType
from infra.database.repository import EventNotFoundError
from services.monitoring_service import MonitoringSourceRequest, MonitoringError
from web.dashboard_support import build_runtime, _validation_path
from web.agent_support import ask_safety_question, generate_safety_report, get_agent_runtime, _display_agent_line
from api.preview_telemetry import PreviewTelemetry

class SourceInput(BaseModel):
    source_type: Literal['mp4', 'usb_camera', 'rtsp']
    location: str | int


class HandlingInput(BaseModel):
    handled: bool


class PeriodInput(BaseModel):
    start_at: str
    end_at: str


class AskInput(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    start_at: str | None = None
    end_at: str | None = None


def period_bounds(start: str | None, end: str | None):
    def convert(value, final):
        if not value:
            return None
        if len(value) == 10:
            value = datetime.combine(date.fromisoformat(value), time.max if final else time.min, timezone.utc).isoformat()
        return value
    return convert(start, False), convert(end, True)


def query_from(start_at=None, end_at=None, event_type=None, status=None, source_group=None, track_id=None, limit=20, offset=0):
    start_at, end_at = period_bounds(start_at, end_at)
    try:
        return EventQuery(start_at=start_at, end_at=end_at, event_type=event_type or None, status=status or None, source_group=source_group or None, track_id=track_id, limit=limit, offset=offset)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from None


def event_json(query_service, event):
    data = event.to_dict()
    data['source'] = safe_source(query_service.sources_for_events((event,)).get(event.id))
    return data


def safe_source(raw):
    if not raw:
        return None
    if raw.startswith('mp4:'):
        return 'mp4'
    if raw.startswith('rtsp:'):
        return 'rtsp'
    if raw.startswith('usb:') and raw[4:].isdigit():
        return 'usb' + raw[4:]
    return '其他来源'


def statistics_json(stats):
    data = stats.to_dict()
    groups = {}
    for source, count in data['by_source'].items():
        label = safe_source(source)
        groups[label] = groups.get(label, 0) + count
    data['by_source'] = groups
    return data


def monitoring_status(app):
    service = app.state.monitoring
    if service is None:
        return {'state': 'idle', 'available': False, 'reason': app.state.monitoring_error, 'has_preview': False, 'recent_events': [], 'preview_fps': None, 'preview_age_ms': None}
    data = service.status().to_dict()
    data.pop('source_id', None)  # May contain an RTSP credential.
    recent = []
    for item in data['recent_events']:
        found = app.state.dashboard.query_service.get_event(item['event_id'])
        if found is not None:
            recent.append({'event_id': found.id, 'type': found.type.value,
                           'track_id': found.track_id, 'timestamp': found.timestamp,
                           'status': found.status.value, 'has_evidence': found.snapshot is not None})
    data['recent_events'] = recent
    data['available'] = bool(service.execution_enabled)
    telemetry = app.state.preview_telemetry
    data.update(telemetry.status(running=data['state'] == 'running') if telemetry else {'preview_fps': None, 'preview_age_ms': None})
    if not service.execution_enabled:
        data['reason'] = '监控执行已被配置禁用'
    if data.get('error_message'):
        data['error_message'] = '视频源或监控运行失败，请检查服务端日志与输入配置。'
    return data


def localized_projection(projection):
    data = projection.to_dict()
    data['answer'] = _display_agent_line(data['answer'])
    data['summary'] = [_display_agent_line(line) for line in data['summary']]
    data['recommendations'] = [_display_agent_line(line) for line in data['recommendations']]
    if data['answer'] == 'The request was refused by the Agent policy.':
        data['answer'] = '安全助手无法回答该问题；请询问已记录的 PPE 事件或统计。'
    return data


_REPORT_EVENT_REFERENCE = re.compile(r'^(?:EVID:)?(EVT-[A-Za-z0-9][A-Za-z0-9._:-]{0,155})$')


def report_evidence_images(projection, query_service, start, end):
    """Resolve cited snapshot references through persisted events in the report period."""
    images = []
    seen = set()
    cited_ids = set()
    snapshot_refs = set()
    for reference in projection.evidence_references:
        match = _REPORT_EVENT_REFERENCE.fullmatch(reference)
        if match:
            cited_ids.add(match.group(1))
        else:
            snapshot_refs.add(reference)
    offset = 0
    while True:
        page = query_service.query_events(query_from(start, end, limit=1000, offset=offset))
        for event in page.items:
            if event.id in seen or not (event.id in cited_ids or event.snapshot in snapshot_refs):
                continue
            seen.add(event.id)
            evidence = query_service.evidence(event.id)
            if evidence is not None and evidence.verified:
                images.append({'event_id': event.id})
        offset += len(page.items)
        if offset >= page.total_count or not page.items:
            break
    return images


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.dashboard = build_runtime()
    app.state.agent_state = SimpleNamespace(session_state={})
    app.state.agent_lock = Lock()
    app.state.monitor_lock = Lock()
    app.state.monitoring = None
    app.state.preview = None
    app.state.preview_telemetry = None
    app.state.monitoring_error = None
    try:
        # Assemble once per process; the existing worker retains its original timing.
        from web.monitoring_support import build_monitoring_runtime
        from web.monitoring_preview import PreviewChannel
        from core.association.ppe_person_association import PPEPersonAssociationAdapter
        from core.events.event_engine import EventEngine
        from core.rendering.annotated_frame import AnnotatedFrameRenderer
        from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
        from infra.database.database import Database
        from infra.database.repository import EventRepository
        from infra.database.snapshot_repository import SnapshotRepository
        from infra.storage.json_event_store import JSONEventStore
        from infra.storage.snapshot_storage import SnapshotStorage
        from services.compliance_service import ComplianceService
        from services.event_ingest_service import EventIngestService
        from services.event_service import EventService
        from services.inference_service import InferenceService
        from services.monitoring_service import MonitoringService
        from services.snapshot_service import SnapshotService
        from utils.config_loader import load_config
        settings = load_config('monitoring')['monitoring']
        inference_config = str(settings.get('inference_config', 'configs/inference.yaml'))
        detection = load_config(inference_config)['inference']['detection']
        db = Database(_validation_path('database/events.sqlite3'))
        repo = EventRepository(db)
        snapshots = SnapshotRepository(db)
        storage = SnapshotStorage(_validation_path('snapshots'))
        preview = PreviewChannel()
        app.state.preview = preview
        telemetry = PreviewTelemetry(preview.publish)
        app.state.preview_telemetry = telemetry
        app.state.monitoring = MonitoringService(
            inference_service=InferenceService(config_path=inference_config, execution_enabled=bool(settings.get('execution_enabled', False))),
            tracker=ByteTrackPersonTrackingAdapter(), association_adapter=PPEPersonAssociationAdapter(),
            compliance_service=ComplianceService(), event_service=EventService(engine=EventEngine(), store=JSONEventStore(_validation_path('logs/events.jsonl'))),
            ingest_service=EventIngestService(repo), snapshot_service=SnapshotService(repo, snapshots, storage),
            alert_service=app.state.dashboard.alert_service, event_loader=repo.get,
            execution_enabled=bool(settings.get('execution_enabled', False)), stop_timeout_seconds=float(settings.get('stop_timeout_seconds', 5.0)),
            max_recent_events=int(settings.get('max_recent_events', 20)), preview_renderer=AnnotatedFrameRenderer(detection['class_names']), preview_sink=telemetry.publish)
    except Exception:
        app.state.monitoring_error = '监控服务初始化失败；请检查服务端配置与依赖。'
    yield
    if app.state.monitoring is not None:
        app.state.monitoring.stop()


app = FastAPI(title='ODPlatform-PPE API', lifespan=lifespan, docs_url='/api/docs', redoc_url=None)


@app.exception_handler(Exception)
async def safe_error(request: Request, exc: Exception):
    return Response('{"detail":"服务处理失败，请检查服务端日志。"}', status_code=500, media_type='application/json')


@app.get('/api/v1/health')
def health():
    return {'status': 'ok'}


@app.get('/api/v1/capabilities')
def capabilities(request: Request):
    from services.configured_report_service import configured_report_client
    return {'monitoring': monitoring_status(request.app)['available'], 'monitoring_reason': request.app.state.monitoring_error, 'single_session': True, 'provider_configured': configured_report_client() is not None, 'authentication': 'local_demo'}


@app.get('/api/v1/events')
def events(request: Request, start_at: str | None = None, end_at: str | None = None, event_type: str | None = None, status: str | None = None, source_group: str | None = None, track_id: int | None = None, limit: int = Query(20, ge=1, le=1000), offset: int = Query(0, ge=0)):
    svc = request.app.state.dashboard.query_service
    page = svc.query_events(query_from(start_at, end_at, event_type, status, source_group, track_id, limit, offset))
    data = page.to_dict()
    sources = svc.sources_for_events(page.items)
    for item in data['items']:
        item['source'] = safe_source(sources.get(item['id']))
    return data


@app.get('/api/v1/events/{event_id}')
def event(request: Request, event_id: str):
    svc = request.app.state.dashboard.query_service
    found = svc.get_event(event_id)
    if found is None:
        raise HTTPException(404, '事件不存在')
    return event_json(svc, found)


@app.patch('/api/v1/events/{event_id}/handling')
def handling(request: Request, event_id: str, body: HandlingInput):
    try:
        found = request.app.state.dashboard.status_service.set_handled(event_id, handled=body.handled)
    except (EventNotFoundError, ValueError):
        raise HTTPException(404, '事件不存在') from None
    return event_json(request.app.state.dashboard.query_service, found)


@app.get('/api/v1/statistics')
def statistics(request: Request, start_at: str | None = None, end_at: str | None = None, event_type: str | None = None, status: str | None = None):
    return statistics_json(request.app.state.dashboard.query_service.statistics(query_from(start_at, end_at, event_type, status, limit=1000)))


@app.get('/api/v1/overview')
def overview(request: Request, start_at: str | None = None, end_at: str | None = None):
    svc = request.app.state.dashboard.query_service
    query = query_from(start_at, end_at, limit=5)
    stats = statistics_json(svc.statistics(query))
    page = svc.query_events(query)
    return {'statistics': stats, 'recent_events': [event_json(svc, e) for e in page.items]}


@app.get('/api/v1/evidence')
def evidence(request: Request, start_at: str | None = None, end_at: str | None = None, event_type: str | None = None, limit: int = Query(20, ge=1, le=1000), offset: int = Query(0, ge=0)):
    svc = request.app.state.dashboard.query_service
    matches = []
    cursor = 0
    while True:
        page = svc.query_events(query_from(start_at, end_at, event_type, limit=1000, offset=cursor))
        matches.extend(e for e in page.items if e.snapshot)
        cursor += len(page.items)
        if cursor >= page.total_count or not page.items:
            break
    return {'items': [event_json(svc, e) for e in matches[offset:offset + limit]], 'total_count': len(matches), 'limit': limit, 'offset': offset}


@app.get('/api/v1/evidence/{event_id}')
def evidence_item(request: Request, event_id: str):
    found = request.app.state.dashboard.query_service.evidence(event_id)
    if found is None:
        raise HTTPException(404, '证据事件不存在')
    snap = found.snapshot.to_dict() if found.snapshot else None
    if snap:
        snap.pop('relative_path', None)
    return {'event': event_json(request.app.state.dashboard.query_service, found.event), 'snapshot': snap, 'verified': found.verified, 'error': None if found.verified else '证据缺失或完整性校验失败'}


@app.get('/api/v1/evidence/{event_id}/image')
def evidence_image(request: Request, event_id: str):
    found = request.app.state.dashboard.query_service.evidence(event_id)
    if found is None or not found.verified or found.file_path is None:
        raise HTTPException(404, '已验证的证据图片不可用')
    return FileResponse(found.file_path, media_type='image/jpeg', headers={'Cache-Control': 'no-store'})


@app.get('/api/v1/monitor/status')
def monitor_status(request: Request):
    return monitoring_status(request.app)


@app.post('/api/v1/monitor/start')
def monitor_start(request: Request, body: SourceInput):
    service = request.app.state.monitoring
    if service is None:
        raise HTTPException(503, request.app.state.monitoring_error)
    try:
        source = MonitoringSourceRequest(SourceType(body.source_type), body.location)
        with request.app.state.monitor_lock:
            service.start(source)
    except MonitoringError as exc:
        raise HTTPException(409, '监控已运行或配置禁止启动' if exc.code != 'MONITORING_CONFIGURATION_INVALID' else '监控参数无效或执行已禁用') from None
    except (ValueError, TypeError):
        raise HTTPException(422, '视频源参数无效') from None
    return monitoring_status(request.app)


@app.post('/api/v1/monitor/stop')
def monitor_stop(request: Request):
    service = request.app.state.monitoring
    if service is None:
        raise HTTPException(503, request.app.state.monitoring_error)
    with request.app.state.monitor_lock:
        service.stop()
    return monitoring_status(request.app)


@app.get('/api/v1/monitor/preview')
def monitor_preview(request: Request):
    channel = request.app.state.preview
    if channel is None:
        raise HTTPException(503, '预览不可用')
    def frames():
        sequence = 0
        while True:
            sequence, jpeg = channel.after(sequence)
            yield b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(len(jpeg)).encode() + b'\r\n\r\n' + jpeg + b'\r\n'
    return StreamingResponse(frames(), media_type='multipart/x-mixed-replace; boundary=frame', headers={'Cache-Control': 'no-store'})


@app.post('/api/v1/reports/generate')
def report(request: Request, body: PeriodInput):
    start, end = period_bounds(body.start_at, body.end_at)
    try:
        with request.app.state.agent_lock:
            projection = generate_safety_report(request.app.state.agent_state, requested_period={'start_at': start, 'end_at': end})
        data = localized_projection(projection)
        data['evidence_images'] = report_evidence_images(projection, request.app.state.dashboard.query_service, start, end)
        return data
    except (ValueError, TypeError):
        raise HTTPException(422, '报告时间范围无效') from None


@app.post('/api/v1/assistant/ask')
def assistant(request: Request, body: AskInput):
    start, end = period_bounds(body.start_at, body.end_at)
    if bool(start) != bool(end):
        raise HTTPException(422, '请同时提供开始和结束日期')
    with request.app.state.agent_lock:
        runtime = get_agent_runtime(request.app.state.agent_state)
        # Normalize only the four advertised UI shortcuts. Free-form questions
        # retain their meaning and pass through the original read-only boundary.
        question = {
            '今日有哪些 PPE 违规？': 'Show event statistics',
            '统计最近的安全事件': 'Show event statistics',
            '有哪些未戴安全帽事件？': 'Show NO_HELMET event statistics',
            '总结当前安全风险': 'Summarize safety events',
        }.get(body.question.strip(), body.question)
        relative = re.fullmatch(r'最近\s*([1-9]\d{0,3})\s*(分钟|小时|天)(?:之内|内)?\s*(?:有(?:哪些|什么)|发生了哪些|有哪些)?\s*(?:PPE\s*违规|安全事件|违规事件)[？?]?', body.question.strip())
        if relative:
            amount, unit = relative.groups()
            minutes = int(amount) * {'分钟': 1, '小时': 60, '天': 1440}[unit]
            if minutes > 10080:
                raise HTTPException(422, '相对时间查询最长支持最近 7 天')
            question = 'Show event statistics'
            if not start:
                now = datetime.now(timezone.utc)
                start, end = (now - timedelta(minutes=minutes)).isoformat(), now.isoformat()
        if not start:
            stats = request.app.state.dashboard.query_service.statistics()
            start = stats.earliest_at or datetime.now(timezone.utc).date().isoformat() + 'T00:00:00Z'
            end = stats.latest_at or datetime.now(timezone.utc).date().isoformat() + 'T23:59:59Z'
        projection = ask_safety_question(request.app.state.agent_state, question=question, requested_period={'start_at': start, 'end_at': end})
    return localized_projection(projection)


DIST = ROOT / 'front' / 'dist'
if DIST.is_dir():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')
    @app.get('/{path:path}')
    def spa(path: str):
        target = (DIST / path).resolve()
        if target.is_file() and DIST in target.parents:
            return FileResponse(target)
        return FileResponse(DIST / 'index.html')
