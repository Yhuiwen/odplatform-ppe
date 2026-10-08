"""Fixed real MP4 frames for the diagnostic interaction matrix."""

from __future__ import annotations

from core.schemas.video import SourceState, SourceType
from core.video.mp4_source import MP4VideoSource
from core.video.video_source import BaseVideoSource


def load_cached_frames(path):
    source = MP4VideoSource(path)
    metadata = source.open()
    try:
        frames = tuple(iter(source.read, None))
    finally:
        source.close()
    if len(frames) != 47:
        raise AssertionError(f"expected 47 real MP4 frames, got {len(frames)}")
    return metadata, frames


class CachedFrameSource(BaseVideoSource):
    """Replay the same decoded FrameData objects; no decoder in cycles."""

    source_type = SourceType.MP4

    def __init__(self, metadata, frames):
        super().__init__()
        self._cached_metadata = metadata
        self._cached_frames = frames
        self._index = 0

    def open(self):
        self._mark_opening()
        self._index = 0
        self._mark_live(self._cached_metadata)
        return self._cached_metadata

    def read(self):
        if self._state is not SourceState.LIVE:
            raise RuntimeError("cached source must be opened before reading")
        if self._index >= len(self._cached_frames):
            self._mark_ended()
            return None
        frame = self._cached_frames[self._index]
        self._index += 1
        return self._record_frame(frame)


class CachedSourceFactory:
    def __init__(self, metadata, frames):
        self.metadata = metadata
        self.frames = frames
        self.created = 0

    def __call__(self, _request):
        self.created += 1
        return CachedFrameSource(self.metadata, self.frames)
