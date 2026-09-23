from __future__ import annotations

import json

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult
from core.schemas.video import (
    FrameData,
    FrameInferenceResult,
    VideoInferenceResult,
    VideoMetadata,
)


def test_video_schema_creation() -> None:
    frame = FrameData(frame_id=0, timestamp=0.0, image=object())
    metadata = VideoMetadata(
        source="video:fixture.mp4",
        fps=25.0,
        width=1280,
        height=720,
        frame_count=1,
        duration_seconds=0.08,
    )
    detection = DetectionResult(
        frame_id=0,
        timestamp=0.0,
        source=metadata.source,
        detection=Detection(
            bbox=BoundingBox(10.0, 20.0, 50.0, 80.0),
            class_id=1,
            class_name="hardhat",
            confidence=0.91,
        ),
    )
    frame_result = FrameInferenceResult(
        frame_id=frame.frame_id,
        timestamp=frame.timestamp,
        detections=(detection,),
    )
    result = VideoInferenceResult(metadata=metadata, frames=(frame_result,))

    assert result.processed_frames == 1
    assert result.frames[0].detection_count == 1
    assert result.frames[0].detections[0].class_name == "hardhat"


def test_video_result_serialization() -> None:
    metadata = VideoMetadata(
        source="video:fixture.mp4",
        fps=25.0,
        width=1280,
        height=720,
        frame_count=1,
        duration_seconds=0.04,
    )
    detection = DetectionResult(
        frame_id=0,
        timestamp=0.0,
        source=metadata.source,
        detection=Detection(
            bbox=BoundingBox(10.0, 20.0, 50.0, 80.0),
            class_id=1,
            class_name="hardhat",
            confidence=0.91,
        ),
    )
    result = VideoInferenceResult(
        metadata=metadata,
        frames=(
            FrameInferenceResult(
                frame_id=0,
                timestamp=0.0,
                detections=(detection,),
            ),
        ),
    )

    payload = result.to_dict()

    assert json.loads(json.dumps(payload)) == {
        "video": {
            "source": "video:fixture.mp4",
            "fps": 25.0,
            "width": 1280,
            "height": 720,
            "frame_count": 1,
            "duration_seconds": 0.04,
        },
        "processed_frames": 1,
        "frame_results": [
            {
                "frame_id": 0,
                "timestamp": 0.0,
                "detection_count": 1,
                "detections": [
                    {
                        "frame_id": 0,
                        "timestamp": 0.0,
                        "source": "video:fixture.mp4",
                        "class_id": 1,
                        "class_name": "hardhat",
                        "confidence": 0.91,
                        "bbox": {
                            "x1": 10.0,
                            "y1": 20.0,
                            "x2": 50.0,
                            "y2": 80.0,
                        },
                    }
                ],
            }
        ],
    }
