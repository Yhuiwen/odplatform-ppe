"""Bounded upload inspection without invoking the detection model."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from offline.jobs import JobError, OfflineSettings


EXTENSIONS = {".jpg": ("image", "image/jpeg"), ".jpeg": ("image", "image/jpeg"), ".png": ("image", "image/png"), ".mp4": ("video", "video/mp4")}


def clean_filename(name: str) -> tuple[str, str, str]:
    if not name or name in {".", ".."} or any(c in name for c in ("/", "\\", "\x00")) or any(ord(c) < 32 for c in name) or len(name) > 200:
        raise JobError("INVALID_FILENAME", "文件名无效", 422)
    suffix = Path(name).suffix.lower()
    if suffix not in EXTENSIONS:
        raise JobError("UNSUPPORTED_MEDIA", "仅支持 JPG、PNG 和 MP4", 415)
    return suffix, *EXTENSIONS[suffix]


def inspect_image(path: Path, suffix: str, settings: OfflineSettings) -> dict:
    try:
        with Image.open(path) as image:
            expected = "JPEG" if suffix in {".jpg", ".jpeg"} else "PNG"
            if image.format != expected:
                raise JobError("MEDIA_TYPE_MISMATCH", "文件扩展名与图片格式不符", 415)
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > settings.max_pixels:
                raise JobError("PIXEL_LIMIT", "图片像素尺寸超过限制", 413)
            image.verify()
        with Image.open(path) as image:
            with ImageOps.exif_transpose(image) as oriented:
                width, height = oriented.size
                oriented.load()
    except JobError:
        raise
    except (OSError, ValueError, ImportError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise JobError("INVALID_MEDIA", "图片无法完整解码", 422) from exc
    return {"input_width": width, "input_height": height, "input_mime": "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"}


def _fraction(value: str) -> float | None:
    try:
        numerator, denominator = value.split("/", 1)
        result = float(numerator) / float(denominator)
        return result if math.isfinite(result) and result > 0 else None
    except (ValueError, ZeroDivisionError, AttributeError):
        return None


def inspect_video(path: Path, settings: OfflineSettings, *, probe=None) -> dict:
    with path.open("rb") as handle:
        header = handle.read(16)
    if len(header) < 12 or header[4:8] != b"ftyp":
        raise JobError("MEDIA_TYPE_MISMATCH", "文件不是有效的 MP4 容器", 415)
    if probe is None:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames:stream_tags=rotate:stream_side_data=rotation", "-of", "json", str(path)],
                capture_output=True, text=True, timeout=settings.ffprobe_timeout_seconds, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise JobError("PROBE_UNAVAILABLE", "视频探测工具不可用或超时", 503) from exc
        if result.returncode or len(result.stdout) > 1024 * 1024:
            raise JobError("INVALID_MEDIA", "视频无法探测", 422)
        try:
            probe = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise JobError("INVALID_MEDIA", "视频元数据无效", 422) from exc
    if not isinstance(probe, dict) or not isinstance(probe.get("streams"), list):
        raise JobError("INVALID_MEDIA", "视频元数据无效", 422)
    streams = probe["streams"]
    videos = [item for item in streams if item.get("codec_type") == "video"]
    if len(videos) != 1:
        raise JobError("INVALID_MEDIA", "MP4 必须包含一路视频", 422)
    stream = videos[0]
    try:
        width, height = int(stream.get("width") or 0), int(stream.get("height") or 0)
    except (TypeError, ValueError) as exc:
        raise JobError("INVALID_MEDIA", "视频尺寸元数据无效", 422) from exc
    if width <= 0 or height <= 0 or width * height > settings.max_pixels:
        raise JobError("PIXEL_LIMIT", "视频像素尺寸超过限制", 413)
    try:
        duration = float(probe.get("format", {}).get("duration"))
    except (ValueError, TypeError) as exc:
        raise JobError("INVALID_MEDIA", "视频时长不可用", 422) from exc
    if not math.isfinite(duration) or duration <= 0:
        raise JobError("INVALID_MEDIA", "视频时长无效", 422)
    if duration > settings.video_max_seconds:
        raise JobError("DURATION_LIMIT", "视频时长超过限制", 413)
    fps = _fraction(stream.get("avg_frame_rate"))
    nominal = _fraction(stream.get("r_frame_rate"))
    if fps is None or nominal is None or abs(fps - nominal) > 0.001:
        raise JobError("UNSUPPORTED_TIMING", "暂不支持可变帧率或无效时间戳视频", 422)
    try:
        count = int(stream.get("nb_frames"))
    except (ValueError, TypeError) as exc:
        raise JobError("UNSUPPORTED_TIMING", "视频帧数不可用", 422) from exc
    if count <= 0 or abs(count / fps - duration) > max(1.0, duration * 0.02):
        raise JobError("UNSUPPORTED_TIMING", "视频帧数与时长不一致", 422)
    rotation = stream.get("tags", {}).get("rotate")
    side_rotation = [item.get("rotation") for item in stream.get("side_data_list", []) if "rotation" in item]
    try:
        rotated = (rotation is not None and float(rotation) % 360 != 0) or any(float(value) % 360 != 0 for value in side_rotation)
    except (TypeError, ValueError) as exc:
        raise JobError("INVALID_MEDIA", "视频旋转元数据无效", 422) from exc
    if rotated:
        raise JobError("UNSUPPORTED_ROTATION", "暂不支持带旋转元数据的视频", 422)
    return {"input_width":width,"input_height":height,"input_fps":fps,"input_frame_count":count,"input_duration_seconds":duration,"input_mime":"video/mp4","input_codec":stream.get("codec_name"),"has_audio":any(item.get("codec_type") == "audio" for item in streams)}
