"""Read-only timing for frames already published to the MJPEG preview."""

from collections import deque
from threading import Lock
from time import monotonic
from typing import Callable


class PreviewTelemetry:
    def __init__(self, publish: Callable, *, clock: Callable[[], float] = monotonic):
        self._publish = publish
        self._clock = clock
        self._times = deque(maxlen=120)
        self._lock = Lock()

    def publish(self, frame_id: int, image: object) -> None:
        self._publish(frame_id, image)
        with self._lock:
            self._times.append(self._clock())

    def status(self, *, running: bool) -> dict[str, float | int | None]:
        if not running:
            return {'preview_fps': None, 'preview_age_ms': None}
        with self._lock:
            now = self._clock()
            recent = [t for t in self._times if now - t <= 3.0]
        if not recent:
            return {'preview_fps': None, 'preview_age_ms': None}
        age_ms = max(0, round((now - recent[-1]) * 1000))
        span = recent[-1] - recent[0]
        fps = round((len(recent) - 1) / span, 1) if len(recent) > 1 and span > 0 else None
        return {'preview_fps': fps, 'preview_age_ms': age_ms}
