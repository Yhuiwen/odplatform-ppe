"""USB camera adapter with bounded lifecycle and observable failures."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from core.schemas.video import FrameData, SourceMetadata, SourceState, SourceType
from core.video.video_source import (
    BaseVideoSource,
    InvalidVideoSourceError,
    VideoSourceDisconnectedError,
    VideoSourceOpenError,
    VideoSourceReadError,
    VideoSourceStateError,
)

__all__ = ["USBCameraSource"]

CaptureFactory = Callable[[int], Any]


class USBCameraSource(BaseVideoSource):
    """Open one bounded local camera index through ``cv2.VideoCapture``."""

    source_type = SourceType.USB_CAMERA

    def __init__(
        self,
        device_index: int,
        *,
        capture_factory: CaptureFactory | None = None,
        wall_clock: Callable[[], datetime] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        super().__init__(
            wall_clock=wall_clock,
            monotonic_clock=monotonic_clock,
        )
        if isinstance(device_index, bool) or not isinstance(device_index, int):
            raise InvalidVideoSourceError("USB camera device index must be an integer")
        if device_index < 0:
            raise InvalidVideoSourceError(
                "USB camera device index cannot be negative"
            )
        self.device_index = device_index
        self._capture_factory = capture_factory
        self._capture: Any | None = None

    def open(self) -> SourceMetadata:
        if self._state is SourceState.LIVE:
            assert self._metadata is not None
            return self._metadata
        if self._capture is not None:
            raise VideoSourceStateError("USB camera source is already open")

        self._mark_opening()
        try:
            capture = self._create_capture()
            if capture is None or not self._is_opened(capture):
                if capture is not None:
                    capture.release()
                raise VideoSourceOpenError(
                    f"Could not open USB camera index {self.device_index}"
                )
            metadata = SourceMetadata(
                source_id=f"usb:{self.device_index}",
                source_type=SourceType.USB_CAMERA,
                display_name=f"USB Camera {self.device_index}",
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
                f"Could not open USB camera index {self.device_index}"
            )
            self._mark_failed(error.code, str(error))
            raise error from exc

        self._capture = capture
        self._mark_live(metadata)
        return metadata

    def read(self) -> FrameData | None:
        if self._state is not SourceState.LIVE or self._capture is None:
            raise VideoSourceStateError("USB camera source must be opened before reading")
        try:
            ok, image = self._capture.read()
        except Exception as exc:
            self._mark_failed(VideoSourceReadError.code, type(exc).__name__)
            raise VideoSourceReadError(
                f"Could not read USB camera index {self.device_index}"
            ) from exc
        if not ok or image is None:
            self._mark_failed(
                VideoSourceDisconnectedError.code,
                f"USB camera index {self.device_index} stopped returning frames",
            )
            raise VideoSourceDisconnectedError(
                f"USB camera index {self.device_index} disconnected"
            )

        frame = FrameData(
            frame_id=0 if self._last_frame_id is None else self._last_frame_id + 1,
            timestamp=self._next_live_timestamp(),
            image=image,
        )
        return self._record_frame(frame)

    def _create_capture(self) -> Any:
        if self._capture_factory is not None:
            return self._capture_factory(self.device_index)
        try:
            import cv2
        except ImportError as exc:
            raise VideoSourceOpenError(
                "OpenCV is required for USB camera input"
            ) from exc
        return cv2.VideoCapture(self.device_index)

    @staticmethod
    def _is_opened(capture: Any) -> bool:
        is_opened = getattr(capture, "isOpened", None)
        return bool(is_opened()) if callable(is_opened) else True

    def _positive_int_property(self, capture: Any, name: str) -> int | None:
        code = self._property_code(name)
        if code is None:
            return None
        try:
            value = int(capture.get(code))
        except (AttributeError, TypeError, ValueError):
            return None
        return value if value > 0 else None

    def _positive_float_property(self, capture: Any, name: str) -> float | None:
        code = self._property_code(name)
        if code is None:
            return None
        try:
            value = float(capture.get(code))
        except (AttributeError, TypeError, ValueError):
            return None
        return value if value > 0 else None

    @staticmethod
    def _property_code(name: str) -> int | None:
        # These OpenCV constants are stable public ABI values. Keeping the
        # numeric fallbacks lets injected capture doubles run without cv2.
        mapping = {
            "width": 3,
            "height": 4,
            "fps": 5,
        }
        return mapping[name]

    def _release(self) -> None:
        try:
            if self._capture is not None:
                self._capture.release()
        finally:
            self._capture = None
