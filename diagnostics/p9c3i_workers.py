"""Bounded diagnostic inference executors; no production service changes."""

from __future__ import annotations

from queue import Queue
from threading import Thread


class PersistentCycleWorker:
    """One worker processes successive complete inference cycles serially."""

    def __init__(self, process_cycle):
        self._process_cycle = process_cycle
        self._requests = Queue(maxsize=1)
        self._results = Queue(maxsize=1)
        self._thread = Thread(target=self._loop, name="p9c3i-persistent-inference")
        self._thread.start()
        self.created = 1
        self.joined = 0

    def _loop(self):
        while True:
            request = self._requests.get()
            if request is None:
                return
            try:
                result = (True, self._process_cycle(*request))
            except BaseException as exc:
                result = (False, exc)
            self._results.put(result)

    def run_cycle(self, frames, source, fixture=None):
        self._requests.put((frames, source, fixture))
        ok, result = self._results.get()
        if not ok:
            raise result
        return result

    def close(self):
        if self.joined:
            return
        self._requests.put(None)
        self._thread.join(timeout=30)
        if self._thread.is_alive():
            raise RuntimeError("persistent inference worker failed to join")
        self.joined = 1


class PersistentInferenceAdapter:
    """Synchronous, single-thread inference bridge for diagnostic T4 only."""

    def __init__(self, service, semantic_check=None):
        self.service = service
        self.semantic_check = semantic_check
        self._requests = Queue(maxsize=1)
        self._results = Queue(maxsize=1)
        self._thread = Thread(target=self._loop, name="p9c3i-persistent-frame-inference")
        self._thread.start()
        self.created = 1
        self.joined = 0

    def _loop(self):
        while True:
            request = self._requests.get()
            if request is None:
                return
            frame, source = request
            try:
                detections = self.service.infer_frame(frame, source=source)
                if self.semantic_check is not None:
                    self.semantic_check(frame.frame_id, detections)
                result = (True, detections)
            except BaseException as exc:
                result = (False, exc)
            self._results.put(result)

    def infer_frame(self, frame, *, source):
        if self.joined:
            raise RuntimeError("persistent inference adapter is shut down")
        self._requests.put((frame, source))
        ok, result = self._results.get()
        if not ok:
            raise result
        return result

    def shutdown(self):
        if self.joined:
            return
        self._requests.put(None)
        self._thread.join(timeout=30)
        if self._thread.is_alive():
            raise RuntimeError("persistent inference adapter failed to join")
        self.joined = 1


def run_in_fresh_worker(process_cycle, frames, source, fixture=None):
    """Create, join and release exactly one thread for a cycle."""
    slot = {}

    def target():
        try:
            slot["result"] = process_cycle(frames, source, fixture)
        except BaseException as exc:
            slot["error"] = exc

    worker = Thread(target=target, name="p9c3i-fresh-inference")
    worker.start()
    worker.join(timeout=180)
    if worker.is_alive():
        raise RuntimeError("fresh inference worker failed to join")
    if "error" in slot:
        raise slot["error"]
    return slot["result"]
