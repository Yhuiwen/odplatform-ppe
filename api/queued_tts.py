"""API-owned bounded speech worker; inference never waits for playback."""
from collections import OrderedDict
from datetime import datetime, timezone
from queue import Queue, Empty, Full
from threading import Event, Lock, Thread
import os
from core.schemas.alerts import AlertResult, AlertStatus


class QueuedTTSAdapter:
    name = 'tts'

    def __init__(self, adapter, capacity=32):
        self.adapter = adapter
        self.queue = Queue(maxsize=capacity)
        self.lock = Lock()
        self.closed = Event()
        self.results = OrderedDict()
        self.generation = 0
        self.delivered = self.failed = 0
        self.thread = Thread(target=self._run, name='ppe-speech', daemon=True)
        self.thread.start()

    def start_session(self, callback):
        with self.lock:
            callback()
            self.generation += 1
            self.delivered = self.failed = 0

    def send(self, message):
        with self.lock:
            if message.event_id in self.results:
                return self._receipt(message.event_id, 'TTS_DUPLICATE_QUEUED')
            if self.closed.is_set():
                return self._receipt(message.event_id, 'TTS_WORKER_CLOSED', failed=True)
            receipt = self._receipt(message.event_id, 'TTS_QUEUED')
            self.results[message.event_id] = receipt.to_dict()
            try:
                self.queue.put_nowait((self.generation, message))
            except Full:
                self.results.pop(message.event_id, None)
                return self._receipt(message.event_id, 'TTS_QUEUE_FULL', failed=True)
            while len(self.results) > 2048:
                self.results.popitem(last=False)
            return receipt

    def _receipt(self, event_id, code, failed=False):
        return AlertResult(event_id=event_id, adapter='tts', status=AlertStatus.FAILED if failed else AlertStatus.SKIPPED,
                           timestamp=datetime.now(timezone.utc).isoformat(), error_code=code,
                           error_message='Speech worker status')

    def result(self, event_id):
        with self.lock:
            result = self.results.get(event_id)
            return dict(result) if result else None

    def counts(self):
        with self.lock:
            return self.delivered, self.failed

    def _run(self):
        com = None
        active_generation = None
        try:
            if os.name == 'nt':
                import pythoncom
                pythoncom.CoInitialize()
                com = pythoncom
            prepare = getattr(self.adapter.service.speaker, 'prepare', None)
            if prepare is not None:
                prepare()
            while not self.closed.is_set() or not self.queue.empty():
                try:
                    generation, message = self.queue.get(timeout=.1)
                except Empty:
                    continue
                try:
                    try:
                        if generation != active_generation:
                            # Track identifiers belong to one monitoring session.
                            # Retain the engine on this thread, scope adapter cooldown/dedup to that session.
                            from infra.alerts.tts import TTSAlertAdapter
                            previous = self.adapter
                            self.adapter = TTSAlertAdapter(previous.service, enabled=previous.enabled,
                                cooldown_seconds=previous.cooldown_seconds, clock=previous.clock)
                            active_generation = generation
                        result = self.adapter.send(message)
                    except Exception:
                        result = self._receipt(message.event_id, 'TTS_BACKEND_FAILED', failed=True)
                    with self.lock:
                        self.results[message.event_id] = result.to_dict()
                        if generation == self.generation:
                            self.delivered += int(result.status == AlertStatus.DELIVERED)
                            self.failed += int(result.status == AlertStatus.FAILED)
                finally:
                    self.queue.task_done()
        except Exception:
            # COM startup failure remains observable; never invent delivered receipts.
            self.closed.set()
            with self.lock:
                for event_id, result in list(self.results.items()):
                    if result.get('error_code') == 'TTS_QUEUED':
                        self.results[event_id] = self._receipt(event_id, 'TTS_UNAVAILABLE', failed=True).to_dict()
        finally:
            self.adapter.service.close()
            cleanup = getattr(self.adapter.service.speaker, 'close', None)
            if cleanup is not None:
                cleanup()
            if com is not None:
                com.CoUninitialize()

    def close(self):
        self.closed.set()
        self.thread.join(timeout=5)
