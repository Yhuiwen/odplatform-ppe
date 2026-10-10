"""Loopback-only offline upload and durable job API (no production inference in B)."""
from __future__ import annotations

import hashlib
import asyncio
import os
import shutil
import json
import re
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse

from offline.jobs import JobError, STATES
from offline.media import clean_filename, inspect_image, inspect_video

router = APIRouter(prefix="/api/v1/offline", tags=["offline"])


class OfflineUploadLimit:
    """Bound multipart body before Starlette spools it to disk."""
    def __init__(self, app, max_bytes: int):
        self.app, self.max_bytes = app, max_bytes
        self._upload_lock = asyncio.Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] != "/api/v1/offline/jobs":
            return await self.app(scope, receive, send)
        try:
            _boundary(Request(scope))
        except HTTPException as exc:
            return await JSONResponse({"detail": exc.detail}, status_code=exc.status_code)(scope, receive, send)
        headers = dict(scope["headers"])
        if b"content-length" not in headers:
            return await JSONResponse({"detail": {"code": "LENGTH_REQUIRED", "message": "上传必须提供请求体长度"}}, status_code=411)(scope, receive, send)
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            length = self.max_bytes + 1
        if length > self.max_bytes:
            return await JSONResponse({"detail": {"code": "REQUEST_TOO_LARGE", "message": "请求体超过上限"}}, status_code=413)(scope, receive, send)
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise JobError("REQUEST_TOO_LARGE", "请求体超过上限", 413)
            return message

        async with self._upload_lock:
            try:
                return await self.app(scope, bounded_receive, send)
            except JobError as exc:
                return await JSONResponse({"detail": {"code": exc.code, "message": str(exc)}}, status_code=exc.status_code)(scope, receive, send)


def _error(exc: JobError):
    raise HTTPException(exc.status_code, {"code": exc.code, "message": str(exc)}) from None


def _boundary(request: Request):
    host = request.url.hostname
    if host not in {"127.0.0.1", "localhost", "::1"}:
        _error(JobError("LOCAL_ONLY", "离线接口仅允许本机访问", 403))
    origin = request.headers.get("origin")
    allowed_origins = {
        f"http://{host}:{request.url.port}", f"http://{host}",
        "http://127.0.0.1:5173", "http://localhost:5173",
    }
    if request.headers.get("sec-fetch-site") == "cross-site" and origin not in allowed_origins:
        _error(JobError("ORIGIN_DENIED", "跨站请求已拒绝", 403))
    if origin and origin not in allowed_origins:
        _error(JobError("ORIGIN_DENIED", "请求来源不被允许", 403))


def _public(job: dict) -> dict:
    from datetime import datetime, timezone
    elapsed = None
    if job.get("started_at"):
        end = datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00")) if job.get("completed_at") else datetime.now(timezone.utc)
        elapsed = max(0, (end - datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))).total_seconds())
    return {key: value for key, value in job.items() if key not in {"artifact_manifest"}} | {
        "elapsed_seconds": elapsed,
        "artifact_keys": [key for key in job["artifact_manifest"] if key != "events_db"],
        "artifacts_available": job["status"] == "COMPLETED" and bool(job["artifact_manifest"]),
    }


@router.get("/capabilities")
def capabilities(request: Request):
    _boundary(request)
    settings = request.app.state.offline_settings
    return {"formats": ["jpg", "jpeg", "png", "mp4"], "processor_available": request.app.state.offline_image_ready,
            "image_processor_available": request.app.state.offline_image_ready,
            "image_processor_reason": request.app.state.offline_image_reason,
            "video_processor_available": request.app.state.offline_video_ready,
            "video_processor_reason": request.app.state.offline_video_reason,
            "event_analysis_available": bool(request.app.state.offline_video_ready and request.app.state.offline_worker.processors["video"].collector_factory),
            "max_image_bytes": settings.image_max_bytes, "max_video_bytes": settings.video_max_bytes,
            "max_video_seconds": settings.video_max_seconds, "max_pixels": settings.max_pixels,
            "max_queued_jobs": settings.max_queued_jobs, "audio_output_policy": "视频输出不保留原始音轨；有音轨时必须明确确认"}


