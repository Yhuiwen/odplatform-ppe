"""Restart cleans only known interrupted video outputs, preserving input/queue."""
from pathlib import Path
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from api.main import app
from offline.jobs import JobStorage,JobRepository,sha256_file
from offline.video_processor import OUTPUTS


def test_video_restart_recovery(tmp_path,monkeypatch):
    root=tmp_path/"jobs"
    storage=JobStorage(root)
    repo=JobRepository(root/"jobs.sqlite3")
    ids=[]
    for digit,status in (("1","PROCESSING"),("2","ENCODING"),("3","CANCELLING"),("4","QUEUED")):
        job_id=digit*32
        ids.append(job_id)
        storage.create(job_id)
        source=storage.path(job_id,"input","source.mp4")
        source.write_bytes(b"owned original upload")
        repo.create(job_id,"video","sample.mp4",True)
        repo.transition(job_id,"QUEUED",updates={"input_sha256":sha256_file(source),"input_size_bytes":source.stat().st_size})
        if status!="QUEUED":
            repo.transition(job_id,"PROCESSING")
            if status=="ENCODING":
                repo.transition(job_id,"ENCODING")
            elif status=="CANCELLING":
                repo.cancel(job_id)
            for section in ("staging","output"):
                for name in OUTPUTS:
                    storage.path(job_id,section,name).write_bytes(b"unverified")
                for name in ("events.sqlite3", "events.sqlite3-wal", "events.sqlite3-shm", "events.json", "events.csv", "evidence_index.json", "original_EVT-"+"f"*32+".png", "annotated_EVT-"+"f"*32+".png.part"):
                    storage.path(job_id,section,name).write_bytes(b"unverified E data")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT",str(root))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION","0")
    with TestClient(app,base_url="http://127.0.0.1:8000") as http:
        for job_id in ids:
            job=http.get(f"/api/v1/offline/jobs/{job_id}").json()
            assert job["status"]==("QUEUED" if job_id==ids[-1] else "INTERRUPTED")
            assert storage.path(job_id,"input","source.mp4").read_bytes()==b"owned original upload"
            assert http.get(f"/api/v1/offline/jobs/{job_id}/artifacts").json()=={"items":[]}
            for section in ("staging","output"):
                assert not list(storage.path(job_id,section,"annotated.mp4").parent.iterdir())
