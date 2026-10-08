"""Isolated native capture helper for the non-production P9-C.3 rewind control."""

from __future__ import annotations

from pathlib import Path

import cv2


def open_diagnostic_capture(path: Path):
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError("persistent diagnostic capture did not open")
    return capture
