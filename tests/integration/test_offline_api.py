"""V1.2-B real HTTP boundary with isolated durable storage; no inference."""
from __future__ import annotations

import hashlib
import io
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
pytest.importorskip("fastapi", reason="V1 frozen runtime excludes the separate V1.2 API dependencies")
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app


def image_bytes(fmt):
    image = Image.new("RGB", (32, 24), "red")
    stream = io.BytesIO()
    image.save(stream, format=fmt)
    return stream.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT", str(tmp_path / "offline"))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION", "0")
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        yield client, tmp_path / "offline"


@pytest.mark.parametrize("name,mime,content", [
    ("sample.jpg", "image/jpeg", image_bytes("JPEG")),
    ("sample.png", "image/png", image_bytes("PNG")),
])
def test_image_upload_persistence_and_cancel(client, name, mime, content):
    http, root = client
    result = http.post("/api/v1/offline/jobs", files={"file": (name, content, mime)})
    assert result.status_code == 202, result.text
    job = result.json()
    assert job["status"] == "QUEUED"
    assert job["input_sha256"] == hashlib.sha256(content).hexdigest()
    assert "artifact_manifest" not in job
    assert (root / job["job_id"] / "input" / ("source" + Path(name).suffix)).read_bytes() == content
    listed = http.get("/api/v1/offline/jobs", params={"media_type": "image", "status": "QUEUED"}).json()
    assert listed["total_count"] == 1
    assert http.get(f"/api/v1/offline/jobs/{job['job_id']}/artifacts").json() == {"items": []}
    assert http.get(f"/api/v1/offline/jobs/{job['job_id']}/artifacts/fake").status_code == 404
    path = f"/api/v1/offline/jobs/{job['job_id']}/cancel"
    assert http.post(path).json()["status"] == "CANCELLED"
    assert http.post(path).json()["status"] == "CANCELLED"
    assert http.get(f"/api/v1/offline/jobs/{job['job_id']}").json()["status"] == "CANCELLED"


@pytest.mark.parametrize("name,mime,content,code", [
    ("empty.jpg", "image/jpeg", b"", "EMPTY_FILE"),
    ("wrong.jpg", "image/jpeg", image_bytes("PNG"), "MEDIA_TYPE_MISMATCH"),
    ("bad.png", "image/png", b"nonsense", "INVALID_MEDIA"),
    ("../escape.jpg", "image/jpeg", image_bytes("JPEG"), "INVALID_FILENAME"),
    ("wrong.png", "image/jpeg", image_bytes("PNG"), "MEDIA_TYPE_MISMATCH"),
])
def test_rejected_uploads(client, name, mime, content, code):
    http, root = client
    response = http.post("/api/v1/offline/jobs", files={"file": (name, content, mime)})
    assert response.status_code >= 400
    assert response.json()["detail"]["code"] == code
    assert not list(root.rglob("upload.part"))


def test_origin_boundary_and_capabilities(client):
    http, _ = client
    denied = http.get("/api/v1/offline/capabilities", headers={"Origin": "https://attacker.example"})
    assert denied.status_code == 403
    assert http.get("/api/v1/offline/capabilities").json()["processor_available"] is False


def test_image_size_limit_and_no_staged_file(client):
    http, root = client
    app.state.offline_settings = replace(app.state.offline_settings, image_max_bytes=8)
    response = http.post("/api/v1/offline/jobs", files={"file": ("big.jpg", image_bytes("JPEG"), "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "FILE_TOO_LARGE"
    assert not list(root.rglob("upload.part"))


def test_request_body_limit_before_spooling(client):
    http, root = client
    response = http.post("/api/v1/offline/jobs", content=b"x", headers={"Content-Length": str(514 * 1024 * 1024)})
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "REQUEST_TOO_LARGE"
    assert not list(root.rglob("upload.part"))


def test_interrupted_stream_removes_staging(client):
    _, root = client
    from api.offline import create_job

    class Interrupted:
        def __init__(self):
            self.reads = 0

        def read(self, _):
            self.reads += 1
            if self.reads == 1:
                return b"partial"
            raise OSError("disconnected")

        def close(self):
            pass

    request = SimpleNamespace(app=app, url=SimpleNamespace(hostname="127.0.0.1", port=8000), headers={})
    upload = SimpleNamespace(filename="broken.jpg", content_type="image/jpeg", file=Interrupted())
    with pytest.raises(OSError):
        create_job(request, upload, False)
    assert not list(root.rglob("upload.part"))
    assert app.state.offline_jobs.list(status="FAILED")["total_count"] == 1


def test_real_mp4_upload_requires_audio_confirmation(client):
    http, root = client
    sample = Path(__file__).resolve().parents[2] / "artifacts" / "validation" / "test" / "4afa6b121fe5db806c3ff416bafdf571.mp4"
    if not sample.is_file():
        pytest.skip("local MP4 sample unavailable")
    payload = sample.read_bytes()
    denied = http.post("/api/v1/offline/jobs", files={"file": ("sample.mp4", payload, "video/mp4")})
    assert denied.status_code == 422
    assert denied.json()["detail"]["code"] == "AUDIO_CONFIRMATION_REQUIRED"
    accepted = http.post("/api/v1/offline/jobs", files={"file": ("sample.mp4", payload, "video/mp4")}, data={"audio_discard_confirmed": "true"})
    assert accepted.status_code == 202, accepted.text
    job = accepted.json()
    assert job["status"] == "QUEUED" and job["has_audio"] is True
    assert job["input_codec"] == "hevc"
    assert job["input_sha256"] == hashlib.sha256(payload).hexdigest()


def test_restart_recovers_validating_and_keeps_queued(tmp_path, monkeypatch):
    from offline.jobs import JobRepository, JobStorage
    root = tmp_path / "offline"
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT", str(root))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION", "0")
    with TestClient(app, base_url="http://127.0.0.1:8000") as http:
        response = http.post("/api/v1/offline/jobs", files={"file": ("x.png", image_bytes("PNG"), "image/png")})
        queued_id = response.json()["job_id"]
    repo = JobRepository(root / "jobs.sqlite3")
    other_id = "a" * 32
    JobStorage(root).create(other_id)
    repo.create(other_id, "image", "broken.png", False)
    (root / other_id / "staging" / "upload.part").write_bytes(b"partial")
    with TestClient(app, base_url="http://127.0.0.1:8000") as http:
        assert http.get(f"/api/v1/offline/jobs/{queued_id}").json()["status"] == "QUEUED"
        assert http.get(f"/api/v1/offline/jobs/{other_id}").json()["status"] == "FAILED"
    assert not (root / other_id / "staging" / "upload.part").exists()


def test_restart_rejects_corrupt_queued_input(tmp_path, monkeypatch):
    root = tmp_path / "offline"
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT", str(root))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION", "0")
    with TestClient(app, base_url="http://127.0.0.1:8000") as http:
        job = http.post("/api/v1/offline/jobs", files={"file": ("x.png", image_bytes("PNG"), "image/png")}).json()
    (root / job["job_id"] / "input" / "source.png").write_bytes(b"damaged")
    with TestClient(app, base_url="http://127.0.0.1:8000") as http:
        found = http.get(f"/api/v1/offline/jobs/{job['job_id']}").json()
    assert found["status"] == "FAILED" and found["error_code"] == "INPUT_CORRUPT"
