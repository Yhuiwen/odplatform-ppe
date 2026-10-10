"""Exact rational timing and sequential timestamp validation without frame lists."""
from __future__ import annotations

import json
import subprocess
import tempfile
import time
from fractions import Fraction
from pathlib import Path

from offline.jobs import JobError
from offline.media import inspect_video


def probe_cfr(path, settings, cancelled=lambda: False):
    basic = inspect_video(path, settings)
    if basic["input_width"] % 2 or basic["input_height"] % 2:
        raise JobError("UNSUPPORTED_DIMENSIONS", "不支持奇数宽高，不能裁剪或缩放", 422)
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=avg_frame_rate,r_frame_rate,time_base,pix_fmt", "-of", "json", str(path)],
            capture_output=True, timeout=settings.ffprobe_timeout_seconds, check=True)
        stream = json.loads(result.stdout)["streams"][0]
        fps = Fraction(stream["avg_frame_rate"])
        tick = Fraction(stream["time_base"])
        if fps <= 0 or fps > 240 or tick <= 0 or fps != Fraction(stream["r_frame_rate"]):
            raise ValueError("timing")
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError) as exc:
        raise JobError("UNSUPPORTED_TIMING", "视频精确帧率或时间基无效", 422) from exc
    # FFprobe decodes timestamps to an anonymous file, not an in-memory list.
    with tempfile.TemporaryFile() as timestamps, tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(["ffprobe", "-v", "error", "-threads", "1", "-select_streams", "v:0", "-show_frames",
            "-show_entries", "frame=best_effort_timestamp", "-of", "csv=p=0", str(path)],
            stdout=timestamps, stderr=errors)
        deadline = time.monotonic() + max(30, settings.ffprobe_timeout_seconds)
        try:
            while process.poll() is None:
                if cancelled():
                    raise JobError("JOB_CANCELLED", "时间戳验证已取消")
                if time.monotonic() > deadline:
                    raise JobError("PROBE_TIMEOUT", "逐帧时间戳验证超时")
                if timestamps.tell() > 32 * 1024 * 1024 or errors.tell() > 65536:
                    raise JobError("PROBE_LIMIT", "视频探测输出超过限制")
                time.sleep(.02)
            errors.seek(0)
            if process.returncode or errors.read(1):
                raise JobError("INVALID_MEDIA", "视频存在解码错误", 422)
            timestamps.seek(0)
            count, first, previous = 0, None, None
            interval_ticks = 1 / fps / tick
            lower = interval_ticks.numerator // interval_ticks.denominator
            upper = -(-interval_ticks.numerator // interval_ticks.denominator)
            for line in timestamps:
                token = line.decode("ascii").strip().split(",")[0]
                if not token:
                    continue
                try:
                    pts = int(token) * tick
                except ValueError as exc:
                    raise JobError("UNSUPPORTED_TIMING", "视频帧缺少有效时间戳", 422) from exc
                if first is None:
                    first = pts
                if previous is not None:
                    delta = (pts - previous) / tick
                    if delta <= 0 or delta not in {lower, upper}:
                        raise JobError("UNSUPPORTED_TIMING", f"视频帧间隔不是恒定帧率（帧 {count}，间隔 tick={delta}，预期 {lower}/{upper}，FPS={fps}，time_base={tick}）", 422)
                if abs(pts - first - Fraction(count, 1) / fps) > tick:
                    raise JobError("UNSUPPORTED_TIMING", "视频逐帧时间戳不是恒定帧率", 422)
                count += 1
                previous = pts
            if count != basic["input_frame_count"] or count == 0:
                raise JobError("FRAME_COUNT_MISMATCH", "视频时间戳帧数与声明不一致", 422)
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
    return basic | {"fps_rational": str(fps), "time_base": str(tick), "pixel_format": stream["pix_fmt"],
                    "timestamp_frames": count, "timestamp_validation": "CFR_VERIFIED"}
