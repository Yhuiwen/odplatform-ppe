from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from core.detection.schemas import BoundingBox, Detection
from core.rendering.annotated_frame import (
    AnnotatedFrameRenderer,
    AnnotatedRenderingError,
)
from core.schemas.detection import DetectionResult
from core.schemas.video import FrameData, VideoMetadata
from infra.storage.annotated_video_writer import (
    AnnotatedVideoFrameCountError,
    AnnotatedVideoOutputConflictError,
    AnnotatedVideoWriter,
)
from scripts.render_annotated_demo_video import main as annotated_cli_main
from services.annotated_video_service import (
    AnnotatedVideoService,
)


CLASS_NAMES = ("person", "hardhat", "no_hardhat", "vest", "no_vest")


def _detection(
    frame: FrameData,
    *,
    class_id: int,
    source: str = "video:fixture.mp4",
    bbox: tuple[float, float, float, float] = (4.0, 5.0, 24.0, 30.0),
) -> DetectionResult:
    class_name = CLASS_NAMES[class_id]
    return DetectionResult(
        frame_id=frame.frame_id,
        timestamp=frame.timestamp,
        source=source,
        detection=Detection(
            bbox=BoundingBox(*bbox),
            class_id=class_id,
            class_name=class_name,
            confidence=0.91,
        ),
    )


class _FakeInference:
    def __init__(self) -> None:
        self.execution_enabled = True
        self.frames: list[int] = []

    def infer_frame(self, frame: FrameData, *, source: str):
        self.frames.append(frame.frame_id)
        if frame.frame_id == 1:
            return []
        return [
            _detection(
                frame,
                class_id=frame.frame_id % len(CLASS_NAMES),
                source=source,
            )
        ]


class _FakeReader:
    def __init__(
        self,
        metadata: VideoMetadata,
        frames: list[FrameData],
        *,
        fail_on_frame: int | None = None,
    ) -> None:
        self.metadata = metadata
        self._frames = frames
        self._fail_on_frame = fail_on_frame

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def open(self) -> VideoMetadata:
        return self.metadata

    def __iter__(self):
        for frame in self._frames:
            if frame.frame_id == self._fail_on_frame:
                raise RuntimeError("synthetic reader failure")
            yield frame


class _FakeVideoWriter:
    def __init__(self, path: Path, fps: float, size: tuple[int, int], codec: str):
        self.path = path
        self.fps = fps
        self.size = size
        self.codec = codec
        self.frames: list[Any] = []
        self.released = False

    def write(self, image: Any) -> None:
        self.frames.append(image.copy())

    def release(self) -> None:
        self.released = True
        self.path.write_bytes(
            f"fake-mp4:{len(self.frames)}:{self.size[0]}x{self.size[1]}".encode(
                "ascii"
            )
        )

    def isOpened(self) -> bool:
        return True


class _FakeCapture:
    def __init__(
        self,
        *,
        frame_count: int,
        fps: float,
        width: int,
        height: int,
    ) -> None:
        self.frame_count = frame_count
        self.fps = fps
        self.width = width
        self.height = height
        self._remaining = frame_count
        self.released = False

    def read(self):
        if self._remaining <= 0:
            return False, None
        self._remaining -= 1
        return True, np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def release(self) -> None:
        self.released = True


class _RecordingBackend:
    def __init__(self) -> None:
        self.boxes: list[tuple[int, int, int, int]] = []
        self.labels: list[str] = []

    def copy(self, image: Any) -> Any:
        return image.copy()

    def rectangle(self, image: Any, bbox, color) -> None:
        self.boxes.append(tuple(bbox))

    def label(self, image: Any, text: str, origin, color, width, height) -> None:
        self.labels.append(text)


def _metadata(frame_count: int = 3) -> VideoMetadata:
    return VideoMetadata(
        source="video:fixture.mp4",
        fps=25.0,
        width=64,
        height=48,
        frame_count=frame_count,
        duration_seconds=frame_count / 25.0,
    )


