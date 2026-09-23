"""RTSP adapter with URI redaction and observable connection failures."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from urllib.parse import urlsplit

from core.schemas.video import FrameData, SourceMetadata, SourceState, SourceType
from core.video.video_source import (
    BaseVideoSource,
    InvalidVideoSourceError,
    VideoSourceDisconnectedError,
    VideoSourceOpenError,
    VideoSourceReadError,
    VideoSourceStateError,
)

__all__ = ["RTSPVideoSource", "redact_rtsp_uri"]

CaptureFactory = Callable[[str], Any]


def redact_rtsp_uri(uri: str) -> str:
    """Return a credential-free, query-free URI suitable for logs/status."""

    if not isinstance(uri, str) or not uri.strip():
        raise InvalidVideoSourceError("RTSP URI cannot be empty")
    candidate = uri.strip()
    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
        parsed_port = parsed.port
    except ValueError as exc:
        raise InvalidVideoSourceError("RTSP URI is invalid") from exc
    if parsed.scheme.lower() not in {"rtsp", "rtsps"}:
        raise InvalidVideoSourceError("RTSP URI must use rtsp:// or rtsps://")
    if not hostname:
        raise InvalidVideoSourceError("RTSP URI must include a hostname")

    port = f":{parsed_port}" if parsed_port is not None else ""
    path = parsed.path or "/"
    return f"{parsed.scheme.lower()}://{hostname}{port}{path}"


class RTSPVideoSource(BaseVideoSource):
    """Open one credential-redacted RTSP stream through OpenCV."""

    source_type = SourceType.RTSP

    def __init__(
        self,
        uri: str,
        *,
        open_timeout_ms: int = 5000,
        read_timeout_ms: int = 5000,
        capture_factory: CaptureFactory | None = None,
        wall_clock: Callable[[], datetime] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        super().__init__(
            wall_clock=wall_clock,
            monotonic_clock=monotonic_clock,
        )
        self.uri = uri.strip() if isinstance(uri, str) else uri
        self.safe_uri = redact_rtsp_uri(uri)
        self.open_timeout_ms = self._validate_timeout(
            open_timeout_ms,
            "open_timeout_ms",
        )
        self.read_timeout_ms = self._validate_timeout(
            read_timeout_ms,
            "read_timeout_ms",
        )
        self._capture_factory = capture_factory
        self._capture: Any | None = None

    @staticmethod
    def _validate_timeout(value: int, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidVideoSourceError(f"{name} must be an integer")
        if value <= 0:
            raise InvalidVideoSourceError(f"{name} must be positive")
        return value

    def open(self) -> SourceMetadata:
        if self._state is SourceState.LIVE:
            assert self._metadata is not None
            return self._metadata
        if self._capture is not None:
            raise VideoSourceStateError("RTSP source is already open")

        self._mark_opening()
        try:
            capture = self._create_capture()
            if capture is None or not self._is_opened(capture):
                if capture is not None:
                    capture.release()
                raise VideoSourceOpenError(
                    f"Could not open RTSP source {self.safe_uri}"
                )
            self._configure_timeouts(capture)
            metadata = SourceMetadata(
                source_id=f"rtsp:{self.safe_uri}",
                source_type=SourceType.RTSP,
                display_name=self.safe_uri,
                width=self._positive_int_property(capture, "width"),
                height=self._positive_int_property(capture, "height"),
                fps=self._positive_float_property(capture, "fps"),
                frame_count=None,
            )
        except VideoSourceOpenError as exc:
            self._mark_failed(exc.code, str(exc))
            raise
        except Exception as exc:
            error = VideoSourceOpenError(
                f"Could not open RTSP source {self.safe_uri}"
            )
            self._mark_failed(error.code, str(error))
            raise error from exc

        self._capture = capture
        self._mark_live(metadata)
        return metadata

    def read(self) -> FrameData | None:
        if self._state is not SourceState.LIVE or self._capture is None:
            raise VideoSourceStateError("RTSP source must be opened before reading")
        try:
            ok, image = self._capture.read()
        except Exception as exc:
            self._mark_failed(VideoSourceReadError.code, type(exc).__name__)
            raise VideoSourceReadError(
                f"Could not read RTSP source {self.safe_uri}"
            ) from exc
        if not ok or image is None:
            self._mark_failed(
                VideoSourceDisconnectedError.code,
                f"RTSP source stopped returning frames: {self.safe_uri}",
            )
            raise VideoSourceDisconnectedError(
                f"RTSP source disconnected: {self.safe_uri}"
            )

        frame = FrameData(
            frame_id=0 if self._last_frame_id is None else self._last_frame_id + 1,
            timestamp=self._next_live_timestamp(),
            image=image,
        )
        return self._record_frame(frame)

    def _create_capture(self) -> Any:
        if self._capture_factory is not None:
            return self._capture_factory(self.uri)
        try:
            import cv2
        except ImportError as exc:
            raise VideoSourceOpenError(
                "OpenCV is required for RTSP input"
            ) from exc
        return cv2.VideoCapture(self.uri)

    @staticmethod
    def _is_opened(capture: Any) -> bool:
        is_opened = getattr(capture, "isOpened", None)
        return bool(is_opened()) if callable(is_opened) else True

    def _configure_timeouts(self, capture: Any) -> None:
        setter = getattr(capture, "set", None)
        if not callable(setter):
            return
        setter(53, float(self.open_timeout_ms))
        setter(54, float(self.read_timeout_ms))

    def _positive_int_property(self, capture: Any, name: str) -> int | None:
        code = self._property_code(name)
        try:
            value = int(capture.get(code))
        except (AttributeError, TypeError, ValueError):
            return None
        return value if value > 0 else None

    def _positive_float_property(self, capture: Any, name: str) -> float | None:
        code = self._property_code(name)
        try:
            value = float(capture.get(code))
        except (AttributeError, TypeError, ValueError):
            return None
        return value if value > 0 else None

    @staticmethod
    def _property_code(name: str) -> int:
        return {"width": 3, "height": 4, "fps": 5}[name]

    def _release(self) -> None:
        try:
            if self._capture is not None:
                self._capture.release()
        finally:
            self._capture = None
