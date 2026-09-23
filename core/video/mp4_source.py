"""MP4 adapter over the existing sequential :class:`VideoReader`."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator

from core.schemas.video import (
    FrameData,
    SourceMetadata,
    SourceState,
    SourceType,
)
from core.video.reader import (
    EmptyVideoError,
    InvalidVideoFormatError,
    VideoDecodeError,
    VideoError,
    VideoNotFoundError,
    VideoReader,
    VideoRuntimeUnavailableError,
)
from core.video.video_source import (
    BaseVideoSource,
    InvalidVideoSourceError,
    VideoSourceOpenError,
    VideoSourceReadError,
    VideoSourceStateError,
)

__all__ = ["MP4VideoSource"]

ReaderFactory = Callable[[str | Path], VideoReader]


class MP4VideoSource(BaseVideoSource):
    """Expose one local MP4 file through the common VideoSource lifecycle."""

    source_type = SourceType.MP4

    def __init__(
        self,
        source: str | Path,
        *,
        reader_factory: ReaderFactory | None = None,
        wall_clock: Callable[[], Any] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        super().__init__(
            wall_clock=wall_clock,
            monotonic_clock=monotonic_clock,
        )
        if not isinstance(source, (str, Path)):
            raise InvalidVideoSourceError("MP4 source must be a filesystem path")
        self.source = Path(source).expanduser()
        self._reader_factory = reader_factory or VideoReader
        self._reader: VideoReader | None = None
        self._frames: Iterator[FrameData] | None = None

    def open(self) -> SourceMetadata:
        if self._state is SourceState.LIVE:
            assert self._metadata is not None
            return self._metadata

        self._mark_opening()
        reader: VideoReader | None = None
        try:
            reader = self._reader_factory(self.source)
            metadata = reader.open()
            source_metadata = SourceMetadata(
                source_id=f"mp4:{self.source.name}",
                source_type=SourceType.MP4,
                display_name=self.source.name,
                width=metadata.width,
                height=metadata.height,
                fps=metadata.fps,
                frame_count=metadata.frame_count,
            )
            self._reader = reader
            self._frames = reader.iter_frames()
            self._mark_live(source_metadata)
            return source_metadata
        except Exception as exc:
            if reader is not None:
                try:
                    reader.close()
                except Exception:
                    pass
            self._reader = None
            self._frames = None
            error = self._open_error(exc)
            self._mark_failed(error.code, str(error))
            raise error from exc

    @staticmethod
    def _open_error(exc: Exception) -> VideoSourceOpenError | InvalidVideoSourceError:
        if isinstance(
            exc,
            (
                VideoNotFoundError,
                InvalidVideoFormatError,
                EmptyVideoError,
                VideoRuntimeUnavailableError,
                VideoDecodeError,
            ),
        ):
            return InvalidVideoSourceError(str(exc))
        return VideoSourceOpenError(
            f"Could not open MP4 source: {type(exc).__name__}"
        )

    def read(self) -> FrameData | None:
        if self._state not in {SourceState.LIVE, SourceState.DEGRADED}:
            raise VideoSourceStateError("MP4 source must be opened before reading")
        assert self._frames is not None
        try:
            frame = next(self._frames)
        except StopIteration:
            self._mark_ended()
            return None
        except VideoError as exc:
            self._mark_failed(VideoSourceReadError.code, str(exc))
            raise VideoSourceReadError(str(exc)) from exc
        except Exception as exc:
            self._mark_failed(VideoSourceReadError.code, type(exc).__name__)
            raise VideoSourceReadError(
                f"Could not read MP4 frame: {type(exc).__name__}"
            ) from exc
        return self._record_frame(frame)

    def _release(self) -> None:
        try:
            if self._reader is not None:
                self._reader.close()
        finally:
            self._reader = None
            self._frames = None
