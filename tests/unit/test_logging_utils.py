import logging
from pathlib import Path

import pytest

from utils.logging_utils import configure_logging, shutdown_logging


def test_logging_writes_to_console_and_file(tmp_path: Path) -> None:
    logger_name = "odplatform.test.file"
    logger = configure_logging(
        tmp_path,
        filename="unit.log",
        logger_name=logger_name,
        reset=True,
    )
    try:
        logger.info("phase-zero-log-check")
        for handler in logger.handlers:
            handler.flush()
        content = (tmp_path / "unit.log").read_text(encoding="utf-8")
        assert "phase-zero-log-check" in content
        assert any(
            isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, logging.FileHandler)
            for handler in logger.handlers
        )
    finally:
        shutdown_logging(logger_name)


def test_invalid_log_level_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported log level"):
        configure_logging(
            tmp_path,
            level="TRACE",
            logger_name="odplatform.test.invalid",
            reset=True,
        )
