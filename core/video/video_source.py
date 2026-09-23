"""Unified lifecycle contract for MP4, USB camera and RTSP inputs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Protocol, runtime_checkable

from core.schemas.events import format_utc_timestamp
from core.schemas.video import (
    FrameData,
    SourceMetadata,
    SourceState,
    SourceStatus,
    SourceType,
)

__all__ = [
    "BaseVideoSource",
    "InvalidVideoSourceError",
    "VideoSource",
    "VideoSourceDisconnectedError",
    "VideoSourceError",
    "VideoSourceOpenError",
    "VideoSourceReadError",
    "VideoSourceReleaseError",
    "VideoSourceStateError",
    "VideoSourceTimeoutError",
]


class VideoSourceError(RuntimeError):
    """Base source failure with a stable machine-readable code."""

    code = "SOURCE_FAILED"


class InvalidVideoSourceError(VideoSourceError):
    code = "UNSUPPORTED_INPUT"


class VideoSourceOpenError(VideoSourceError):
    code = "SOURCE_OPEN_FAILED"


class VideoSourceReadError(VideoSourceError):
    code = "SOURCE_READ_FAILED"


class VideoSourceTimeoutError(VideoSourceError):
    code = "SOURCE_TIMEOUT"


class VideoSourceDisconnectedError(VideoSourceError):
    code = "SOURCE_DISCONNECTED"


class VideoSourceStateError(VideoSourceError):
    code = "SOURCE_INVALID_STATE"


class VideoSourceReleaseError(VideoSourceError):
    code = "SOURCE_RELEASE_FAILED"


@runtime_checkable
class VideoSource(Protocol):
    """One open/read/status/close lifecycle shared by every input adapter."""

    metadata: SourceMetadata | None
    source_type: SourceType

    def open(self) -> SourceMetadata:
        ...

    def read(self) -> FrameData | None:
        ...

    def status(self) -> SourceStatus:
        ...

    def close(self) -> None:
        ...


class BaseVideoSource:
    """State tracking and cleanup shared by concrete source adapters."""

    source_type: SourceType

    def __init__(
        self,
        *,
        wall_clock: Callable[[], datetime] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        if not hasattr(self, "source_type"):
            raise TypeError("source adapter must define source_type")
        self._wall_clock = wall_clock or (lambda: datetime.now(timezone.utc))
        self._monotonic_clock = monotonic_clock
        self._metadata: SourceMetadata | None = None
        self._state = SourceState.IDLE
        self._last_frame_id: int | None = None
        self._last_frame_at: str | None = None
        self._error_code: str | None = None
        self._error_message: str | None = None
        self._reconnect_count = 0
        self._opened_at: float | None = None
        self._last_timestamp = -1.0

    @property
    def metadata(self) -> SourceMetadata | None:
        return self._metadata

    def status(self) -> SourceStatus:
        return SourceStatus(
            state=self._state,
            last_frame_id=self._last_frame_id,
            last_frame_at=self._last_frame_at,
            error_code=self._error_code,
            error_message=self._error_message,
            reconnect_count=self._reconnect_count,
        )

    def __enter__(self) -> BaseVideoSource:
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def _mark_opening(self) -> None:
        self._state = SourceState.OPENING
        self._error_code = None
        self._error_message = None

    def _mark_live(self, metadata: SourceMetadata) -> None:
        if not isinstance(metadata, SourceMetadata):
            raise TypeError("metadata must be SourceMetadata")
        if metadata.source_type is not self.source_type:
            raise ValueError("metadata source_type must match the adapter")
        self._metadata = metadata
        self._state = SourceState.LIVE
        self._opened_at = self._monotonic()
        self._last_timestamp = -1.0

    def _mark_ended(self) -> None:
        self._state = SourceState.ENDED
        self._error_code = None
        self._error_message = None

    def _mark_failed(
        self,
        code: str,
        message: str,
        *,
        degraded: bool = False,
    ) -> None:
        self._state = SourceState.DEGRADED if degraded else SourceState.FAILED
        self._error_code = code
        self._error_message = message

    def _record_frame(self, frame: FrameData) -> FrameData:
        if not isinstance(frame, FrameData):
            raise TypeError("frame must be FrameData")
        self._last_frame_id = frame.frame_id
        self._last_frame_at = format_utc_timestamp(self._wall_clock())
        self._last_timestamp = frame.timestamp
        self._state = SourceState.LIVE
        self._error_code = None
        self._error_message = None
        return frame

    def _next_live_timestamp(self) -> float:
        now = self._monotonic()
        elapsed = now - (self._opened_at if self._opened_at is not None else now)
        timestamp = max(0.0, elapsed)
        if timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1e-6
        return timestamp

    def _monotonic(self) -> float:
        if self._monotonic_clock is not None:
            return float(self._monotonic_clock())
        import time

        return time.monotonic()

    def close(self) -> None:
        if self._state is SourceState.CLOSED:
            return
        release_error: Exception | None = None
        try:
            self._release()
        except Exception as exc:
            release_error = exc
        finally:
            self._metadata = None
            self._opened_at = None
            self._state = SourceState.CLOSED
        if release_error is not None:
            self._mark_failed(
                VideoSourceReleaseError.code,
                f"{type(release_error).__name__}: {release_error}",
            )
            raise VideoSourceReleaseError(
                f"Could not release source: {type(release_error).__name__}"
            ) from release_error

    def _release(self) -> None:
        """Release adapter-owned resources; subclasses override when needed."""
