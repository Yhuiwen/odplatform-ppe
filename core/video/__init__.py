"""Unified MP4, USB camera and RTSP input support."""

from core.video.mp4_source import MP4VideoSource
from core.video.reader import (
    EmptyVideoError,
    InvalidVideoFormatError,
    VideoDecodeError,
    VideoError,
    VideoNotFoundError,
    VideoReader,
    VideoRuntimeUnavailableError,
)
from core.video.rtsp_source import RTSPVideoSource, redact_rtsp_uri
from core.video.usb_camera_source import USBCameraSource
from core.video.video_source import (
    BaseVideoSource,
    InvalidVideoSourceError,
    VideoSource,
    VideoSourceDisconnectedError,
    VideoSourceError,
    VideoSourceOpenError,
    VideoSourceReadError,
    VideoSourceReleaseError,
    VideoSourceStateError,
    VideoSourceTimeoutError,
)

__all__ = [
    "BaseVideoSource",
    "EmptyVideoError",
    "InvalidVideoFormatError",
    "InvalidVideoSourceError",
    "MP4VideoSource",
    "RTSPVideoSource",
    "USBCameraSource",
    "VideoDecodeError",
    "VideoError",
    "VideoNotFoundError",
    "VideoReader",
    "VideoRuntimeUnavailableError",
    "VideoSource",
    "VideoSourceDisconnectedError",
    "VideoSourceError",
    "VideoSourceOpenError",
    "VideoSourceReadError",
    "VideoSourceReleaseError",
    "VideoSourceStateError",
    "VideoSourceTimeoutError",
    "redact_rtsp_uri",
]
