"""Chinese text-to-speech service used by the Phase 7 alert adapter."""

from __future__ import annotations

from threading import Lock
from typing import Any, Callable

__all__ = [
    "TTSBackendError",
    "TTSService",
    "TTSServiceError",
    "TTSUnavailableError",
]

Speaker = Callable[[str], None]
EngineFactory = Callable[[int, float], Any]


class TTSServiceError(RuntimeError):
    """Base TTS failure with a stable machine-readable code."""

    code = "TTS_FAILED"


class TTSUnavailableError(TTSServiceError):
    code = "TTS_UNAVAILABLE"


class TTSBackendError(TTSServiceError):
    code = "TTS_BACKEND_FAILED"


class TTSService:
    """Synthesize one Chinese alert message through an injectable backend."""

    def __init__(
        self,
        *,
        speaker: Speaker | None = None,
        engine_factory: EngineFactory | None = None,
        rate: int = 180,
        volume: float = 1.0,
    ) -> None:
        if speaker is not None and not callable(speaker):
            raise TypeError("speaker must be callable or None")
        if engine_factory is not None and not callable(engine_factory):
            raise TypeError("engine_factory must be callable or None")
        if isinstance(rate, bool) or not isinstance(rate, int):
            raise TypeError("rate must be an integer")
        if rate <= 0:
            raise ValueError("rate must be positive")
        if isinstance(volume, bool) or not isinstance(volume, (int, float)):
            raise TypeError("volume must be numeric")
        normalized_volume = float(volume)
        if not 0.0 <= normalized_volume <= 1.0:
            raise ValueError("volume must be between 0 and 1")

        self.speaker = speaker
        self.engine_factory = engine_factory or _pyttsx3_engine_factory
        self.rate = rate
        self.volume = normalized_volume
        self._engine: Any | None = None
        self._lock = Lock()

    def speak(self, message: str) -> None:
        """Speak one non-empty message and fail with a stable error code."""

        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        normalized = message.strip()
        if self.speaker is not None:
            try:
                self.speaker(normalized)
            except Exception as exc:
                raise TTSBackendError(
                    f"TTS speaker failed: {type(exc).__name__}"
                ) from exc
            return

        with self._lock:
            engine = self._get_engine()
            try:
                engine.say(normalized)
                engine.runAndWait()
            except Exception as exc:
                raise TTSBackendError(
                    f"TTS backend failed: {type(exc).__name__}"
                ) from exc

    def close(self) -> None:
        """Release the lazily created engine when the backend supports it."""

        with self._lock:
            engine = self._engine
            self._engine = None
        if engine is None:
            return
        stop = getattr(engine, "stop", None)
        if callable(stop):
            try:
                stop()
            except Exception:
                return

    def _get_engine(self) -> Any:
        if self._engine is not None:
            return self._engine
        try:
            engine = self.engine_factory(self.rate, self.volume)
        except TTSServiceError:
            raise
        except ImportError as exc:
            raise TTSUnavailableError(
                "pyttsx3 is required for the default TTS backend"
            ) from exc
        except Exception as exc:
            raise TTSUnavailableError(
                f"Could not initialize the TTS backend: {type(exc).__name__}"
            ) from exc
        self._engine = engine
        return engine


def _pyttsx3_engine_factory(rate: int, volume: float) -> Any:
    """Create the optional pyttsx3 engine only when speech is requested."""

    try:
        import pyttsx3
    except ImportError as exc:
        raise TTSUnavailableError(
            "pyttsx3 is required for the default TTS backend"
        ) from exc

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)
    return engine
