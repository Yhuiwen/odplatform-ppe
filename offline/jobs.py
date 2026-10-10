"""Durable offline-job records, explicit transitions and confined storage."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import tomllib
from collections import OrderedDict
from threading import RLock
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class JobError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 409):
        super().__init__(message)
        self.code, self.status_code = code, status_code


STATES = frozenset({"VALIDATING", "QUEUED", "PROCESSING", "ENCODING", "CANCELLING", "COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"})
TRANSITIONS = {
    "VALIDATING": {"QUEUED", "FAILED"},
    "QUEUED": {"PROCESSING", "CANCELLED", "FAILED"},
    "PROCESSING": {"ENCODING", "COMPLETED", "CANCELLING", "FAILED", "INTERRUPTED"},
    "ENCODING": {"COMPLETED", "CANCELLING", "FAILED", "INTERRUPTED"},
    "CANCELLING": {"CANCELLED", "FAILED", "INTERRUPTED"},
    "INTERRUPTED": set(), "COMPLETED": set(), "FAILED": set(), "CANCELLED": set(),
}
JOB_ID = re.compile(r"[0-9a-f]{32}\Z")
ARTIFACT_KEY = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


@dataclass(frozen=True)
class OfflineSettings:
    root: Path
    image_max_bytes: int = 20 * 1024 * 1024
    video_max_bytes: int = 512 * 1024 * 1024
    video_max_seconds: int = 600
    max_pixels: int = 3840 * 2160
    max_queued_jobs: int = 20
    min_free_bytes: int = 1024 * 1024 * 1024
    max_staging_bytes: int = 1024 * 1024 * 1024
    ffprobe_timeout_seconds: int = 15
    image_execution_enabled: bool = False
    image_config_sha256: str | None = None

    @classmethod
    def load(cls, root: Path, config: Path) -> "OfflineSettings":
        with config.open("rb") as handle:
            values = tomllib.load(handle)["offline"]
        if any(type(v) is not int or v <= 0 for k, v in values.items() if k not in {"image_execution_enabled", "image_config_sha256"}):
            raise ValueError("offline limits must be positive integers")
        if type(values.get("image_execution_enabled")) is not bool:
            raise ValueError("image execution setting must be boolean")
        fingerprint = values.get("image_config_sha256")
        if fingerprint is not None and (not isinstance(fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None):
            raise ValueError("image inference configuration fingerprint is invalid")
        return cls(root=root.resolve(), **values)


class JobRepository:
    """One SQLite database separate from the V1 realtime event database."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _init_schema(self):
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
            version = db.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] or 0
            if version > 2:
                raise RuntimeError("offline database schema is newer than this application")
            if version == 0:
                db.executescript((Path(__file__).parent / "migrations" / "0001_jobs.sql").read_text(encoding="utf-8"))
                db.execute("INSERT INTO schema_migrations VALUES(1, ?)", (utc_now(),))
                version = 1
            if version == 1:
                db.executescript((Path(__file__).parent / "migrations" / "0002_image_results.sql").read_text(encoding="utf-8"))
                db.execute("INSERT INTO schema_migrations VALUES(2, ?)", (utc_now(),))

    @staticmethod
    def _row(row):
        if row is None:
            return None
        data = dict(row)
        data["has_audio"] = None if data["has_audio"] is None else bool(data["has_audio"])
        data["audio_discard_confirmed"] = bool(data["audio_discard_confirmed"])
        data["artifact_manifest"] = json.loads(data["artifact_manifest"])
        return data

    def create(self, job_id: str, media_type: str, filename: str, audio_confirmed: bool) -> dict:
        now = utc_now()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO jobs(job_id,media_type,original_filename,audio_discard_confirmed,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                       (job_id, media_type, filename, int(audio_confirmed), "VALIDATING", now, now))
        return self.get(job_id)

    def get(self, job_id: str) -> dict | None:
        with self._connect() as db:
            return self._row(db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone())

    def list(self, *, limit=20, offset=0, media_type=None, status=None, start_at=None, end_at=None) -> dict:
        filters, args = [], []
        for col, value, op in (("media_type",media_type,"="),("status",status,"="),("created_at",start_at,">="),("created_at",end_at,"<=")):
            if value is not None:
                filters.append(f"{col} {op} ?")
                args.append(value)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        with self._connect() as db:
            total = db.execute("SELECT COUNT(*) FROM jobs" + where, args).fetchone()[0]
            rows = db.execute("SELECT * FROM jobs" + where + " ORDER BY created_at DESC, job_id DESC LIMIT ? OFFSET ?", (*args,limit,offset)).fetchall()
        return {"items": [self._row(row) for row in rows], "total_count": total, "limit": limit, "offset": offset}

    def count_queued(self) -> int:
        with self._connect() as db:
            return db.execute("SELECT COUNT(*) FROM jobs WHERE status='QUEUED'").fetchone()[0]

    def next_queued(self, media_types: tuple[str, ...] | None = None) -> dict | None:
        with self._connect() as db:
            if media_types is not None:
                if not media_types:
                    return None
                placeholders = ",".join("?" for _ in media_types)
                row = db.execute(f"SELECT * FROM jobs WHERE status='QUEUED' AND media_type IN ({placeholders}) ORDER BY created_at, rowid LIMIT 1", media_types).fetchone()
            else:
                row = db.execute("SELECT * FROM jobs WHERE status='QUEUED' ORDER BY created_at, rowid LIMIT 1").fetchone()
            return self._row(row)

    def transition(self, job_id: str, target: str, *, updates: dict | None = None) -> dict:
        if target not in STATES:
            raise JobError("INVALID_STATUS", "任务状态无效", 422)
        updates = updates or {}
        permitted = {"input_sha256","input_size_bytes","input_mime","input_codec","input_width","input_height","input_fps","input_frame_count","input_duration_seconds","has_audio","processed_frames","total_frames","progress_percent","error_code","error_message","artifact_manifest","detection_count","candidate_count","processing_seconds"}
        if set(updates) - permitted:
            raise JobError("INVALID_UPDATE", "任务更新字段无效", 422)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise JobError("JOB_NOT_FOUND", "任务不存在", 404)
            if target not in TRANSITIONS[row["status"]]:
                raise JobError("INVALID_TRANSITION", "任务状态不允许这样转换")
            if target == "COMPLETED":
                manifest = updates.get("artifact_manifest", row["artifact_manifest"])
                if isinstance(manifest, str):
                    manifest = json.loads(manifest)
                if not manifest or not all(item.get("verified") for item in manifest.values()):
                    raise JobError("ARTIFACT_NOT_VERIFIED", "未验证产物，不能完成任务")
                updates["artifact_manifest"] = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
                if row["media_type"] == "image" and (row["detection_count"] is None or row["candidate_count"] is None):
                    raise JobError("RESULT_INCOMPLETE", "图片统计结果不完整")
            updates["updated_at"] = utc_now()
            if target == "PROCESSING":
                updates["started_at"] = updates["updated_at"]
            if target in {"COMPLETED","FAILED","CANCELLED","INTERRUPTED"}:
                updates["completed_at"] = updates["updated_at"]
            columns = ",".join(["status=?"] + [f"{key}=?" for key in updates])
            db.execute(f"UPDATE jobs SET {columns} WHERE job_id=?", (target, *updates.values(), job_id))
        return self.get(job_id)

    def progress(self, job_id: str, processed: int, total: int | None) -> dict:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status,processed_frames,media_type FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise JobError("JOB_NOT_FOUND", "任务不存在", 404)
            if row["status"] not in {"PROCESSING","ENCODING","CANCELLING"} or processed < row["processed_frames"] or (total is not None and processed > total):
                raise JobError("INVALID_PROGRESS", "任务进度无效")
            percent = None if total is None or total == 0 else round(processed * 100 / total, 2)
            if row["media_type"] == "video" and percent is not None:
                percent = min(percent, 99.0)
            db.execute("UPDATE jobs SET processed_frames=?,total_frames=?,progress_percent=?,updated_at=? WHERE job_id=?", (processed,total,percent,utc_now(),job_id))
        return self.get(job_id)

    def record_image_result(self, job_id: str, detections: int, candidates: int, seconds: float) -> dict:
        if any(type(value) is not int or value < 0 for value in (detections, candidates)) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise JobError("INVALID_RESULT", "图片统计结果无效")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status,media_type FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None or row["status"] != "PROCESSING" or row["media_type"] != "image":
                raise JobError("INVALID_RESULT", "当前任务不能登记图片结果")
            db.execute("UPDATE jobs SET detection_count=?,candidate_count=?,processing_seconds=?,updated_at=? WHERE job_id=?", (detections,candidates,float(seconds),utc_now(),job_id))
        return self.get(job_id)

    def cancel(self, job_id: str) -> dict:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise JobError("JOB_NOT_FOUND", "任务不存在", 404)
            status = row["status"]
            if status == "VALIDATING":
                raise JobError("VALIDATION_IN_PROGRESS", "上传校验尚未完成，请稍后重试")
            if status == "QUEUED":
                now = utc_now()
                db.execute("UPDATE jobs SET status='CANCELLED',updated_at=?,completed_at=? WHERE job_id=?", (now,now,job_id))
            elif status in {"PROCESSING", "ENCODING"}:
                db.execute("UPDATE jobs SET status='CANCELLING',updated_at=? WHERE job_id=?", (utc_now(),job_id))
        return self.get(job_id)

    def record_video_result(self, job_id: str, detections: int, seconds: float) -> dict:
        if type(detections) is not int or detections < 0 or not isinstance(seconds, (float,int)) or not math.isfinite(seconds) or seconds < 0:
            raise JobError("INVALID_RESULT", "视频统计结果无效")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status,media_type FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None or row["status"] != "ENCODING" or row["media_type"] != "video":
                raise JobError("INVALID_RESULT", "当前任务不能登记视频结果")
            db.execute("UPDATE jobs SET detection_count=?,processing_seconds=?,updated_at=? WHERE job_id=?", (detections,float(seconds),utc_now(),job_id))
        return self.get(job_id)

    def recover(self) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            now = utc_now()
            db.execute("UPDATE jobs SET status='INTERRUPTED',error_code='PROCESS_INTERRUPTED',error_message='服务退出，任务未完成；需要新建任务重新处理',updated_at=?,completed_at=? WHERE status IN ('PROCESSING','ENCODING','CANCELLING')", (now,now))
            db.execute("UPDATE jobs SET status='FAILED',error_code='UPLOAD_INTERRUPTED',error_message='上传未完成',updated_at=?,completed_at=? WHERE status='VALIDATING'", (now,now))


