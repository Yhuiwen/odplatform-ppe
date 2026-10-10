from __future__ import annotations

import hashlib
from pathlib import Path
from threading import Event, Thread

import pytest

from offline.jobs import ArtifactPublisher, JobError, JobRepository, JobStorage, sha256_file
from offline.worker import InstanceLock, ResourceAdmission, SingleWorker


@pytest.fixture
def system(tmp_path):
    storage = JobStorage(tmp_path / "offline")
    repository = JobRepository(storage.root / "jobs.sqlite3")
    return storage, repository


def new_job(system, job_id):
    storage, repository = system
    storage.create(job_id)
    repository.create(job_id, "image", "x.png", False)
    repository.transition(job_id, "QUEUED")
    return job_id


def test_migration_and_state_recovery(system):
    storage, repo = system
    one, two = new_job(system, "1" * 32), new_job(system, "2" * 32)
    assert repo.list(limit=1)["total_count"] == 2
    repo.transition(one, "PROCESSING")
    repo.progress(one, 1, 2)
    with pytest.raises(JobError):
        repo.transition(one, "QUEUED")
    assert repo.cancel(two)["status"] == "CANCELLED"
    assert repo.cancel(two)["status"] == "CANCELLED"
    repo.recover()
    assert JobRepository(repo.path).get(one)["status"] == "INTERRUPTED"
    assert repo.get(two)["status"] == "CANCELLED"
    with repo._connect() as db:
        assert db.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 2


def test_worker_fake_processor_and_artifact_integrity(system):
    storage, repo = system
    job_id = new_job(system, "3" * 32)
    admission = ResourceAdmission(lambda: "idle")

    def processor(context):
        context.progress(1, 1)
        context.record_result(1, 0, 0.01)
        staged = storage.path(job_id, "staging", "result.bin")
        staged.write_bytes(b"verified test output")
        return {"result": context.publisher.publish(job_id, "result", "result.bin", sha256_file(staged))}

    worker = SingleWorker(repo, storage, admission, processor)
    assert worker.run_once()
    job = repo.get(job_id)
    assert job["status"] == "COMPLETED"
    assert storage.artifact(job, "result")[0].read_bytes() == b"verified test output"
    storage.path(job_id, "output", "result.bin").write_bytes(b"tampered")
    with pytest.raises(JobError, match="完整性"):
        storage.artifact(job, "result")


def test_resource_admission_and_failure(system):
    storage, repo = system
    job_id = new_job(system, "4" * 32)
    admission = ResourceAdmission(lambda: "running")
    worker = SingleWorker(repo, storage, admission, lambda context: {})
    assert worker.run_once() is False
    assert repo.get(job_id)["status"] == "QUEUED"
    assert admission.reserve_offline("other") is False
    admission.monitor_state = lambda: "idle"
    assert admission.reserve_offline("other")
    with pytest.raises(JobError):
        admission.start_monitoring(lambda: None)
    admission.release_offline("other")
    assert worker.run_once()
    assert repo.get(job_id)["status"] == "FAILED"


def test_instance_lock(system):
    storage, _ = system
    first = InstanceLock(storage.root / ".worker.lock")
    second = InstanceLock(storage.root / ".worker.lock")
    first.acquire()
    try:
        with pytest.raises(RuntimeError):
            second.acquire()
    finally:
        first.release()
    second.acquire()
    second.release()


def test_processing_cancel_and_single_execution(system):
    storage, repo = system
    job_id = new_job(system, "5" * 32)
    entered, release = Event(), Event()
    calls = []

    def processor(context):
        calls.append(context.job["job_id"])
        entered.set()
        assert release.wait(3)
        assert context.cancelled()
        return {}

    worker = SingleWorker(repo, storage, ResourceAdmission(lambda: "idle"), processor)
    thread = Thread(target=worker.run_once)
    thread.start()
    assert entered.wait(3)
    assert worker.run_once() is False
    assert repo.cancel(job_id)["status"] == "CANCELLING"
    release.set()
    thread.join(3)
    assert not thread.is_alive()
    assert calls == [job_id]
    assert repo.get(job_id)["status"] == "CANCELLED"


def test_unsupported_mp4_does_not_block_images(system):
    storage, repo = system
    video_id = "0" * 32
    storage.create(video_id)
    repo.create(video_id, "video", "clip.mp4", True)
    repo.transition(video_id, "QUEUED")
    images = [new_job(system, digit * 32) for digit in ("6", "7")]

    def image_processor(context):
        job_id = context.job["job_id"]
        staged = storage.path(job_id, "staging", "result.bin")
        staged.write_bytes(b"unit-only")
        context.record_result(0, 0, 0.01)
        return {"result": context.publisher.publish(job_id, "result", "result.bin", sha256_file(staged))}

    worker = SingleWorker(repo, storage, ResourceAdmission(lambda: "idle"), processors={"image": image_processor})
    assert worker.run_once() and worker.run_once()
    assert worker.run_once() is False
    assert repo.get(video_id)["status"] == "QUEUED"
    assert all(repo.get(job_id)["status"] == "COMPLETED" for job_id in images)


def test_v1_database_migrates_without_losing_jobs(tmp_path):
    import sqlite3
    from offline.jobs import utc_now
    path = tmp_path / "jobs.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        db.executescript((Path(__file__).resolve().parents[2] / "offline" / "migrations" / "0001_jobs.sql").read_text(encoding="utf-8"))
        db.execute("INSERT INTO schema_migrations VALUES(1, ?)", (utc_now(),))
        db.execute("INSERT INTO jobs(job_id,media_type,original_filename,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                   ("8" * 32, "video", "old.mp4", "QUEUED", utc_now(), utc_now()))
    repo = JobRepository(path)
    assert repo.get("8" * 32)["status"] == "QUEUED"
    with repo._connect() as db:
        assert db.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 2