def _frames(frame_count: int = 3) -> list[FrameData]:
    return [
        FrameData(
            frame_id=index,
            timestamp=index / 25.0,
            image=np.zeros((48, 64, 3), dtype=np.uint8),
        )
        for index in range(frame_count)
    ]


def _write_config(tmp_path: Path, checkpoint: Path) -> Path:
    config = {
        "inference": {
            "execution_enabled": False,
            "runtime": {
                "id": "test-runtime",
                "python": "3.10.4",
                "torch": "2.5.1+cpu",
                "ultralytics": "8.4.157",
            },
            "model": {
                "path": str(checkpoint),
                "sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                "size_bytes": checkpoint.stat().st_size,
                "auto_download": False,
            },
            "device": {
                "policy": "cpu_only",
                "device": "cpu",
                "auto": False,
                "cuda_authorized": False,
            },
            "preprocessing": {"imgsz": 640, "batch": 1},
            "detection": {
                "conf_threshold": 0.25,
                "iou_threshold": 0.45,
                "max_det": 300,
                "class_filter": list(range(len(CLASS_NAMES))),
                "class_names": list(CLASS_NAMES),
            },
            "input": {
                "video_extensions": [".mp4"],
                "image_extensions": [".jpg"],
            },
            "output": {"codec": "mp4v"},
        }
    }
    path = tmp_path / "inference.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "source.mp4"
    path.write_bytes(b"source-mp4")
    return path


def _service(
    tmp_path: Path,
    *,
    output_frame_count: int | None = None,
    reader_frames: list[FrameData] | None = None,
    fail_on_frame: int | None = None,
) -> tuple[AnnotatedVideoService, _FakeInference, Path]:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"frozen-checkpoint")
    config = _write_config(tmp_path, checkpoint)
    source = _source(tmp_path)
    metadata = _metadata((len(reader_frames) if reader_frames is not None else 3))
    frames = reader_frames if reader_frames is not None else _frames()
    expected_output_count = (
        output_frame_count if output_frame_count is not None else len(frames)
    )
    inference = _FakeInference()

    def capture_factory(_: Path) -> _FakeCapture:
        return _FakeCapture(
            frame_count=expected_output_count,
            fps=metadata.fps,
            width=metadata.width,
            height=metadata.height,
        )

    def writer_factory(output_dir: Path, video_metadata: VideoMetadata):
        return AnnotatedVideoWriter(
            output_dir,
            video_metadata,
            writer_factory=lambda path, fps, size, codec: _FakeVideoWriter(
                path,
                fps,
                size,
                codec,
            ),
            capture_factory=capture_factory,
        )

    service = AnnotatedVideoService(
        config,
        execution_enabled=True,
        inference_service=inference,
        reader_factory=lambda _: _FakeReader(
            metadata,
            frames,
            fail_on_frame=fail_on_frame,
        ),
        writer_factory=writer_factory,
        run_id_factory=lambda: "run-001",
        clock=lambda: datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc),
    )
    return service, inference, source


def test_annotation_plan_is_clipped_deterministic_and_class_bound() -> None:
    backend = _RecordingBackend()
    renderer = AnnotatedFrameRenderer(CLASS_NAMES, drawing_backend=backend)
    frame = _frames(1)[0]
    detection = _detection(
        frame,
        class_id=0,
        bbox=(-5.0, 2.0, 20.2, 30.0),
    )

    plan = renderer.annotation_plan((detection,), width=64, height=48)

    assert len(plan) == 1
    assert plan[0].bbox == (0, 2, 21, 30)
    assert plan[0].label == "person 0.91"
    assert plan[0].color == (0, 165, 255)
    rendered = renderer.render(frame, (detection,))
    assert rendered.shape == frame.image.shape
    assert backend.boxes == [(0, 2, 21, 30)]
    assert backend.labels == ["person 0.91"]

    wrong_name = DetectionResult(
        frame_id=frame.frame_id,
        timestamp=frame.timestamp,
        source="video:fixture.mp4",
        detection=Detection(
            bbox=BoundingBox(1.0, 1.0, 10.0, 10.0),
            class_id=0,
            class_name="vehicle",
            confidence=0.8,
        ),
    )
    with pytest.raises(AnnotatedRenderingError):
        renderer.annotation_plan((wrong_name,), width=64, height=48)


