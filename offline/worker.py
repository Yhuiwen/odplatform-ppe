"""One persistent, bounded worker with an injectable processor contract."""
from __future__ import annotations

import threading
import os
from dataclasses import dataclass
from typing import Callable, Protocol

from offline.jobs import ArtifactPublisher, JobError, JobRepository, JobStorage


class InstanceLock:
    """OS-held lock prevents a second API process from owning the queue."""
    def __init__(self, path):
        self.path = path
        self.handle = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        self.handle.seek(0)
        self.handle.write(b"0")
        self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.handle.close()
            self.handle = None
            raise RuntimeError("offline scheduler already active; start FastAPI with one worker") from exc

    def release(self):
        if self.handle is not None:
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()
            self.handle = None


class Processor(Protocol):
    def __call__(self, context: "JobContext") -> dict[str, dict]: ...


@dataclass(frozen=True)
class JobContext:
    job: dict
    storage: JobStorage
    publisher: ArtifactPublisher
    progress: Callable[[int, int | None], None]
    cancelled: Callable[[], bool]
    record_result: Callable[[int, int, float], None] | None = None
    finalizing: Callable[[], None] | None = None
    record_video_result: Callable[[int, float], None] | None = None


class ResourceAdmission:
    """Same-process policy: never begin offline work alongside live monitoring."""
    def __init__(self, monitor_state: Callable[[], str]):
        self.monitor_state = monitor_state
        self._lock = threading.Lock()
        self.offline_job_id: str | None = None

    def reserve_offline(self, job_id: str) -> bool:
        with self._lock:
            if self.offline_job_id or self.monitor_state() in {"starting","running","stopping"}:
                return False
            self.offline_job_id = job_id
            return True

    def release_offline(self, job_id: str) -> None:
        with self._lock:
            if self.offline_job_id == job_id:
                self.offline_job_id = None

    def start_monitoring(self, start: Callable[[], object]):
        with self._lock:
            if self.offline_job_id:
                raise JobError("RESOURCE_BUSY", "离线任务正在处理，请待其完成或取消后启动实时监控", 409)
            return start()


class SingleWorker:
    """Production B has no processor, so queued jobs remain queued honestly."""
    def __init__(self, repository: JobRepository, storage: JobStorage, admission: ResourceAdmission, processor: Processor | None = None, *, processors: dict[str, Processor] | None = None):
        self.repository, self.storage, self.admission = repository, storage, admission
        self.processors = processors if processors is not None else ({"image": processor, "video": processor} if processor is not None else {})
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._run_lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="offline-single-worker", daemon=False)
        self._thread.start()

    def wake(self):
        self._wake.set()

    def close(self):
        self._stop.set()
        self._wake.set()
        if self._thread:
            # A synchronous CPU model call may not stop until its next safe checkpoint.
            self._thread.join(timeout=60)
            if self._thread.is_alive():
                raise RuntimeError("offline worker did not stop")

    def _run(self):
        while not self._stop.is_set():
            if self.processors:
                self.run_once()
            self._wake.wait(timeout=0.2)
            self._wake.clear()

    def run_once(self) -> bool:
        if not self.processors:
            return False
        if not self._run_lock.acquire(blocking=False):
            return False
        try:
            return self._consume_one()
        finally:
            self._run_lock.release()

    def _consume_one(self) -> bool:
        job = self.repository.next_queued(tuple(self.processors))
        if job is None or not self.admission.reserve_offline(job["job_id"]):
            return False
        job_id = job["job_id"]
        try:
            if self.repository.get(job_id)["status"] != "QUEUED":
                return False
            job = self.repository.transition(job_id, "PROCESSING")
            context = JobContext(
                job=job, storage=self.storage, publisher=ArtifactPublisher(self.storage),
                progress=lambda count,total: self.repository.progress(job_id,count,total),
                cancelled=lambda: self._stop.is_set() or self.repository.get(job_id)["status"] == "CANCELLING",
                record_result=lambda detections,candidates,seconds: self.repository.record_image_result(job_id,detections,candidates,seconds),
                finalizing=lambda: self.repository.transition(job_id, "ENCODING"),
                record_video_result=lambda detections,seconds: self.repository.record_video_result(job_id,detections,seconds),
            )
            manifest = self.processors[job["media_type"]](context)
            current = self.repository.get(job_id)
            if current["status"] == "CANCELLING" or self._stop.is_set():
                if current["status"] != "CANCELLING":
                    self.repository.transition(job_id,"CANCELLING")
                self.repository.transition(job_id,"CANCELLED")
            elif not manifest:
                self.repository.transition(job_id,"FAILED", updates={"error_code":"NO_VERIFIED_OUTPUT","error_message":"处理器没有提供已验证产物"})
            else:
                self.storage.verify_manifest(job_id, manifest)
                self.repository.transition(job_id,"COMPLETED", updates={"artifact_manifest":manifest,"progress_percent":100.0})
        except Exception as exc:
            current = self.repository.get(job_id)
            if current and current["status"] in {"PROCESSING","ENCODING","CANCELLING"}:
                code = exc.code if isinstance(exc, JobError) else "PROCESSOR_FAILED"
                message = str(exc) if isinstance(exc, JobError) else "离线处理失败"
                if code == "JOB_CANCELLED" and self._stop.is_set() and current["status"] != "CANCELLING":
                    current = self.repository.transition(job_id,"CANCELLING")
                self.repository.transition(job_id,"CANCELLED" if current["status"] == "CANCELLING" else "FAILED", updates={"error_code":code,"error_message":message})
        finally:
            try:
                current = self.repository.get(job_id)
                if current and current["status"] in {"CANCELLED", "FAILED", "INTERRUPTED"}:
                    from offline.jobs import cleanup_generated
                    try:
                        cleanup_generated(self.storage, job_id)
                    except OSError:
                        # Job remains unavailable; startup retries owned cleanup.
                        pass
            finally:
                self.admission.release_offline(job_id)
        return True
