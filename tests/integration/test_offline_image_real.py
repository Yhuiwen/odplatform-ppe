"""Authorized real frozen-checkpoint image chain, isolated from formal jobs."""
from __future__ import annotations

import hashlib
import io
import json
import time
import zipfile
from pathlib import Path
from threading import Event, Thread

import pytest
pytest.importorskip("fastapi", reason="real offline API requires separate FastAPI runtime")
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from core.schemas.events import EventQuery
import psutil


def test_real_image_upload_to_verified_download(tmp_path, monkeypatch):
    project = Path(__file__).resolve().parents[2]
    source = project / "artifacts" / "validation" / "P4C-1" / "input" / "construction-workers-public-domain.jpg"
    model = project / "models" / "checkpoints" / "EXP-001" / "best.pt"
    if not source.is_file() or not model.is_file():
        pytest.skip("verified local image/checkpoint unavailable; real inference NOT_EXECUTED")
    expected_model = "1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61"
    assert hashlib.sha256(model.read_bytes()).hexdigest() == expected_model
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT", str(tmp_path / "jobs"))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION", "1")
    monkeypatch.setenv("ODPLATFORM_OFFLINE_VIDEO_EXECUTION", "0")
    payload = source.read_bytes()
    started = time.monotonic()
    rss_samples = []
    sampling_stop = Event()
    process = psutil.Process()

    def sample_rss():
        while not sampling_stop.is_set():
            rss_samples.append(process.memory_info().rss)
            sampling_stop.wait(0.05)

    sampler = Thread(target=sample_rss, daemon=True)
    sampler.start()
    with TestClient(app, base_url="http://127.0.0.1:8000") as http:
        event_count_before = app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count
        capabilities = http.get("/api/v1/offline/capabilities").json()
        assert capabilities["image_processor_available"] is True
        assert capabilities["video_processor_available"] is False
        response = http.post("/api/v1/offline/jobs", files={"file": ("construction.jpg", payload, "image/jpeg")})
        assert response.status_code == 202, response.text
        job_id = response.json()["job_id"]
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            job = http.get(f"/api/v1/offline/jobs/{job_id}").json()
            if job["status"] in {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                break
            time.sleep(0.2)
        else:
            pytest.fail("real image job did not reach a terminal status")
        assert job["status"] == "COMPLETED", job
        manifest = http.get(f"/api/v1/offline/jobs/{job_id}/artifacts").json()["items"]
        assert {item["key"] for item in manifest} == {"annotated", "detections", "summary", "results"}
        downloaded = {}
        for item in manifest:
            result = http.get(f"/api/v1/offline/jobs/{job_id}/artifacts/{item['key']}")
            assert result.status_code == 200
            downloaded[item["key"]] = result.content
            assert hashlib.sha256(result.content).hexdigest() == item["sha256"]
        with Image.open(io.BytesIO(downloaded["annotated"])) as image:
            assert image.size == (1024, 766) and image.format == "PNG"
            image.load()
        summary = json.loads(downloaded["summary"])
        detections = json.loads(downloaded["detections"])
        assert summary["model_sha256"] == expected_model
        assert summary["input_sha256"] == hashlib.sha256(payload).hexdigest()
        assert summary["image"]["normalized_width"] == summary["image"]["output_width"] == 1024
        assert summary["image"]["normalized_height"] == summary["image"]["output_height"] == 766
        assert len(detections["detections"]) == summary["detection_count"] == job["detection_count"]
        assert summary["candidate_count"] == job["candidate_count"]
        assert 0 <= summary["inference_seconds"] <= summary["processing_seconds"] <= job["processing_seconds"]
        assert sum(summary["class_counts"].values()) == summary["detection_count"]
        assert {item["class_name"] for item in summary["not_evaluated_classes"]} == {"machinery", "vehicle"}
        with zipfile.ZipFile(io.BytesIO(downloaded["results"])) as archive:
            assert set(archive.namelist()) == {"annotated.png", "detections.json", "summary.json"}
            assert archive.testzip() is None
        model_identity = id(app.state.offline_worker.processors["image"].detector._model)
        for index in range(2):
            queued = http.post("/api/v1/offline/jobs", files={"file": (f"repeat-{index}.jpg", payload, "image/jpeg")})
            assert queued.status_code == 202
            repeat_id = queued.json()["job_id"]
            repeat_deadline = time.monotonic() + 90
            while time.monotonic() < repeat_deadline:
                repeat = http.get(f"/api/v1/offline/jobs/{repeat_id}").json()
                if repeat["status"] in {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                    break
                time.sleep(0.2)
            assert repeat["status"] == "COMPLETED", repeat
            assert id(app.state.offline_worker.processors["image"].detector._model) == model_identity
        assert app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count == event_count_before
    sampling_stop.set()
    sampler.join(2)
    print("REAL_IMAGE_RESULT", json.dumps({"detection_count":summary["detection_count"],
                                           "class_counts":summary["class_counts"],"candidate_count":summary["candidate_count"],
                                           "processing_seconds":summary["processing_seconds"],
                                           "inference_seconds":summary["inference_seconds"],
                                           "wall_seconds":round(time.monotonic()-started,3),
                                           "sampled_peak_rss_bytes":max(rss_samples),
                                           "final_rss_bytes":rss_samples[-1],
                                           "output_bytes":{key:len(value) for key,value in downloaded.items()}}, sort_keys=True))
