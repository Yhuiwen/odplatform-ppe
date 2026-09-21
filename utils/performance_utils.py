"""Reusable timing helpers."""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, ParamSpec, TypeVar

from utils.logging_utils import get_logger


P = ParamSpec("P")
R = TypeVar("R")


@contextmanager
def timer(
    label: str,
    *,
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
) -> Iterator[dict[str, float]]:
    """Measure elapsed wall-clock seconds for a block."""

    started = time.perf_counter()
    result = {"elapsed_seconds": 0.0}
    try:
        yield result
    finally:
        result["elapsed_seconds"] = time.perf_counter() - started
        (logger or get_logger()).log(
            level,
            "%s completed in %.6f seconds",
            label,
            result["elapsed_seconds"],
        )


def timed(
    func: Callable[P, R] | None = None,
    *,
    label: str | None = None,
    logger: logging.Logger | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a function and log its execution time."""

    def decorator(callable_: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(callable_)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with timer(label or callable_.__qualname__, logger=logger):
                return callable_(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def elapsed_seconds(started: float) -> float:
    """Return elapsed seconds from a ``time.perf_counter`` value."""

    return time.perf_counter() - started
