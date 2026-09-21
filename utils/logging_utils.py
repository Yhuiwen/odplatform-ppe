"""Minimal console and file logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path

from utils.paths import LOGS_DIR


DEFAULT_LOGGER_NAME = "odplatform"
VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}


def _level_value(level: str | int) -> int:
    if isinstance(level, int):
        return level
    normalized = level.upper()
    if normalized not in VALID_LEVELS:
        raise ValueError(
            f"Unsupported log level {level!r}; expected one of {sorted(VALID_LEVELS)}"
        )
    return getattr(logging, normalized)


def _close_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def configure_logging(
    log_dir: str | Path | None = None,
    *,
    level: str | int = "INFO",
    filename: str = "odplatform.log",
    console: bool = True,
    logger_name: str = DEFAULT_LOGGER_NAME,
    reset: bool = False,
) -> logging.Logger:
    """Configure and return a logger with console and file handlers."""

    logger = logging.getLogger(logger_name)
    if logger.handlers and not reset:
        return logger
    if reset:
        _close_handlers(logger)

    resolved_log_dir = Path(log_dir).expanduser().resolve() if log_dir else LOGS_DIR
    resolved_log_dir.mkdir(parents=True, exist_ok=True)
    resolved_level = _level_value(level)

    logger.setLevel(resolved_level)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(
        resolved_log_dir / filename,
        encoding="utf-8",
    )
    file_handler.setLevel(resolved_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(resolved_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return the project logger or a named child logger."""

    if not name:
        return logging.getLogger(DEFAULT_LOGGER_NAME)
    return logging.getLogger(f"{DEFAULT_LOGGER_NAME}.{name}")


def shutdown_logging(logger_name: str = DEFAULT_LOGGER_NAME) -> None:
    """Close and remove handlers for clean shutdown or test isolation."""

    _close_handlers(logging.getLogger(logger_name))
