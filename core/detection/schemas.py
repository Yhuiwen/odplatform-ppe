"""Stable detection schemas used by future phases."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class DetectionClass(IntEnum):
    PERSON = 0
    HARDHAT = 1
    NO_HARDHAT = 2
    VEST = 3
    NO_VEST = 4


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("Bounding box must satisfy x2 > x1 and y2 > y1")

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    def as_tuple(self) -> tuple[float, float, float, float]:
        return self.x1, self.y1, self.x2, self.y2


@dataclass(frozen=True, slots=True)
class Detection:
    bbox: BoundingBox
    class_id: int
    class_name: str
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Detection confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class FrameMeta:
    frame_id: int
    timestamp: float
    width: int
    height: int
    source: str

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id cannot be negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Frame dimensions must be positive")
