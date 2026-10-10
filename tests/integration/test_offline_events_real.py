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
def test_real_video_events_evidence(tmp_path, monkeypatch, relative, expected):
    source = Path(relative)
    if not source.exists() or not Path("models/checkpoints/EXP-001/best.pt").exists() or not shutil.which("ffmpeg"):
        pytest.skip("local verified video/model/encoder missing: NOT_EXECUTED")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT",str(tmp_path / "jobs"))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION","1")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_VIDEO_EXECUTION","1")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_EVENT_EXECUTION","1")
    stop = threading.Event()
    process = psutil.Process()
    peak = [process.memory_info().rss]
    encoder_peak = [0]
    def sample():
        while not stop.wait(.1):
            peak[0] = max(peak[0],process.memory_info().rss)
            try:
                encoder_peak[0] = max(encoder_peak[0],sum(child.memory_info().rss for child in process.children() if "ffmpeg" in child.name().lower()))
            except psutil.Error:
                pass
    sampler = threading.Thread(target=sample)
    sampler.start()
    start = time.monotonic()
    cpu_start = process.cpu_times()
    try:
        with TestClient(app,base_url="http://127.0.0.1:8000") as http:
            inference_calls = {}
            inference = app.state.offline_worker.processors["image"].inference
            infer_frame = inference.infer_frame
            def observed_infer(frame, *, source):
                inference_calls.setdefault(source, []).append(frame.frame_id)
                return infer_frame(frame,source=source)
            inference.infer_frame = observed_infer
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
            if job["status"] != "COMPLETED":
                print("REAL_EVENT_FAILURE", json.dumps({key:job.get(key) for key in ("job_id","status","error_code","error_message","processed_frames")}))
            assert job["status"] == "COMPLETED", job
            assert job["processed_frames"] == expected
            assert inference_calls[f"offline:video:{job_id}"] == list(range(expected))
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
            assert summary["event_analysis_status"] == "COMPLETED"
            assert summary["event_analysis_frames"] == expected
            assert summary["confirmed_events"] == sum(summary["events_by_type"].values())
            assert summary["evidence_image_files"] == 2 * summary["confirmed_events"]
            import zipfile, io
            events = json.loads(downloaded["events"])["items"]
            index = json.loads(downloaded["evidence_index"])["items"]
            assert len(events) == len(index) == summary["confirmed_events"]
            with zipfile.ZipFile(io.BytesIO(downloaded["results"])) as archive:
                assert archive.testzip() is None
                assert len(archive.namelist()) == len(set(archive.namelist()))
                assert not any(".." in name or name.startswith("/") for name in archive.namelist())
                assert "events.sqlite3" not in archive.namelist()
                assert archive.getinfo("annotated.mp4").compress_type == zipfile.ZIP_STORED
                for row in events:
                    assert row["job_id"] == job_id
                    assert row["video_timestamp_seconds"] == row["frame_id"] / summary["playback_fps"]
                    details = http.get(f"/api/v1/offline/jobs/{job_id}/events/{row['event_id']}")
                    assert details.status_code == 200
                    for variant in ("original", "annotated"):
                        payload = http.get(f"/api/v1/offline/jobs/{job_id}/evidence/{row['evidence_id']}/image",params={"variant":variant})
                        assert payload.status_code == 200
                        assert hashlib.sha256(payload.content).hexdigest() == row[variant]["sha256"]
                        assert archive.read(row[variant]["zip_path"]) == payload.content
                        from PIL import Image
                        with Image.open(io.BytesIO(payload.content)) as png:
                            assert png.size == (1280,720)
                            png.verify()
            assert http.get(f"/api/v1/offline/jobs/{job_id}/events",params={"limit":1}).json()["total"] == len(events)
            assert http.get(f"/api/v1/offline/jobs/{job_id}/artifacts/events_db").status_code == 404
            # Raw original evidence must equal the untouched decoded trigger frame.
            from core.video.reader import VideoReader
            by_frame = {row["frame_id"]: row for row in events}
            with VideoReader(source) as reader:
                for frame in reader:
                    if frame.frame_id in by_frame:
                        import cv2
                        row = by_frame[frame.frame_id]
                        raw = cv2.imdecode(__import__("numpy").frombuffer(downloaded[row["original"]["artifact_key"]],dtype="uint8"),cv2.IMREAD_COLOR)
                        assert __import__("numpy").array_equal(raw,frame.image)
            assert len(downloaded["frames"].splitlines()) == expected
            destination = Path("artifacts/validation/v12e") / str(expected) / job_id
            destination.mkdir(parents=True,exist_ok=True)
            for key,payload in downloaded.items():
                if key == "results":
                    # The locked source-asset audit treats every repository ZIP as
                    # an unregistered training/data archive. Keep this generated
                    # download in the isolated test root, without weakening it.
                    (tmp_path/"downloaded-results.zip").write_bytes(payload)
                    continue
                filename = app.state.offline_jobs.get(job_id)["artifact_manifest"][key]["filename"]
                (destination/filename).write_bytes(payload)
            metrics = {"wall_seconds":time.monotonic()-start,"task_processing_seconds":job["processing_seconds"],"ffmpeg_peak_rss_bytes":encoder_peak[0],"peak_rss_bytes":peak[0],"end_rss_bytes":process.memory_info().rss,
                       "statuses":sorted(statuses),"encoder_children_remaining":[child.name() for child in process.children() if "ffmpeg" in child.name().lower()],
                       "summary":summary,"verification":verification,"event_database_bytes":app.state.offline_storage.artifact(app.state.offline_jobs.get(job_id),"events_db")[0].stat().st_size,"evidence_bytes":sum(row[v]["size_bytes"] for row in events for v in ("original","annotated"))}
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
                assert inference_calls[f"offline:video:{repeat_id}"] == list(range(47))
                assert id(detector._model)==identity
                repeat_summary = http.get(f"/api/v1/offline/jobs/{repeat_id}/artifacts/summary").json()
                metrics["sequential_repeat_summary"] = repeat_summary
                repeat_events = http.get(f"/api/v1/offline/jobs/{repeat_id}/events").json()["items"]
                assert not ({r["event_id"] for r in events} & {r["event_id"] for r in repeat_events})
                if events:
                    assert http.get(f"/api/v1/offline/jobs/{repeat_id}/events/{events[0]['event_id']}").status_code == 404
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
