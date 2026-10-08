"""Bounded, non-production stage replacements for MonitoringService attribution."""

from __future__ import annotations

import weakref
from pathlib import Path
from types import SimpleNamespace

from core.events.event_engine import EventEngine
from core.schemas.association import AssociationResult
from core.schemas.compliance import ComplianceResult
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from diagnostics.p9c3a_precomputed import PrecomputedInferenceService
from diagnostics.p9c3b_precomputed_tracking import PrecomputedTrackingAdapter
from scripts.run_p9c3_memory_attribution import CachedFrameSource
from services.event_service import EventService


class EmptyInference:
    def infer_frame(self, frame, *, source: str):
        return ()

    def close(self) -> None:
        pass


class EmptyTracker:
    def update(self, detections, *, frame_id: int, timestamp: float, source: str):
        return ()

    def reset(self) -> None:
        pass


class EmptyAssociation:
    def associate(self, tracks, ppe, *, frame_id: int, timestamp: float, source: str):
        return AssociationResult(frame_id=frame_id, timestamp=timestamp, source=source)


class EmptyCompliance:
    def evaluate(self, association: AssociationResult):
        return ComplianceResult(frame_id=association.frame_id, timestamp=association.timestamp)


class EmptyEvents:
    def process(self, compliance: ComplianceResult):
        return ()

    def reset(self) -> None:
        pass


class EngineEventBoundary:
    """Call real EventService/EventEngine with an isolated discard store."""

    def __init__(self, *, emit: bool) -> None:
        self.engine = EventEngine()
        self.service = EventService(engine=self.engine, store=_DiscardEventStore())
        self.emit = emit
        self.confirmed_count = 0

    def process(self, compliance: ComplianceResult):
        events = self.service.process(compliance)
        self.confirmed_count += len(events)
        return events if self.emit else ()

    def reset(self) -> None:
        self.engine.reset()


class _DiscardEventStore:
    """S2–S4 diagnostic store; no JSONL side effect or retained events."""

    def append_many(self, events) -> int:
        return len(events)


class UnusedIngest:
    def ingest(self, *args, **kwargs):
        raise AssertionError("ingest is outside this diagnostic stage")


class NoSnapshot:
    """Explicit diagnostic placeholder; never claims to store an image."""

    def __init__(self) -> None:
        self.calls = 0

    def capture(self, event_id, image):
        self.calls += 1
        return SimpleNamespace(relative_path="diagnostic/no-snapshot")


class NoAlert:
    def dispatch_event(self, event):
        return ()


class CountingCachedSource(CachedFrameSource):
    def __init__(self, metadata, frames, counters) -> None:
        super().__init__(metadata, frames)
        self._counters = counters

    def open(self):
        self._counters["opens"] += 1
        return super().open()

    def close(self):
        self._counters["closes"] += 1
        return super().close()


class SourceFactory:
    def __init__(self, metadata, frames) -> None:
        self.metadata, self.frames = metadata, frames
        self.counters = {"created": 0, "opens": 0, "closes": 0}
        self.live = weakref.WeakSet()

    def __call__(self, _request):
        source = CountingCachedSource(self.metadata, self.frames, self.counters)
        self.counters["created"] += 1
        self.live.add(source)
        return source


def stage_components(stage: str, *, detection_fixture: dict | None = None,
                     track_fixture: dict | None = None, real_tracker: bool = False):
    if stage not in {"S0", "S1", "S2", "S3", "S4"}:
        raise ValueError("unknown P9-C.3d stage")
    if stage == "S0":
        return {"inference_service": EmptyInference(), "tracker": EmptyTracker(),
                "association_adapter": EmptyAssociation(),
                "compliance_service": EmptyCompliance(),
                "event_service": EmptyEvents()}
    if detection_fixture is None or track_fixture is None:
        raise ValueError("real diagnostic fixtures required for S1–S4")
    from core.association.ppe_person_association import PPEPersonAssociationAdapter
    from services.compliance_service import ComplianceService
    return {
        "inference_service": PrecomputedInferenceService(detection_fixture),
        "tracker": (ByteTrackPersonTrackingAdapter() if real_tracker
                    else PrecomputedTrackingAdapter(track_fixture)),
        "association_adapter": PPEPersonAssociationAdapter(),
        "compliance_service": ComplianceService(),
        "event_service": (EmptyEvents() if stage == "S1" else
                          EngineEventBoundary(emit=stage in {"S3", "S4"})),
    }