@router.post("/jobs", status_code=202)
def create_job(request: Request, file: UploadFile = File(...), audio_discard_confirmed: bool = Form(False)):
    _boundary(request)
    settings = request.app.state.offline_settings
    repo = request.app.state.offline_jobs
    storage = request.app.state.offline_storage
    job_id = None
    try:
        suffix, media_type, mime = clean_filename(file.filename or "")
        if file.content_type != mime:
            raise JobError("MEDIA_TYPE_MISMATCH", "声明的媒体类型与文件名不符", 415)
        if repo.count_queued() >= settings.max_queued_jobs:
            raise JobError("QUEUE_FULL", "离线任务队列已满", 429)
        if shutil.disk_usage(settings.root).free < settings.min_free_bytes:
            raise JobError("DISK_LOW", "剩余磁盘空间不足", 507)
        limit = settings.image_max_bytes if media_type == "image" else settings.video_max_bytes
        job_id = uuid4().hex
        storage.create(job_id)
        repo.create(job_id, media_type, file.filename, audio_discard_confirmed)
        staged = storage.path(job_id, "staging", "upload.part")
        digest, size = hashlib.sha256(), 0
        with staged.open("xb") as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > limit or size > settings.max_staging_bytes:
                    raise JobError("FILE_TOO_LARGE", "上传文件超过配置限制", 413)
                digest.update(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if size == 0:
            raise JobError("EMPTY_FILE", "文件不能为空", 422)
        metadata = inspect_image(staged, suffix, settings) if media_type == "image" else inspect_video(staged, settings)
        if media_type == "video" and metadata["has_audio"] and not audio_discard_confirmed:
            raise JobError("AUDIO_CONFIRMATION_REQUIRED", "视频含音轨；请确认未来输出标注视频不保留原始音轨", 422)
        final = storage.path(job_id, "input", "source" + suffix)
        os.replace(staged, final)
        job = repo.transition(job_id, "QUEUED", updates={"input_sha256": digest.hexdigest(), "input_size_bytes": size, **metadata})
        request.app.state.offline_worker.wake()
        return _public(job)
    except JobError as exc:
        if job_id:
            current = repo.get(job_id)
            if current and current["status"] == "VALIDATING":
                repo.transition(job_id, "FAILED", updates={"error_code": exc.code, "error_message": str(exc)})
            staged = storage.path(job_id, "staging", "upload.part")
            staged.unlink(missing_ok=True)
            if current and current["status"] == "VALIDATING":
                storage.path(job_id, "input", "source" + suffix).unlink(missing_ok=True)
        _error(exc)
    except Exception:
        if job_id:
            current = repo.get(job_id)
            if current and current["status"] == "VALIDATING":
                repo.transition(job_id, "FAILED", updates={"error_code": "UPLOAD_FAILED", "error_message": "上传或登记失败"})
            storage.path(job_id, "staging", "upload.part").unlink(missing_ok=True)
            if current and current["status"] == "VALIDATING":
                storage.path(job_id, "input", "source" + suffix).unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


@router.get("/jobs")
def list_jobs(request: Request, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
              media_type: str | None = None, status: str | None = None, start_at: str | None = None, end_at: str | None = None):
    _boundary(request)
    if media_type not in {None, "image", "video"} or status not in ({None} | STATES):
        _error(JobError("INVALID_FILTER", "查询筛选条件无效", 422))
    page = request.app.state.offline_jobs.list(limit=limit, offset=offset, media_type=media_type, status=status, start_at=start_at, end_at=end_at)
    page["items"] = [_public(item) for item in page["items"]]
    return page


def _job(request: Request, job_id: str):
    _boundary(request)
    job = request.app.state.offline_jobs.get(job_id)
    if job is None:
        _error(JobError("JOB_NOT_FOUND", "任务不存在", 404))
    return job


@router.get("/jobs/{job_id}")
def get_job(request: Request, job_id: str):
    return _public(_job(request, job_id))


@router.post("/jobs/{job_id}/cancel")
def cancel_job(request: Request, job_id: str):
    _job(request, job_id)
    try:
        job = request.app.state.offline_jobs.cancel(job_id)
        request.app.state.offline_worker.wake()
        return _public(job)
    except JobError as exc:
        _error(exc)


@router.get("/jobs/{job_id}/artifacts")
def artifacts(request: Request, job_id: str):
    job = _job(request, job_id)
    if job["status"] != "COMPLETED":
        return {"items": []}
    return {"items": [{"key": key, "size_bytes": value["size_bytes"], "sha256": value["sha256"]}
                      for key, value in job["artifact_manifest"].items() if value.get("verified") and key != "events_db"]}


@router.api_route("/jobs/{job_id}/artifacts/{key}", methods=["GET", "HEAD"])
def artifact(request: Request, job_id: str, key: str):
    job = _job(request, job_id)
    if key == "events_db":
        _error(JobError("ARTIFACT_NOT_AVAILABLE", "数据库不提供下载", 404))
    try:
        path, item = request.app.state.offline_storage.artifact(job, key, cache_verified=True)
    except JobError as exc:
        _error(exc)
    return FileResponse(path, filename=Path(item["filename"]).name, headers={"Cache-Control": "no-store"})


@router.get("/jobs/{job_id}/input-image")
def input_image(request: Request, job_id: str):
    job = _job(request, job_id)
    if job["status"] != "COMPLETED" or job["media_type"] != "image":
        _error(JobError("INPUT_NOT_AVAILABLE", "已完成图片任务的原图不可用", 404))
    suffix = {"image/jpeg": (".jpg", ".jpeg"), "image/png": (".png",)}.get(job["input_mime"], ())
    storage = request.app.state.offline_storage
    try:
        paths = [storage.path(job_id, "input", "source" + extension) for extension in suffix]
        path = next((candidate for candidate in paths if candidate.is_file()), None)
        if path is None:
            raise JobError("INPUT_NOT_AVAILABLE", "任务原图不存在", 404)
        storage.verify_file(path, {"size_bytes": job["input_size_bytes"], "sha256": job["input_sha256"]}, cache_verified=True)
    except JobError as exc:
        _error(exc)
    return FileResponse(path, media_type=job["input_mime"], headers={"Cache-Control": "no-store"})


def _event_rows(request, job_id, *, event_id=None, evidence_id=None, event_type=None, limit=20, offset=0):
    job = _job(request, job_id)
    if event_type not in {None, "NO_HELMET", "NO_VEST", "PPE_UNKNOWN"}:
        _error(JobError("INVALID_FILTER", "事件类型无效", 422))
    for identifier, prefix in ((event_id, "EVT"), (evidence_id, "EVD")):
        if identifier is not None and not re.fullmatch(prefix + r"-[0-9a-f]{32}", identifier):
            _error(JobError("NOT_FOUND", "记录不存在", 404))
    storage = request.app.state.offline_storage
    try:
        path, _ = storage.artifact(job, "events_db")
        clauses, parameters = ["o.job_id=?"], [job_id]
        for column, value in (("o.event_id", event_id), ("o.evidence_id", evidence_id), ("e.event_type", event_type)):
            if value is not None:
                clauses.append(column + "=?")
                parameters.append(value)
        where = " AND ".join(clauses)
        # Filename came exclusively from the verified manifest, not the request.
        db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        try:
            total = db.execute("SELECT COUNT(*) FROM offline_evidence o JOIN events e ON e.event_id=o.event_id WHERE " + where, parameters).fetchone()[0]
            rows = db.execute("SELECT o.metadata_json,e.created_at,e.source,e.frame_id,e.source_timestamp,e.track_id,e.event_type,e.confidence,e.bbox_json FROM offline_evidence o JOIN events e ON e.event_id=o.event_id WHERE " + where + " ORDER BY e.frame_id DESC,e.event_id LIMIT ? OFFSET ?", (*parameters, limit, offset)).fetchall()
        finally:
            db.close()
        items = []
        from offline.evidence_store import OfflineEvidenceStore
        for record in rows:
            row = json.loads(record[0])
            if (row["job_id"] != job_id or row["frame_id"] != record[3] or row["video_timestamp_seconds"] != record[4]
                or row["track_id"] != record[5] or row["event_type"] != record[6] or row["confidence"] != record[7]
                or row["bbox"] != json.loads(record[8]) or record[2] != f"offline:video:{job_id}"):
                raise JobError("EVENT_EVIDENCE_MISMATCH", "事件证据关系无效", 409)
            row.update(created_at=record[1], source=record[2])
            for variant in ("original", "annotated"):
                image_path, _ = storage.artifact(job, row[variant]["artifact_key"])
                OfflineEvidenceStore.verify(image_path, row[variant])
                # No server filename/path in API output.
                row[variant] = {key: value for key, value in row[variant].items() if key not in {"filename", "zip_path"}}
            items.append(row)
        return {"job_id": job_id, "items": items, "total": total, "limit": limit, "offset": offset}
    except JobError as exc:
        _error(exc)
    except (sqlite3.Error, ValueError, KeyError, OSError):
        _error(JobError("EVENT_RESULTS_CORRUPT", "事件结果完整性校验失败", 409))


@router.get("/jobs/{job_id}/events")
@router.get("/jobs/{job_id}/evidence")
def event_list(request: Request, job_id: str, event_type: str | None = None,
               limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return _event_rows(request, job_id, event_type=event_type, limit=limit, offset=offset)


@router.get("/jobs/{job_id}/events/{event_id}")
def event_detail(request: Request, job_id: str, event_id: str):
    page = _event_rows(request, job_id, event_id=event_id)
    if not page["items"]:
        _error(JobError("EVENT_NOT_FOUND", "事件不存在", 404))
    return page["items"][0]


@router.get("/jobs/{job_id}/evidence/{evidence_id}")
def evidence_detail(request: Request, job_id: str, evidence_id: str):
    page = _event_rows(request, job_id, evidence_id=evidence_id)
    if not page["items"]:
        _error(JobError("EVIDENCE_NOT_FOUND", "证据不存在", 404))
    return page["items"][0]


@router.get("/jobs/{job_id}/evidence/{evidence_id}/image")
def evidence_image(request: Request, job_id: str, evidence_id: str, variant: str = "annotated"):
    if variant not in {"original", "annotated"}:
        _error(JobError("INVALID_VARIANT", "证据图像类型无效", 422))
    row = evidence_detail(request, job_id, evidence_id)
    return artifact(request, job_id, row[variant]["artifact_key"])
