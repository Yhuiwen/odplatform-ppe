from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from core.schemas.video import (
    FrameData,
    SourceMetadata,
    SourceState,
    SourceStatus,
    SourceType,
)
from core.video.mp4_source import MP4VideoSource
from core.video.reader import VideoReader
from core.video.rtsp_source import RTSPVideoSource, redact_rtsp_uri
from core.video.usb_camera_source import USBCameraSource
from core.video.video_source import (
    InvalidVideoSourceError,
    VideoSource,
    VideoSourceDisconnectedError,
    VideoSourceOpenError,
    VideoSourceStateError,
)
from utils.paths import PROJECT_ROOT


class _FakeCapture:
    def __init__(
        self,
        *,
        opened: bool = True,
        fps: float = 25.0,
        width: int = 640,
        height: int = 480,
        frames: list[object] | None = None,
    ) -> None:
        self.opened = opened
        self.fps = fps
        self.width = width
        self.height = height
        self.values = {3: width, 4: height, 5: fps}
        self.frames = list(frames or [object()])
        self.frame_count = len(self.frames)
        self.released = False
        self.timeouts: dict[int, float] = {}

    def isOpened(self) -> bool:
        return self.opened

    def get(self, code: int) -> float:
        return self.values.get(code, 0.0)

    def set(self, code: int, value: float) -> None:
        self.timeouts[code] = value

    def read(self) -> tuple[bool, object | None]:
        if self.frames:
            return True, self.frames.pop(0)
        return False, None

    def release(self) -> None:
        self.released = True


class _MockVideoSource:
    source_type = SourceType.MP4
    metadata: SourceMetadata | None = None

    def open(self) -> SourceMetadata:
        self.metadata = SourceMetadata(
            source_id="mock:1",
            source_type=SourceType.MP4,
            display_name="mock",
            width=None,
            height=None,
            fps=None,
            frame_count=None,
        )
        return self.metadata

    def read(self) -> FrameData | None:
        return None

    def status(self) -> SourceStatus:
        return SourceStatus(state=SourceState.IDLE)

    def close(self) -> None:
        self.metadata = None


def _video_path(tmp_path: Path) -> Path:
    path = tmp_path / "fixture.mp4"
    path.write_bytes(b"fake-mp4")
    return path


def _clock() -> datetime:
    return datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)


def test_mock_source_satisfies_protocol() -> None:
    source = _MockVideoSource()

    assert isinstance(source, VideoSource)
    assert source.open().source_type is SourceType.MP4
    assert source.read() is None
    assert source.status().state is SourceState.IDLE
    source.close()


def test_mp4_source_preserves_order_and_ends_cleanly(tmp_path: Path) -> None:
    path = _video_path(tmp_path)
    capture = _FakeCapture(frames=[object(), object(), object()])
    source = MP4VideoSource(
        path,
        reader_factory=lambda item: VideoReader(
            item,
            capture_factory=lambda _: capture,
        ),
        wall_clock=_clock,
        monotonic_clock=lambda: 10.0,
    )

    metadata = source.open()
    frames = [source.read(), source.read(), source.read()]
    end = source.read()

    assert metadata.source_type is SourceType.MP4
    assert metadata.frame_count == 3
    assert [frame.frame_id for frame in frames if frame is not None] == [0, 1, 2]
    assert [frame.timestamp for frame in frames if frame is not None] == [
        0.0,
        0.04,
        0.08,
    ]
    assert end is None
    assert source.status().state is SourceState.ENDED
    source.close()
    source.close()
    assert source.status().state is SourceState.CLOSED
    assert capture.released is True


def test_usb_camera_lifecycle_and_disconnect(tmp_path: Path) -> None:
    capture = _FakeCapture(frames=[object()])
    source = USBCameraSource(
        0,
        capture_factory=lambda _: capture,
        wall_clock=_clock,
        monotonic_clock=lambda: 20.0,
    )

    metadata = source.open()
    frame = source.read()

    assert metadata.source_type is SourceType.USB_CAMERA
    assert metadata.source_id == "usb:0"
    assert frame is not None and frame.frame_id == 0
    assert source.status().state is SourceState.LIVE

    with pytest.raises(VideoSourceDisconnectedError) as error:
        source.read()
    assert error.value.code == "SOURCE_DISCONNECTED"
    assert source.status().state is SourceState.FAILED
    source.close()
    assert capture.released is True


def test_rtsp_source_redacts_credentials_and_query() -> None:
    uri = "rtsp://operator:secret@example.com:8554/live?token=hidden"
    capture = _FakeCapture(frames=[object()])
    received: list[str] = []
    source = RTSPVideoSource(
        uri,
        capture_factory=lambda value: (received.append(value), capture)[1],
        wall_clock=_clock,
        monotonic_clock=lambda: 30.0,
    )

    assert source.safe_uri == "rtsp://example.com:8554/live"
    metadata = source.open()
    frame = source.read()

    assert metadata.display_name == source.safe_uri
    assert frame is not None and frame.frame_id == 0
    assert received == [uri]
    assert "secret" not in source.status().to_dict().__repr__()
    assert capture.timeouts == {53: 5000.0, 54: 5000.0}
    source.close()
    assert capture.released is True


def test_invalid_source_inputs_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(InvalidVideoSourceError):
        USBCameraSource(-1)
    with pytest.raises(InvalidVideoSourceError):
        RTSPVideoSource("http://example.com/stream")
    with pytest.raises(InvalidVideoSourceError):
        redact_rtsp_uri("rtsp://")
    with pytest.raises(InvalidVideoSourceError):
        redact_rtsp_uri("rtsp://example.com:not-a-port/live")

    source = USBCameraSource(
        0,
        capture_factory=lambda _: _FakeCapture(opened=False),
    )
    with pytest.raises(VideoSourceOpenError):
        source.open()
    assert source.status().state is SourceState.FAILED
    assert source.status().error_code == "SOURCE_OPEN_FAILED"

    with pytest.raises(VideoSourceStateError):
        source.read()

    missing = MP4VideoSource(tmp_path / "missing.mp4")
    with pytest.raises(InvalidVideoSourceError):
        missing.open()
    assert missing.status().state is SourceState.FAILED


def test_business_layers_do_not_call_video_capture_directly() -> None:
    business_roots = ("services", "web", "scripts")
    for root in business_roots:
        for path in (PROJECT_ROOT / root).rglob("*.py"):
            assert "cv2.VideoCapture" not in path.read_text(encoding="utf-8")

    for path in (PROJECT_ROOT / "core").rglob("*.py"):
        if "video" in path.parts:
            continue
        assert "cv2.VideoCapture" not in path.read_text(encoding="utf-8")
