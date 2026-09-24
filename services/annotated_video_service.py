"""M-007 composition service for annotated local MP4 rendering."""

from __future__ import annotations

import hashlib
import importlib
import platform
import sys
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping

from core.inference.detector import (
    CheckpointIntegrityError,
    InferenceError,
    InferenceExecutionDisabledError,
)
from core.rendering.annotated_frame import AnnotatedFrameRenderer
from core.schemas.video import FrameData, FrameInferenceResult
from core.video.reader import VideoReader
from infra.storage.annotated_video_writer import (
    AnnotatedVideoFrameCountError,
    AnnotatedVideoWriter,
    VideoWriteVerification,
)
from services.inference_service import InferenceService
from utils.config_loader import load_yaml
from utils.paths import PROJECT_ROOT, config_path as resolve_default_config_path

__all__ = [
    "AnnotatedVideoConfigurationError",
    "AnnotatedVideoInputError",
    "AnnotatedVideoRunResult",
    "AnnotatedVideoService",
    "AnnotatedVideoServiceError",
    "AnnotatedVideoSourceChangedError",
]


class AnnotatedVideoServiceError(RuntimeError):
    """Base M-007 application error with a stable machine-readable code."""

    code = "m007_annotated_video_failed"


class AnnotatedVideoConfigurationError(AnnotatedVideoServiceError):
    code = "invalid_m007_configuration"


class AnnotatedVideoInputError(AnnotatedVideoServiceError):
    code = "invalid_m007_input"


class AnnotatedVideoSourceChangedError(AnnotatedVideoServiceError):
    code = "annotated_video_source_changed"