class JobStorage:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._verified_cache = OrderedDict()
        self._verification_lock = RLock()

    def directory(self, job_id: str) -> Path:
        if not JOB_ID.fullmatch(job_id):
            raise JobError("INVALID_JOB_ID", "任务编号无效", 404)
        directory = self.root / job_id
        if directory.is_symlink() or (directory.exists() and directory.resolve() != directory):
            raise JobError("UNSAFE_PATH", "任务目录无效", 403)
        return directory

    def create(self, job_id: str) -> Path:
        directory = self.directory(job_id)
        directory.mkdir(exist_ok=False)
        for name in ("input", "staging", "output", "evidence", "metadata"):
            (directory / name).mkdir()
        return directory

    def path(self, job_id: str, section: str, filename: str) -> Path:
        if section not in {"input", "staging", "output", "evidence", "metadata"} or not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
            raise JobError("UNSAFE_PATH", "文件路径无效", 403)
        base = self.directory(job_id) / section
        if base.is_symlink() or not base.is_dir():
            raise JobError("UNSAFE_PATH", "任务目录无效", 403)
        target = base / filename
        if target.is_symlink() or target.resolve().parent != base:
            raise JobError("UNSAFE_PATH", "文件路径无效", 403)
        return target

    def artifact(self, job: dict, key: str, *, cache_verified: bool = False) -> tuple[Path, dict]:
        if not ARTIFACT_KEY.fullmatch(key):
            raise JobError("INVALID_ARTIFACT_KEY", "产物编号无效", 404)
        item = job["artifact_manifest"].get(key)
        if job["status"] != "COMPLETED" or not item or not item.get("verified"):
            raise JobError("ARTIFACT_NOT_AVAILABLE", "已验证产物不可用", 404)
        path = self.path(job["job_id"], "output", item["filename"])
        self.verify_file(path, item, cache_verified=cache_verified)
        return path, item

    def verify_file(self, path, item, *, cache_verified=False):
        """Published files are write-once; invalidate on identity/size/mtime/ctime change.

        A bounded process-local cache avoids full-video hashing per HTTP Range.
        External concurrent mutation during streaming is outside the local trust model.
        """
        def signature():
            stat = path.stat()
            return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        with self._verification_lock:
            try:
                before = signature()
                key = (str(path), item["sha256"], item["size_bytes"])
                if not path.is_file() or before[2] != item["size_bytes"]:
                    raise OSError()
                if cache_verified and self._verified_cache.get(key) == before:
                    self._verified_cache.move_to_end(key)
                    return
                if sha256_file(path) != item["sha256"] or signature() != before:
                    raise OSError()
                if cache_verified:
                    self._verified_cache[key] = before
                    while len(self._verified_cache) > 64:
                        self._verified_cache.popitem(last=False)
            except OSError:
                self._verified_cache.clear()
                raise JobError("ARTIFACT_CORRUPT", "产物完整性校验失败", 409) from None

    def verify_manifest(self, job_id: str, manifest: dict) -> None:
        if not manifest:
            raise JobError("ARTIFACT_NOT_VERIFIED", "未验证产物，不能完成任务")
        for key, item in manifest.items():
            if not ARTIFACT_KEY.fullmatch(key) or not isinstance(item, dict) or not item.get("verified"):
                raise JobError("ARTIFACT_NOT_VERIFIED", "产物清单无效")
            path = self.path(job_id, "output", item.get("filename", ""))
            if not path.is_file() or path.stat().st_size != item.get("size_bytes") or sha256_file(path) != item.get("sha256"):
                raise JobError("ARTIFACT_CORRUPT", "产物完整性校验失败")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ArtifactPublisher:
    """Only verified staged files may become a completed job's manifest."""
    def __init__(self, storage: JobStorage):
        self.storage = storage

    def publish(self, job_id: str, key: str, filename: str, expected_sha256: str) -> dict:
        if not ARTIFACT_KEY.fullmatch(key):
            raise JobError("INVALID_ARTIFACT_KEY", "产物编号无效", 422)
        staged = self.storage.path(job_id, "staging", filename)
        final = self.storage.path(job_id, "output", filename)
        if not staged.is_file() or final.exists():
            raise JobError("ARTIFACT_NOT_AVAILABLE", "产物不可用")
        observed = sha256_file(staged)
        if observed != expected_sha256 or staged.stat().st_size == 0:
            raise JobError("ARTIFACT_CORRUPT", "产物完整性校验失败")
        os.replace(staged, final)
        return {"filename": filename, "sha256": observed, "size_bytes": final.stat().st_size, "verified": True}


def cleanup_generated(storage, job_id):
    """Remove only generated filenames inside this known job; never its input."""
    pattern = re.compile(r"(?:annotated\.(?:mp4|png)|frames\.jsonl|detections\.json|summary\.json|video_verification\.json|results\.zip|events\.(?:json|csv|sqlite3(?:-wal|-shm)?)|evidence_index\.json|(?:original|annotated)_EVT-[0-9a-f]{32}\.png(?:\.part)?)")
    for section in ("staging", "output"):
        base = storage.path(job_id, section, "summary.json").parent
        for entry in base.iterdir():
            if pattern.fullmatch(entry.name):
                storage.path(job_id, section, entry.name).unlink(missing_ok=True)