def test_service_publishes_complete_atomic_output_in_frame_order(
    tmp_path: Path,
) -> None:
    service, inference, source = _service(tmp_path)
    output_dir = tmp_path / "published"

    result = service.render_video(source, output_dir=output_dir)

    assert inference.frames == [0, 1, 2]
    assert result.processed_frames == 3
    assert result.source_frames == 3
    assert result.written_frames == 3
    assert sorted(path.name for path in output_dir.iterdir()) == [
        "demo.mp4",
        "frames.jsonl",
        "renderer.log",
        "run.json",
        "summary.json",
    ]
    records = [
        json.loads(line)
        for line in (output_dir / "frames.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [record["frame_id"] for record in records] == [0, 1, 2]
    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["source_frame_count"] == 3
    assert summary["processed_frame_count"] == 3
    assert summary["written_frame_count"] == 3
    assert summary["verified_output_frame_count"] == 3
    assert summary["class_counts"]["person"] == 1
    assert summary["class_counts"]["no_hardhat"] == 1
    run = json.loads((output_dir / "run.json").read_text(encoding="utf-8"))
    assert run["run_id"] == "run-001"
    assert run["class_order"] == list(CLASS_NAMES)
    assert not list(tmp_path.glob(".published.staging-*"))


def test_writer_count_mismatch_rolls_back_all_staging_files(tmp_path: Path) -> None:
    service, _, source = _service(
        tmp_path,
        output_frame_count=2,
    )
    output_dir = tmp_path / "should-not-exist"

    with pytest.raises(AnnotatedVideoFrameCountError):
        service.render_video(source, output_dir=output_dir)

    assert not output_dir.exists()
    assert not list(tmp_path.glob(".should-not-exist.staging-*"))


def test_service_reader_failure_rolls_back(tmp_path: Path) -> None:
    service, _, source = _service(
        tmp_path,
        reader_frames=_frames(),
        fail_on_frame=1,
    )
    output_dir = tmp_path / "reader-failure"

    with pytest.raises(RuntimeError, match="synthetic reader failure"):
        service.render_video(source, output_dir=output_dir)

    assert not output_dir.exists()
    assert not list(tmp_path.glob(".reader-failure.staging-*"))


def test_writer_rejects_existing_output_without_touching_it(tmp_path: Path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"checkpoint")
    output_dir = tmp_path / "existing"
    output_dir.mkdir()
    marker = output_dir / "marker.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(AnnotatedVideoOutputConflictError):
        with AnnotatedVideoWriter(
            output_dir,
            _metadata(),
            writer_factory=lambda path, fps, size, codec: _FakeVideoWriter(
                path,
                fps,
                size,
                codec,
            ),
            capture_factory=lambda _: _FakeCapture(
                frame_count=3,
                fps=25.0,
                width=64,
                height=48,
            ),
        ):
            pass

    assert marker.read_text(encoding="utf-8") == "keep"


def test_cli_reports_structured_errors_with_required_fields(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = annotated_cli_main([str(tmp_path / "missing.mp4")])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["status"] == "error"
    assert payload["error"] == "video_not_found"
    assert payload["processed_frames"] == 0
    assert payload["source_frames"] is None
    assert payload["output_video"] is None
    assert "error" in payload and "elapsed_seconds" in payload


def test_cli_rejects_execution_when_frozen_config_is_disabled(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _source(tmp_path)

    exit_code = annotated_cli_main([str(source)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["error"] == "execution_disabled"
    assert payload["output_video"] is None
