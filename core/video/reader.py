"""Sequential MP4 reader that emits model-independent ``FrameData`` objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator

from core.schemas.video import FrameData, VideoMetadata


class VideoError(RuntimeError):
    """Base error with a stable machine-readable code."""

    code = "video_error"


class VideoNotFoundError(VideoError):
    code = "video_not_found"


class InvalidVideoFormatError(VideoError):
    code = "invalid_video_format"


class EmptyVideoError(VideoError):
    code = "empty_video"


class VideoDecodeError(VideoError):
    code = "video_decode_failed"


class VideoRuntimeUnavailableError(VideoError):
    code = "runtime_unavailable"


class VideoReaderStateError(VideoError):
    code = "video_reader_not_open"


CaptureFactory = Callable[[Path], Any]


class _OpenCVVideoCapture:
    """Expose the small capture surface used by ``VideoReader``."""

    def __init__(self, cv2_module: Any, capture: Any) -> None:
        self._capture = capture
        self.fps = float(capture.get(cv2_module.CAP_PROP_FPS))
        self.width = int(capture.get(cv2_module.CAP_PROP_FRAME_WIDTH))
        self.height = int(capture.get(cv2_module.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(capture.get(cv2_module.CAP_PROP_FRAME_COUNT))
        self.frame_count = frame_count if frame_count > 0 else None

    def read(self) -> tuple[bool, Any]:
        return self._capture.read()

    def release(self) -> None:
        self._capture.release()


class VideoReader:
    """Read a local MP4 sequentially without calling any detector."""

    def __init__(
        self,
        source: str | Path,
        *,
        capture_factory: CaptureFactory | None = None,
    ) -> None:
        self.path = self.validate_source(source)
        self._capture_factory = capture_factory
        self._capture: Any | None = None
        self.metadata: VideoMetadata | None = None

    @staticmethod
    def validate_source(source: str | Path) -> Path:
        if not isinstance(source, (str, Path)):
            raise InvalidVideoFormatError("Video source must be a filesystem path")

        path = Path(source).expanduser()
        if not path.exists():
            raise VideoNotFoundError(f"Video does not exist: {path}")
        if not path.is_file():
            raise InvalidVideoFormatError(f"Video source is not a file: {path}")
        if path.suffix.lower() != ".mp4":
            raise InvalidVideoFormatError(
                f"Unsupported video format: {path.suffix or '<none>'}"
            )
        if path.stat().st_size == 0:
            raise EmptyVideoError(f"Video is empty: {path.name}")
        return path.resolve()

    def __enter__(self) -> VideoReader:
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def open(self) -> VideoMetadata:
        if self._capture is not None:
            assert self.metadata is not None
            return self.metadata

        capture = self._create_capture()
        try:
            metadata = VideoMetadata(
                source=f"video:{self.path.name}",
                fps=float(capture.fps),
                width=int(capture.width),
                height=int(capture.height),
                frame_count=(
                    int(capture.frame_count)
                    if capture.frame_count is not None
                    else None
                ),
                duration_seconds=(
                    float(capture.frame_count) / float(capture.fps)
                    if capture.frame_count is not None
                    else None
                ),
            )
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            capture.release()
            raise VideoDecodeError(
                f"Could not read MP4 metadata: {self.path.name}"
            ) from exc

        self._capture = capture
        self.metadata = metadata
        return metadata

    def iter_frames(self) -> Iterator[FrameData]:
        if self._capture is None or self.metadata is None:
            raise VideoReaderStateError("VideoReader must be opened before reading")

        frame_id = 0
        while True:
            try:
                ok, image = self._capture.read()
            except Exception as exc:
                raise VideoDecodeError(
                    f"Could not decode frame {frame_id}: {self.path.name}"
                ) from exc
            if not ok:
                break
            if image is None:
                raise VideoDecodeError(
                    f"Decoder returned no image for frame {frame_id}"
                )

            yield FrameData(
                frame_id=frame_id,
                timestamp=frame_id / self.metadata.fps,
                image=image,
            )
            frame_id += 1

        if frame_id == 0:
            raise EmptyVideoError(f"Video contains no decodable frames: {self.path.name}")
        if (
            self.metadata.frame_count is not None
            and frame_id < self.metadata.frame_count
        ):
            raise VideoDecodeError(
                "Video ended before the declared frame count: "
                f"expected {self.metadata.frame_count}, observed {frame_id}"
            )
        if (
            self.metadata.frame_count is not None
            and frame_id > self.metadata.frame_count
        ):
            raise VideoDecodeError(
                "Video exceeded the declared frame count: "
                f"expected {self.metadata.frame_count}, observed {frame_id}"
            )

    def __iter__(self) -> Iterator[FrameData]:
        return self.iter_frames()

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        self.metadata = None

    def _create_capture(self) -> Any:
        if self._capture_factory is not None:
            try:
                capture = self._capture_factory(self.path)
            except Exception as exc:
                raise VideoDecodeError(
                    f"Could not open MP4 video: {self.path.name}"
                ) from exc
            if capture is None:
                raise VideoDecodeError(f"Could not open MP4 video: {self.path.name}")
            return capture

        try:
            import cv2
        except ImportError as exc:
            raise VideoRuntimeUnavailableError(
                "OpenCV is not installed in the frozen inference runtime"
            ) from exc

        capture = cv2.VideoCapture(str(self.path))
        if not capture.isOpened():
            capture.release()
            raise VideoDecodeError(f"Could not open MP4 video: {self.path.name}")
        return _OpenCVVideoCapture(cv2, capture)
