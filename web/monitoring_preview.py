"""Local, session-isolated MJPEG preview for completed monitoring frames."""

from __future__ import annotations

import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Condition, Lock, Thread
from weakref import WeakValueDictionary


class PreviewChannel:
    """Keep only the newest encoded frame; slow viewers never block inference."""

    def __init__(self) -> None:
        import cv2
        import numpy as np

        self.token = secrets.token_urlsafe(32)
        self._condition = Condition()
        self._sequence = 1
        ok, placeholder = cv2.imencode(
            ".jpg", np.zeros((180, 320, 3), dtype=np.uint8)
        )
        if not ok:
            raise RuntimeError("could not initialize preview stream")
        self._jpeg: bytes = placeholder.tobytes()

    def publish(self, frame_id: int, image: object) -> None:
        import cv2

        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not ok:
            raise ValueError(f"could not encode preview frame {frame_id}")
        with self._condition:
            self._jpeg = encoded.tobytes()
            self._sequence += 1
            self._condition.notify_all()

    def after(self, sequence: int, timeout: float = 10.0) -> tuple[int, bytes] | None:
        with self._condition:
            self._condition.wait_for(lambda: self._sequence > sequence, timeout)
            # Re-send the current frame as a heartbeat so closed clients are
            # released even when monitoring has stopped or has not started.
            return self._sequence, self._jpeg


class PreviewHub:
    """One loopback HTTP listener shared by browser sessions in this process."""

    def __init__(self) -> None:
        self._channels: WeakValueDictionary[str, PreviewChannel] = WeakValueDictionary()
        self._lock = Lock()
        hub = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                prefix = "/preview/"
                if not self.path.startswith(prefix):
                    self.send_error(404)
                    return
                token = self.path[len(prefix) :]
                with hub._lock:
                    channel = hub._channels.get(token)
                if channel is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                sequence = 0
                try:
                    while True:
                        current = channel.after(sequence)
                        if current is None:
                            continue
                        sequence, jpeg = current
                        self.wfile.write(
                            b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                            + str(len(jpeg)).encode("ascii")
                            + b"\r\n\r\n"
                            + jpeg
                            + b"\r\n"
                        )
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return

            def log_message(self, format: str, *args: object) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def register(self, channel: PreviewChannel) -> str:
        with self._lock:
            self._channels[channel.token] = channel
        port = self._server.server_address[1]
        return f"http://127.0.0.1:{port}/preview/{channel.token}"

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


_hub: PreviewHub | None = None
_hub_lock = Lock()


def get_preview_hub() -> PreviewHub:
    global _hub
    with _hub_lock:
        if _hub is None:
            _hub = PreviewHub()
        return _hub
