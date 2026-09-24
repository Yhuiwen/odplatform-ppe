from pathlib import Path

import pytest

from core.detection.detector import Detector
from core.events.event_state import EventStateManager
from core.pipeline.inference_pipeline import InferencePipeline
from infra.storage.video_storage import VideoStorage
from services.dataset_service import DatasetService
from services.inference_service import InferenceService
from services.tracking_service import TrackingService
from services.train_service import TrainService


PLACEHOLDER_CALLS = [
    ("detector", lambda: Detector().detect(None, None)),
    ("event-state", lambda: EventStateManager().update(None)),
    ("pipeline", lambda: InferencePipeline().run(None)),
    ("dataset-quality-validation", lambda: DatasetService().validate()),
    ("video-service", lambda: InferenceService().infer_video(None)),
    ("stream-service", lambda: InferenceService().infer_stream(None)),
    ("tracking-service", lambda: TrackingService().track([])),
    ("video-storage", lambda: VideoStorage().save_clip([], Path("x.mp4"))),
]


@pytest.mark.parametrize(
    ("name", "call"),
    PLACEHOLDER_CALLS,
    ids=[name for name, _ in PLACEHOLDER_CALLS],
)
def test_future_business_placeholders_fail_explicitly(name: str, call) -> None:
    with pytest.raises(NotImplementedError) as exc_info:
        call()
    assert "NOT IMPLEMENTED - FUTURE PHASE" in str(exc_info.value)
