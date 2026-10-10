"""Bounded, supervised raw BGR pipe; never silently substitutes a codec."""
from __future__ import annotations

import queue
import subprocess
import threading
import time
from collections import deque
from fractions import Fraction
from pathlib import Path

from offline.jobs import JobError


class VideoEncoder:
    def __init__(self, path: Path, width: int, height: int, fps: Fraction, cancelled=lambda: False, timeout=30):
        if width % 2 or height % 2:
            raise JobError("UNSUPPORTED_DIMENSIONS", "H.264 yuv420p 暂不支持奇数宽高", 422)
        self.width, self.height, self.cancelled, self.timeout = width, height, cancelled, timeout
        self.diagnostics = deque(maxlen=16)
        self.written = 0
        self.requests = queue.Queue(maxsize=1)
        self.done = threading.Event()
        self.error = None
        try:
            self.process = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
                "-f", "rawvideo", "-pixel_format", "bgr24", "-video_size", f"{width}x{height}",
                "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264", "-crf", "18",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except OSError as exc:
            raise JobError("ENCODER_UNAVAILABLE", "FFmpeg 编码器不可用", 503) from exc
        self.stderr_thread = threading.Thread(target=self._drain, name="offline-encoder-stderr")
        self.writer_thread = threading.Thread(target=self._write_loop, name="offline-encoder-pipe")
        self.stderr_thread.start()
        self.writer_thread.start()

    def _drain(self):
        for chunk in iter(lambda: self.process.stderr.read(1024), b""):
            self.diagnostics.append(chunk)

    def _write_loop(self):
        while True:
            payload = self.requests.get()
            if payload is None:
                return
            try:
                submitted = self.process.stdin.write(payload)
                if submitted != len(payload):
                    raise OSError("incomplete encoder pipe write")
                self.process.stdin.flush()
            except (OSError, ValueError) as exc:
                self.error = exc
            finally:
                self.done.set()

    def _wait(self, predicate):
        deadline = time.monotonic() + self.timeout
        while not predicate():
            if self.cancelled():
                self.abort()
                raise JobError("JOB_CANCELLED", "视频编码已取消")
            if time.monotonic() >= deadline:
                self.abort()
                raise JobError("ENCODER_TIMEOUT", "视频编码等待超时")
            time.sleep(.02)

    def write(self, frame):
        if frame.shape != (self.height, self.width, 3) or str(frame.dtype) != "uint8":
            raise JobError("OUTPUT_DIMENSIONS", "编码帧尺寸或像素格式不符")
        self.done.clear()
        self.requests.put(frame.tobytes())
        self._wait(self.done.is_set)
        if self.error or self.process.poll() is not None:
            raise JobError("ENCODER_FAILED", "FFmpeg 帧写入失败")
        self.written += 1

    def finish(self):
        self.requests.put(None)
        self.writer_thread.join(timeout=2)
        self.process.stdin.close()
        self._wait(lambda: self.process.poll() is not None)
        self.stderr_thread.join(timeout=2)
        self.process.stderr.close()
        if self.process.returncode != 0:
            raise JobError("ENCODER_FAILED", "FFmpeg 未正常完成视频编码")

    def abort(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
        # Killing the reader releases a blocked pipe write before handles close.
        if self.writer_thread.is_alive():
            try:
                self.requests.put_nowait(None)
            except queue.Full:
                pass
            self.writer_thread.join(timeout=5)
        self.stderr_thread.join(timeout=5)
        for handle in (self.process.stdin, self.process.stderr):
            if handle and not handle.closed:
                handle.close()
