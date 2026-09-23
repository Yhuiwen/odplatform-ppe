from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.detection.schemas import BoundingBox, Detection
from core.inference.detector import InferenceExecutionDisabledError
from core.schemas.detection import DetectionResult
from core.video.reader import (
    EmptyVideoError,
    InvalidVideoFormatError,
    VideoDecodeError,
    VideoNotFoundError,
    VideoReader,
)
from scripts.run_video_inference import main
from services.video_inference_service import VideoInferenceService


class _FakeCapture:
    def __init__(
        self,
        *,
        fps: float = 25.0,
        width: int = 640,
        height: int = 480,
        frame_count: int | None = 3,
        frames: list[object] | None = None,
    ) -> None:
        self.fps = fps
        self.width = width
        self.height = height
        self.frame_count = frame_count
        self._frames = list(frames or [object(), object(), object()])
        self.released = False

    def read(self):
        if self._frames:
            return True, self._frames.pop(0)
        return False, None

    def release(self) -> None:
        self.released = True


class _FakeInferenceService:
    def __init__(self, *, execution_enabled: bool = True) -> None:
        self.execution_enabled = execution_enabled
        self.frames = []

    def infer_frame(self, frame, *, source: str):
        self.frames.append(frame)
        if frame.frame_id == 1:
            return []

        class_names = (
            "person",
            "hardhat",
            "no_hardhat",
            "vest",
            "no_vest",
        )
        class_id = frame.frame_id % len(class_names)
        return [
            DetectionResult(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                source=source,
                detection=Detection(
                    bbox=BoundingBox(10.0, 20.0, 50.0, 80.0),
                    class_id=class_id,
                    class_name=class_names[class_id],
                    confidence=0.9,
                ),
            )
        ]


def _video_path(tmp_path: Path, name: str = "fixture.mp4") -> Path:
    path = tmp_path / name
    path.write_bytes(b"fake-mp4-container")
    return path


def test_reader_preserves_order_and_extracts_metadata(tmp_path: Path) -> None:
    path = _video_path(tmp_path)
    capture = _FakeCapture()

    with VideoReader(path, capture_factory=lambda _: capture) as reader:
        metadata = reader.metadata
        frames = list(reader)

    assert metadata is not None
    assert metadata.source == "video:fixture.mp4"
    assert metadata.fps == 25.0
    assert metadata.width == 640
    assert metadata.height == 480
    assert metadata.frame_count == 3
    assert metadata.duration_seconds == pytest.approx(0.12)
    assert [frame.frame_id for frame in frames] == [0, 1, 2]
    assert [frame.timestamp for frame in frames] == pytest.approx(
        [0.0, 0.04, 0.08]
    )
    assert capture.released is True


def test_video_service_result_is_ordered_and_serializable(tmp_path: Path) -> None:
    path = _video_path(tmp_path)
    capture = _FakeCapture()
    inference_service = _FakeInferenceService()
    service = VideoInferenceService(
        inference_service=inference_service,
        reader_factory=lambda reader_path: VideoReader(
            reader_path,
            capture_factory=lambda _: capture,
        ),
    )

    result = service.infer_video(path)
    payload = json.loads(json.dumps(result.to_dict()))

    assert result.processed_frames == 3
    assert [frame.frame_id for frame in result.frames] == [0, 1, 2]
    assert [frame.detection_count for frame in result.frames] == [1, 0, 1]
    assert [frame.frame_id for frame in inference_service.frames] == [0, 1, 2]
    assert payload["video"]["frame_count"] == 3
    assert payload["processed_frames"] == 3
    assert payload["frame_results"][1]["detections"] == []


def test_reader_errors_are_structured(tmp_path: Path) -> None:
    with pytest.raises(VideoNotFoundError) as missing:
        VideoReader(tmp_path / "missing.mp4")
    assert missing.value.code == "video_not_found"

    invalid = tmp_path / "fixture.avi"
    invalid.write_bytes(b"not-mp4")
    with pytest.raises(InvalidVideoFormatError) as invalid_format:
        VideoReader(invalid)
    assert invalid_format.value.code == "invalid_video_format"

    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    with pytest.raises(EmptyVideoError) as empty_error:
        VideoReader(empty)
    assert empty_error.value.code == "empty_video"

    truncated = _video_path(tmp_path, "truncated.mp4")
    with pytest.raises(VideoDecodeError) as decode_error:
        with VideoReader(
            truncated,
            capture_factory=lambda _: _FakeCapture(
                frame_count=3,
                frames=[object()],
            ),
        ) as reader:
            list(reader)
    assert decode_error.value.code == "video_decode_failed"


def test_video_execution_disabled_does_not_open_reader(tmp_path: Path) -> None:
    reader_calls = 0

    def reader_factory(path: Path):
        nonlocal reader_calls
        reader_calls += 1
        return VideoReader(path, capture_factory=lambda _: _FakeCapture())

    service = VideoInferenceService(
        inference_service=_FakeInferenceService(execution_enabled=False),
        reader_factory=reader_factory,
    )

    with pytest.raises(InferenceExecutionDisabledError) as error:
        service.infer_video(_video_path(tmp_path))

    assert error.value.code == "execution_disabled"
    assert reader_calls == 0


def test_video_cli_returns_structured_disabled_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([str(_video_path(tmp_path))])

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out) == {
        "status": "error",
        "error": "execution_disabled",
        "message": "Video inference is disabled by configs/inference.yaml",
    }


def test_video_cli_returns_structured_input_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([str(tmp_path / "missing.mp4")]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "video_not_found"

    invalid = tmp_path / "fixture.avi"
    invalid.write_bytes(b"not-mp4")
    assert main([str(invalid)]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "invalid_video_format"

    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    assert main([str(empty)]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "empty_video"
