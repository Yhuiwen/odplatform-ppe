"""Image-only processor contract; fake inference isolates decode/render/output rules."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
pytest.importorskip("fastapi", reason="offline image API uses the separate FastAPI runtime")
from PIL import Image

from api.main import app  # Establish the approved frozen business runtime path.

from core.detection.schemas import BoundingBox, Detection
from core.inference.detector import CheckpointIntegrityError
from core.schemas.detection import DetectionResult
from offline.image_processor import ImageProcessor
from offline.jobs import ArtifactPublisher, JobError, JobRepository, JobStorage, OfflineSettings, sha256_file
from offline.worker import JobContext


NAMES = ("person", "hardhat", "no_hardhat", "vest", "no_vest")


class FakeInference:
    def __init__(self, kinds=()):
        self.kinds = kinds
        self.detector = SimpleNamespace(class_names=NAMES, class_filter=tuple(range(5)), runtime_id="FAKE-ONLY-UNIT",
                                        expected_model_sha256="a" * 64,
                                        _model=SimpleNamespace(names={i: name for i, name in enumerate((*NAMES, "machinery", "vehicle"))}))
        self.observed_bgr = None

    def infer_frame(self, frame, *, source):
        self.observed_bgr = frame.image.copy()
        height, width = frame.image.shape[:2]
        return [DetectionResult(0, 0.0, source, Detection(BoundingBox(1, 1, width - 1, height - 1),
                                                       class_id=index, class_name=NAMES[index], confidence=0.85))
                for index in self.kinds]


def payload(fmt="PNG", *, mode="RGB", size=(64, 32), orientation=None):
    color = (255, 0, 0, 0) if mode == "RGBA" else (255, 0, 0) if mode == "RGB" else 120
    image = Image.new(mode, size, color)
    output = io.BytesIO()
    options = {}
    if orientation is not None:
        exif = Image.Exif()
        exif[274] = orientation
        options["exif"] = exif
    image.save(output, format=fmt, **options)
    return output.getvalue()


def run_image(tmp_path, data, filename, fake, *, max_pixels=8294400, cancelled=lambda: False):
    storage = JobStorage(tmp_path / "offline")
    repo = JobRepository(storage.root / "jobs.sqlite3")
    job_id = "a" * 32
    storage.create(job_id)
    source = storage.path(job_id, "input", "source" + Path(filename).suffix)
    source.write_bytes(data)
    repo.create(job_id, "image", filename, False)
    repo.transition(job_id, "QUEUED", updates={"input_sha256":hashlib.sha256(data).hexdigest(),
                                               "input_size_bytes":len(data), "input_mime":"image/jpeg" if filename.endswith("jpg") else "image/png"})
    repo.transition(job_id, "PROCESSING")
    context = JobContext(job=repo.get(job_id), storage=storage, publisher=ArtifactPublisher(storage),
                         progress=lambda done,total: repo.progress(job_id,done,total), cancelled=cancelled,
                         record_result=lambda count,candidates,seconds: repo.record_image_result(job_id,count,candidates,seconds))
    settings = OfflineSettings(root=storage.root, max_pixels=max_pixels)
    processor = ImageProcessor(settings, inference=fake, config_path=Path("configs/inference.yaml"))
    return processor, context, repo, source


@pytest.mark.parametrize("fmt,mode,filename,orientation,expected", [
    ("JPEG", "RGB", "source.jpg", None, (64, 32)),
    ("PNG", "RGB", "source.png", None, (64, 32)),
    ("PNG", "RGBA", "source.png", None, (64, 32)),
    ("PNG", "L", "source.png", None, (64, 32)),
    ("PNG", "RGB", "source.png", None, (80, 20)),
    ("PNG", "RGB", "source.png", None, (2048, 1024)),
    ("JPEG", "RGB", "source.jpg", 6, (32, 64)),
])
def test_decode_original_size_and_outputs(tmp_path, fmt, mode, filename, orientation, expected):
    size = expected if expected in {(80, 20), (2048, 1024)} else (64, 32)
    data = payload(fmt, mode=mode, size=size, orientation=orientation)
    fake = FakeInference((0, 4))
    processor, context, repo, source = run_image(tmp_path, data, filename, fake)
    manifest = processor(context)
    assert source.read_bytes() == data
    assert set(manifest) == {"annotated", "detections", "summary", "results"}
    for key in manifest:
        context.storage.artifact({**repo.get(context.job["job_id"]), "status":"COMPLETED", "artifact_manifest":manifest}, key)
    output = context.storage.path(context.job["job_id"], "output", "annotated.png")
    with Image.open(output) as image:
        assert image.size == expected and image.format == "PNG"
    summary = json.loads(context.storage.path(context.job["job_id"], "output", "summary.json").read_text(encoding="utf-8"))
    records = json.loads(context.storage.path(context.job["job_id"], "output", "detections.json").read_text(encoding="utf-8"))
    assert summary["detection_count"] == 2 and summary["candidate_count"] == 1
    assert 0 <= summary["inference_seconds"] <= summary["processing_seconds"]
    assert summary["class_counts"]["no_vest"] == 1
    assert [item["class_name"] for item in summary["not_evaluated_classes"]] == ["machinery", "vehicle"]
    assert (summary["image"]["output_width"], summary["image"]["output_height"]) == expected
    assert summary["image"]["exif_orientation"] == (orientation or 1)
    assert len(records["detections"]) == 2
    for item in records["detections"]:
        x1, y1, x2, y2 = item["bbox_xyxy"]
        assert 0 <= x1 < x2 < expected[0] and 0 <= y1 < y2 < expected[1]
    with zipfile.ZipFile(context.storage.path(context.job["job_id"], "output", "results.zip")) as archive:
        assert set(archive.namelist()) == {"annotated.png", "detections.json", "summary.json"}
        assert archive.testzip() is None
    assert repo.get(context.job["job_id"])["detection_count"] == 2
    if mode == "RGBA":
        assert summary["image"]["alpha_policy"] == "white_background"
        assert fake.observed_bgr[0, 0].tolist() == [255, 255, 255]
    if mode == "RGB" and orientation is None and fmt == "PNG":
        assert fake.observed_bgr[0, 0].tolist() == [0, 0, 255]


def test_no_detections_and_limits(tmp_path):
    data = payload()
    fake = FakeInference(())
    processor, context, repo, _ = run_image(tmp_path, data, "x.png", fake)
    processor(context)
    assert repo.get(context.job["job_id"])["detection_count"] == 0
    summary = json.loads(context.storage.path(context.job["job_id"], "output", "summary.json").read_text(encoding="utf-8"))
    assert summary["candidate_count"] == 0
    too_big, context2, _, _ = run_image(tmp_path / "second", data, "x.png", fake, max_pixels=100)
    with pytest.raises(JobError, match="像素"):
        too_big(context2)


@pytest.mark.parametrize("data", [b"", b"not an image"])
def test_invalid_image_and_cancellation(tmp_path, data):
    fake = FakeInference()
    processor, context, _, source = run_image(tmp_path, data, "x.png", fake)
    with pytest.raises(JobError):
        processor(context)
    assert source.read_bytes() == data
    assert not list(context.storage.directory(context.job["job_id"]).joinpath("output").iterdir())
    if not data:
        return
    valid = payload()
    processor2, context2, _, source2 = run_image(tmp_path / "cancelled", valid, "x.png", fake, cancelled=lambda: True)
    with pytest.raises(JobError, match="取消"):
        processor2(context2)
    assert source2.read_bytes() == valid


def test_missing_model_is_a_safe_error(tmp_path):
    class MissingModel(FakeInference):
        def infer_frame(self, frame, *, source):
            raise CheckpointIntegrityError("secret server path")

    processor, context, _, _ = run_image(tmp_path, payload(), "x.png", MissingModel())
    with pytest.raises(JobError) as found:
        processor(context)
    assert found.value.code == "MODEL_INTEGRITY_FAILED"
    assert "secret" not in str(found.value)


def test_cancel_during_output_writing_cleans_staging(tmp_path):
    checks = 0

    def cancel_later():
        nonlocal checks
        checks += 1
        return checks >= 6

    processor, context, _, source = run_image(tmp_path, payload(), "x.png", FakeInference((0,)), cancelled=cancel_later)
    with pytest.raises(JobError) as found:
        processor(context)
    assert found.value.code == "JOB_CANCELLED"
    assert source.is_file()
    assert not list(context.storage.directory(context.job["job_id"]).joinpath("staging").iterdir())
    assert not list(context.storage.directory(context.job["job_id"]).joinpath("output").iterdir())


def test_config_fingerprint_mismatch_fails_closed(tmp_path):
    processor, context, _, _ = run_image(tmp_path, payload(), "x.png", FakeInference())
    processor.settings = replace(processor.settings, image_config_sha256="0" * 64)
    assert processor.preflight()[0] is False
    with pytest.raises(JobError) as found:
        processor(context)
    assert found.value.code == "CONFIG_INTEGRITY_FAILED"


def test_wrong_detection_context_is_rejected(tmp_path):
    class WrongFrame(FakeInference):
        def infer_frame(self, frame, *, source):
            return [replace(item, frame_id=1) for item in super().infer_frame(frame,source=source)]
    processor, context, _, _ = run_image(tmp_path, payload(), "x.png", WrongFrame((0,)))
    with pytest.raises(JobError) as found:
        processor(context)
    assert found.value.code == "INVALID_DETECTION_CONTEXT"
    assert not list(context.storage.directory(context.job["job_id"]).joinpath("output").iterdir())


def test_input_changed_during_inference_is_not_published(tmp_path):
    processor, context, _, source = run_image(tmp_path, payload(), "x.png", FakeInference((0,)))
    original = processor.inference.infer_frame
    def tamper(frame, *, source: str):
        result = original(frame, source=source)
        input_path.write_bytes(b"changed input")
        return result
    input_path = source
    processor.inference.infer_frame = tamper
    with pytest.raises(JobError) as found:
        processor(context)
    assert found.value.code == "INPUT_CORRUPT"
    assert not list(context.storage.directory(context.job["job_id"]).joinpath("output").iterdir())
    assert not list(context.storage.directory(context.job["job_id"]).joinpath("staging").iterdir())
