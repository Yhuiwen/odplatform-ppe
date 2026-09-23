"""Compatibility name for the Phase 5 person tracking adapter."""

from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter

PersonTracker = ByteTrackPersonTrackingAdapter

__all__ = ["PersonTracker"]