@dataclass(frozen=True, slots=True)
class AnnotatedVideoRunResult:
    """Successful M-007 run summary returned to the CLI."""

    run_id: str
    output_dir: str
    output_video: str
    processed_frames: int
    source_frames: int
    written_frames: int
    elapsed_seconds: float
    detection_count: int
    class_counts: Mapping[str, int]
    output_sha256: str
    output_size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "run_id": self.run_id,
            "output_video": self.output_video,
            "processed_frames": self.processed_frames,
            "source_frames": self.source_frames,
            "written_frames": self.written_frames,
            "elapsed_seconds": self.elapsed_seconds,
            "detection_count": self.detection_count,
            "class_counts": dict(self.class_counts),
            "output_sha256": self.output_sha256,
            "output_size_bytes": self.output_size_bytes,
            "output_dir": self.output_dir,
            "error": None,
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise AnnotatedVideoConfigurationError(
            "Clock must return a timezone-aware datetime"
        )
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_config_path(value: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    if candidate.is_absolute() or candidate.parent != Path("."):
        return candidate.resolve()
    return resolve_default_config_path(candidate.name).resolve()


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _runtime_version(package: str, module_name: str | None = None) -> str | None:
    if module_name is not None:
        try:
            module = importlib.import_module(module_name)
            observed = getattr(module, "__version__", None)
            if observed:
                return str(observed)
        except ImportError:
            pass
    return _package_version(package)


class AnnotatedVideoService:
    """Compose the frozen reader and inference boundary into one demo MP4."""

    implementation_version = "m007-annotated-demo-v1"
    output_schema_version = "m007-annotated-output-v1"

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        execution_enabled: bool | None = None,
        inference_service: InferenceService | Any | None = None,
        reader_factory: type[VideoReader] = VideoReader,
        writer_factory: Callable[..., AnnotatedVideoWriter] = AnnotatedVideoWriter,
        renderer_factory: Callable[..., AnnotatedFrameRenderer] = (
            AnnotatedFrameRenderer
        ),
        clock: Callable[[], datetime] = _utc_now,
        run_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.config_path = _resolve_config_path(
            config_path or "configs/inference.yaml"
        )
        self.config = load_yaml(self.config_path)
        self.inference = self._required_mapping(self.config, "inference")
        self.runtime = self._required_mapping(self.inference, "runtime")
        self.model = self._required_mapping(self.inference, "model")
        self.device = self._required_mapping(self.inference, "device")
        self.preprocessing = self._required_mapping(
            self.inference,
            "preprocessing",
        )
        self.detection = self._required_mapping(self.inference, "detection")

        self.class_filter = tuple(
            int(item) for item in self.detection.get("class_filter", ())
        )
        self.class_names = tuple(
            str(item) for item in self.detection.get("class_names", ())
        )
        self._validate_contract()

        self.inference_service = inference_service or InferenceService(
            config_path=self.config_path,
            execution_enabled=execution_enabled,
        )
        self.reader_factory = reader_factory
        self.writer_factory = writer_factory
        self.renderer_factory = renderer_factory
        self.clock = clock
        self.run_id_factory = run_id_factory or self._default_run_id

    def render_video(
        self,
        source: str | Path,
        *,
        output_dir: str | Path | None = None,
    ) -> AnnotatedVideoRunResult:
        """Render one local MP4 without skipping or reordering source frames."""

        source_path = VideoReader.validate_source(source)
        if not bool(getattr(self.inference_service, "execution_enabled", False)):
            raise InferenceExecutionDisabledError(
                "Annotated video execution is disabled; an explicit "
                "validation authorization is required"
            )

        checkpoint_path = self._checkpoint_path()
        checkpoint_sha256 = self._verify_checkpoint(checkpoint_path)
        config_sha256 = _sha256(self.config_path)
        source_sha256 = _sha256(source_path)
        run_id = str(self.run_id_factory()).strip()
        if not run_id:
            raise AnnotatedVideoConfigurationError("Run ID cannot be empty")
        created_at = _format_utc(self.clock())
        final_output_dir = (
            Path(output_dir).expanduser().resolve()
            if output_dir is not None
            else (
                PROJECT_ROOT
                / "artifacts"
                / "inference"
                / "annotated"
                / run_id
            ).resolve()
        )

        started = perf_counter()
        class_counts: Counter[str] = Counter()
        frame_records: list[dict[str, Any]] = []
        total_detections = 0
        source_frames: int | None = None
        processed_frames = 0

        reader = self.reader_factory(source_path)
        with reader as opened_reader:
            metadata = opened_reader.open()
            if metadata.frame_count is None or metadata.frame_count <= 0:
                raise AnnotatedVideoInputError(
                    "Source MP4 must declare a positive frame count"
                )
            source_frames = metadata.frame_count
            renderer = self.renderer_factory(self.class_names)
            writer = self.writer_factory(final_output_dir, metadata)

            with writer:
                for frame in opened_reader:
                    detections = self.inference_service.infer_frame(
                        frame,
                        source=metadata.source,
                    )
                    self._validate_detection_context(
                        frame=frame,
                        source=metadata.source,
                        detections=detections,
                    )
                    annotated_frame = renderer.render(frame, detections)
                    writer.append_frame(annotated_frame)

                    frame_result = FrameInferenceResult(
                        frame_id=frame.frame_id,
                        timestamp=frame.timestamp,
                        detections=tuple(detections),
                    )
                    frame_records.append(frame_result.to_dict())
                    total_detections += frame_result.detection_count
                    class_counts.update(
                        detection.class_name for detection in detections
                    )
                    processed_frames += 1

                if processed_frames != source_frames:
                    raise AnnotatedVideoFrameCountError(
                        "Processed frame count mismatch: "
                        f"expected {source_frames}, observed {processed_frames}"
                    )
                if writer.frame_count != source_frames:
                    raise AnnotatedVideoFrameCountError(
                        "Written frame count mismatch before verification: "
                        f"expected {source_frames}, observed {writer.frame_count}"
                    )
                verification = writer.verify_output(source_frames)

                if _sha256(source_path) != source_sha256:
                    raise AnnotatedVideoSourceChangedError(
                        "Source MP4 changed during processing"
                    )
                if _sha256(checkpoint_path) != checkpoint_sha256:
                    raise CheckpointIntegrityError(
                        "Frozen checkpoint changed during processing"
                    )

                elapsed_seconds = perf_counter() - started
                ordered_class_counts = {
                    class_name: int(class_counts[class_name])
                    for class_name in self.class_names
                }
                runtime = self._runtime_fingerprint()
                run_payload = {
                    "schema_version": self.output_schema_version,
                    "implementation_version": self.implementation_version,
                    "run_id": run_id,
                    "created_at": created_at,
                    "source": {
                        "path": _display_path(source_path),
                        "sha256": source_sha256,
                        "metadata": metadata.to_dict(),
                    },
                    "inference_config": {
                        "path": _display_path(self.config_path),
                        "sha256": config_sha256,
                    },
                    "checkpoint": {
                        "path": _display_path(checkpoint_path),
                        "sha256": checkpoint_sha256,
                        "size_bytes": checkpoint_path.stat().st_size,
                    },
                    "runtime": runtime,
                    "class_order": list(self.class_names),
                    "class_filter": list(self.class_filter),
                    "thresholds": {
                        "confidence": float(
                            self.detection.get("conf_threshold")
                        ),
                        "iou": float(self.detection.get("iou_threshold")),
                        "imgsz": int(self.preprocessing.get("imgsz")),
                        "batch": int(self.preprocessing.get("batch")),
                        "device": str(self.device.get("device")),
                        "device_policy": str(self.device.get("policy")),
                    },
                    "output": {
                        "directory": _display_path(final_output_dir),
                        "video": "demo.mp4",
                        "codec": verification.codec,
                    },
                }
                summary_payload = {
                    "schema_version": self.output_schema_version,
                    "run_id": run_id,
                    "status": "success",
                    "source_frame_count": source_frames,
                    "processed_frame_count": processed_frames,
                    "written_frame_count": writer.frame_count,
                    "verified_output_frame_count": verification.frame_count,
                    "elapsed_seconds": elapsed_seconds,
                    "processing_fps": (
                        processed_frames / elapsed_seconds
                        if elapsed_seconds > 0
                        else None
                    ),
                    "total_detections": total_detections,
                    "frames_with_detections": sum(
                        1 for record in frame_records if record["detection_count"]
                    ),
                    "class_counts": ordered_class_counts,
                    "renderer_errors": [],
                    "writer_errors": [],
                    "output": verification.to_dict(),
                    "output_sha256": verification.sha256,
                    "output_dimensions": {
                        "width": verification.width,
                        "height": verification.height,
                    },
                }
                log_content = (
                    f"{created_at} run_started run_id={run_id}\n"
                    f"{_format_utc(self.clock())} frames_processed="
                    f"{processed_frames} output_frames={verification.frame_count}\n"
                    f"{_format_utc(self.clock())} run_completed status=success\n"
                )

                writer.write_json("run.json", run_payload)
                writer.write_jsonl("frames.jsonl", frame_records)
                writer.write_json("summary.json", summary_payload)
                writer.write_text("renderer.log", log_content)
                published = writer.publish()

        return AnnotatedVideoRunResult(
            run_id=run_id,
            output_dir=published.output_dir,
            output_video=published.video_path,
            processed_frames=processed_frames,
            source_frames=int(source_frames),
            written_frames=verification.frame_count,
            elapsed_seconds=elapsed_seconds,
            detection_count=total_detections,
            class_counts=ordered_class_counts,
            output_sha256=verification.sha256,
            output_size_bytes=verification.size_bytes,
        )

    def _required_mapping(
        self,
        parent: Mapping[str, Any],
        key: str,
    ) -> dict[str, Any]:
        value = parent.get(key)
        if not isinstance(value, dict):
            raise AnnotatedVideoConfigurationError(
                f"Configuration requires a '{key}' mapping"
            )
        return value

    def _validate_contract(self) -> None:
        if self.class_filter != tuple(range(len(self.class_filter))):
            raise AnnotatedVideoConfigurationError(
                "M-007 requires a contiguous frozen class filter"
            )
        if not self.class_names or len(self.class_names) != len(self.class_filter):
            raise AnnotatedVideoConfigurationError(
                "Frozen class names must match the class filter"
            )
        if bool(self.model.get("auto_download", True)):
            raise AnnotatedVideoConfigurationError(
                "M-007 cannot download model weights"
            )
        if (
            str(self.device.get("policy")) != "cpu_only"
            or str(self.device.get("device")) != "cpu"
            or bool(self.device.get("auto", True))
            or bool(self.device.get("cuda_authorized", True))
        ):
            raise AnnotatedVideoConfigurationError(
                "M-007 requires the frozen CPU-only device policy"
            )
        if int(self.preprocessing.get("imgsz", 0)) <= 0:
            raise AnnotatedVideoConfigurationError("imgsz must be positive")
        if int(self.preprocessing.get("batch", 0)) != 1:
            raise AnnotatedVideoConfigurationError(
                "M-007 requires frozen batch size 1"
            )
        confidence = float(self.detection.get("conf_threshold", -1))
        iou = float(self.detection.get("iou_threshold", -1))
        if not 0 <= confidence <= 1 or not 0 <= iou <= 1:
            raise AnnotatedVideoConfigurationError(
                "Detection thresholds must be in [0, 1]"
            )

    def _checkpoint_path(self) -> Path:
        raw_path = str(self.model.get("path", "")).strip()
        if not raw_path:
            raise AnnotatedVideoConfigurationError(
                "Frozen checkpoint path is required"
            )
        return _project_path(raw_path).resolve()

    def _verify_checkpoint(self, checkpoint_path: Path) -> str:
        if not checkpoint_path.is_file():
            raise CheckpointIntegrityError(
                f"Frozen checkpoint does not exist: {checkpoint_path}"
            )
        expected_sha256 = str(self.model.get("sha256", "")).lower()
        expected_size = int(self.model.get("size_bytes", -1))
        observed_size = checkpoint_path.stat().st_size
        if observed_size != expected_size:
            raise CheckpointIntegrityError(
                "Checkpoint size mismatch: "
                f"expected {expected_size}, observed {observed_size}"
            )
        observed_sha256 = _sha256(checkpoint_path)
        if observed_sha256 != expected_sha256:
            raise CheckpointIntegrityError(
                "Checkpoint SHA256 mismatch: "
                f"expected {expected_sha256}, observed {observed_sha256}"
            )
        return observed_sha256

    def _runtime_fingerprint(self) -> dict[str, Any]:
        return {
            "id": str(self.runtime.get("id", "")),
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "torch": _runtime_version("torch", "torch"),
            "torchvision": _runtime_version("torchvision", "torchvision"),
            "ultralytics": _runtime_version("ultralytics", "ultralytics"),
            "numpy": _runtime_version("numpy", "numpy"),
            "opencv_python": _runtime_version("opencv-python", "cv2"),
            "expected": {
                "python": str(self.runtime.get("python", "")),
                "torch": str(self.runtime.get("torch", "")),
                "ultralytics": str(self.runtime.get("ultralytics", "")),
            },
        }

    @staticmethod
    def _validate_detection_context(
        *,
        frame: FrameData,
        source: str,
        detections: Any,
    ) -> None:
        for detection in detections:
            if (
                detection.frame_id != frame.frame_id
                or detection.timestamp != frame.timestamp
                or detection.source != source
            ):
                raise InferenceError(
                    "Detector returned a detection for the wrong video frame"
                )

    @staticmethod
    def _default_run_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{timestamp}-{uuid.uuid4().hex[:8]}"
