"""Measure optional live TTS invocation and separate speech wait time."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schemas.alerts import AlertMessage
from core.schemas.compliance import ComplianceEventType
from infra.alerts.tts import TTSAlertAdapter
from infra.tts.tts_service import TTSService, _pyttsx3_engine_factory


timings: dict[str, float] = {}


class TimedEngine:
    def __init__(self, target) -> None:
        self.target = target

    def say(self, message: str) -> None:
        start = perf_counter_ns()
        try:
            self.target.say(message)
        finally:
            timings["say_enqueue_ms"] = (perf_counter_ns() - start) / 1_000_000

    def runAndWait(self) -> None:
        start = perf_counter_ns()
        try:
            self.target.runAndWait()
        finally:
            timings["speech_wait_ms"] = (perf_counter_ns() - start) / 1_000_000

    def stop(self) -> None:
        self.target.stop()


def engine_factory(rate: int, volume: float):
    start = perf_counter_ns()
    try:
        return TimedEngine(_pyttsx3_engine_factory(rate, volume))
    finally:
        timings["engine_init_ms"] = (perf_counter_ns() - start) / 1_000_000


def main() -> int:
    service = TTSService(engine_factory=engine_factory, rate=180, volume=1.0)
    adapter = TTSAlertAdapter(service, enabled=True, cooldown_seconds=30.0)
    message = AlertMessage(
        event_id="P9C-TTS-DIAGNOSTIC",
        timestamp=datetime.now(timezone.utc).isoformat(),
        track_id=0,
        alert_type=ComplianceEventType.NO_HELMET,
        confidence=1.0,
        snapshot=None,
        message="安全提示",
    )
    started = perf_counter_ns()
    result = adapter.send(message)
    timings["adapter_call_ms"] = (perf_counter_ns() - started) / 1_000_000
    service.close()
    output = {"label": "ISOLATED TTS DIAGNOSTIC, NOT LIVE PIPELINE", "status": result.status.value, "error_code": result.error_code, **timings}
    target = ROOT / "artifacts/p9c/tts-diagnostic.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
