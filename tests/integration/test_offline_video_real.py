"""Local authorized real model/video runs, never downloads substitute resources."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import threading
import time

import pytest
pytest.importorskip("fastapi")
from api.main import app
from fastapi.testclient import TestClient
from core.schemas.events import EventQuery
import psutil


@pytest.mark.parametrize("relative,expected", [
    ("artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4",47),
    ("artifacts/validation/test/4afa6b121fe5db806c3ff416bafdf571.mp4",570),
])
def test_real_full_frame_video(tmp_path, monkeypatch, relative, expected):
    source = Path(relative)
    if not source.exists() or not Path("models/checkpoints/EXP-001/best.pt").exists() or not shutil.which("ffmpeg"):
        pytest.skip("local verified video/model/encoder missing: NOT_EXECUTED")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT",str(tmp_path / "jobs"))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION","1")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_VIDEO_EXECUTION","1")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_EVENT_EXECUTION","0")
    stop = threading.Event()
    process = psutil.Process()
    peak = [process.memory_info().rss]
    def sample():
        while not stop.wait(.1):
            peak[0] = max(peak[0],process.memory_info().rss)
    sampler = threading.Thread(target=sample)
    sampler.start()
    start = time.monotonic()
    cpu_start = process.cpu_times()
    try:
        with TestClient(app,base_url="http://127.0.0.1:8000") as http:
            before_events = app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count
            assert http.get("/api/v1/offline/capabilities").json()["video_processor_available"]
            with source.open("rb") as input_file:
                result = http.post("/api/v1/offline/jobs", files={"file":("sample.mp4",input_file,"video/mp4")},data={"audio_discard_confirmed":"true"})
            assert result.status_code == 202, result.text
            job_id = result.json()["job_id"]
            deadline = time.monotonic()+600
            statuses = set()
            while time.monotonic() < deadline:
                job = http.get(f"/api/v1/offline/jobs/{job_id}").json()
                statuses.add(job["status"])
                if job["status"] != "COMPLETED":
                    assert job["progress_percent"] is None or job["progress_percent"] < 100
                if job["status"] in {"COMPLETED","FAILED","CANCELLED","INTERRUPTED"}:
                    break
                time.sleep(.1)
            assert job["status"] == "COMPLETED", job
            assert job["processed_frames"] == expected
            downloaded = {}
            manifest = http.get(f"/api/v1/offline/jobs/{job_id}/artifacts").json()["items"]
            for item in manifest:
                response = http.get(f"/api/v1/offline/jobs/{job_id}/artifacts/{item['key']}")
                assert response.status_code == 200
                assert hashlib.sha256(response.content).hexdigest() == item["sha256"]
                downloaded[item["key"]] = response.content
            verification = json.loads(downloaded["video_verification"])
            for key in ("input_decoded_frames","inferred_frames","rendered_frames","written_frames","output_decoded_frames"):
                assert verification[key] == expected
            summary = json.loads(downloaded["summary"])
            assert summary["confirmed_events"] is None and summary["event_analysis_status"] == "NOT_IMPLEMENTED"
            assert len(downloaded["frames"].splitlines()) == expected
            destination = Path("artifacts/validation/v12d") / str(expected)
            destination.mkdir(parents=True,exist_ok=True)
            for key,payload in downloaded.items():
                if key == "results":
                    # The locked source-asset audit treats every repository ZIP as
                    # an unregistered training/data archive. Keep this generated
                    # download in the isolated test root, without weakening it.
                    (tmp_path/"downloaded-results.zip").write_bytes(payload)
                    continue
                filename = {"annotated":"annotated.mp4","frames":"frames.jsonl","summary":"summary.json","video_verification":"video_verification.json","results":"results.zip"}[key]
                (destination/filename).write_bytes(payload)
            metrics = {"wall_seconds":time.monotonic()-start,"peak_rss_bytes":peak[0],"end_rss_bytes":process.memory_info().rss,
                       "statuses":sorted(statuses),"encoder_children_remaining":[child.name() for child in process.children() if "ffmpeg" in child.name().lower()],
                       "summary":summary,"verification":verification}
            assert metrics["encoder_children_remaining"] == []
            if expected == 570:
                detector = app.state.offline_worker.processors["image"].detector
                identity = id(detector._model)
                repeat_source = Path("artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4")
                with repeat_source.open("rb") as handle:
                    repeat = http.post("/api/v1/offline/jobs",files={"file":("repeat.mp4",handle,"video/mp4")})
                assert repeat.status_code == 202
                repeat_id = repeat.json()["job_id"]
                repeat_deadline = time.monotonic()+120
                while time.monotonic()<repeat_deadline:
                    repeat_job = http.get(f"/api/v1/offline/jobs/{repeat_id}").json()
                    if repeat_job["status"] in {"COMPLETED","FAILED","CANCELLED"}:
                        break
                    time.sleep(.1)
                assert repeat_job["status"]=="COMPLETED",repeat_job
                assert id(detector._model)==identity
                release_deadline = time.monotonic()+5
                while app.state.offline_admission.offline_job_id is not None and time.monotonic()<release_deadline:
                    time.sleep(.01)
                assert app.state.offline_admission.offline_job_id is None
                metrics["sequential_repeat_frames"] = repeat_job["processed_frames"]
                metrics["rss_after_repeat_bytes"] = process.memory_info().rss
            assert app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count == before_events
            cpu_end = process.cpu_times()
            metrics["cpu_user_seconds"] = cpu_end.user-cpu_start.user
            metrics["cpu_system_seconds"] = cpu_end.system-cpu_start.system
            (destination/"runtime_metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
            print("REAL_VIDEO_RESULT",json.dumps(metrics))
    finally:
        stop.set()
        sampler.join(2)
