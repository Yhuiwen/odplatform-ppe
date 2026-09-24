"""Atomic MP4 writer for the M-007 annotated demo video tool."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from core.schemas.video import VideoMetadata

__all__ = [
    "AnnotatedVideoIncompleteOutputError",
    "AnnotatedVideoFrameCountError",
    "AnnotatedVideoOutputConflictError",
    "AnnotatedVideoPublishError",
    "AnnotatedVideoStorageError",
    "AnnotatedVideoWriteError",
    "AnnotatedVideoWriter",
    "PublishedAnnotatedVideo",
    "VideoWriteVerification",
]


class AnnotatedVideoStorageError(RuntimeError):
    """Base M-007 storage failure with a stable machine-readable code."""

    code = "annotated_video_storage_error"


class AnnotatedVideoOutputConflictError(AnnotatedVideoStorageError):
    code = "annotated_video_output_exists"


class AnnotatedVideoWriteError(AnnotatedVideoStorageError):
    code = "annotated_video_write_failed"


class AnnotatedVideoFrameCountError(AnnotatedVideoStorageError):
    code = "annotated_video_frame_count_mismatch"


class AnnotatedVideoIncompleteOutputError(AnnotatedVideoStorageError):
    code = "annotated_video_incomplete_output"


class AnnotatedVideoPublishError(AnnotatedVideoStorageError):
    code = "annotated_video_publish_failed"


@dataclass(frozen=True, slots=True)
class VideoWriteVerification:
    """Integrity summary for the staged MP4 before atomic publication."""

    video_path: str
    frame_count: int
    fps: float
    width: int
    height: int
    duration_seconds: float
    sha256: str
    size_bytes: int
    codec: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_path": self.video_path,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "codec": self.codec,
        }


@dataclass(frozen=True, slots=True)
class PublishedAnnotatedVideo:
    """Final output paths after the staging directory is atomically published."""

    output_dir: str
    video_path: str
    verification: VideoWriteVerification

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_dir": self.output_dir,
            "video_path": self.video_path,
            **self.verification.to_dict(),
        }


VideoWriterFactory = Callable[
    [Path, float, tuple[int, int], str],
    Any,
]
CaptureFactory = Callable[[Path], Any]

REQUIRED_ARTIFACTS = (
    "demo.mp4",
    "run.json",
    "frames.jsonl",
    "summary.json",
    "renderer.log",
)


class _OpenCVVideoWriter:
    """Create the configured MP4 writer with the frozen codec policy."""

    def __init__(
        self,
        path: Path,
        fps: float,
        size: tuple[int, int],
        codec: str,
    ) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise AnnotatedVideoWriteError(
                "OpenCV is not installed in the frozen rendering runtime"
            ) from exc

        if len(codec) != 4:
            raise AnnotatedVideoWriteError(
                "MP4 codec must be a four-character FourCC"
            )
        self._writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*codec),
            float(fps),
            (int(size[0]), int(size[1])),
        )
        if not self._writer.isOpened():
            self._writer.release()
            raise AnnotatedVideoWriteError(
                f"Could not open MP4 writer with codec {codec}"
            )

    def write(self, image: Any) -> None:
        self._writer.write(image)

    def release(self) -> None:
        self._writer.release()


class _OpenCVFrameCapture:
    """Small sequential decoder used to verify the staged MP4 artifact."""

    def __init__(self, path: Path) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise AnnotatedVideoWriteError(
                "OpenCV is not installed in the frozen rendering runtime"
            ) from exc
        self._capture = cv2.VideoCapture(str(path))
        if not self._capture.isOpened():
            self._capture.release()
            raise AnnotatedVideoWriteError(
                f"Could not reopen staged MP4: {path.name}"
            )
        self.fps = float(self._capture.get(cv2.CAP_PROP_FPS))
        self.width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read(self) -> tuple[bool, Any]:
        return self._capture.read()

    def release(self) -> None:
        self._capture.release()


class AnnotatedVideoWriter:
    """Write one complete output directory and publish it atomically."""

    def __init__(
        self,
        output_dir: str | Path,
        metadata: VideoMetadata,
        *,
        codec: str = "mp4v",
        writer_factory: VideoWriterFactory | None = None,
        capture_factory: CaptureFactory | None = None,
    ) -> None:
        if not isinstance(metadata, VideoMetadata):
            raise TypeError("metadata must be VideoMetadata")
        if not isinstance(codec, str) or len(codec) != 4:
            raise AnnotatedVideoWriteError(
                "MP4 codec must be a four-character FourCC"
            )
        if metadata.frame_count is None or metadata.frame_count <= 0:
            raise AnnotatedVideoWriteError(
                "Source MP4 must declare a positive frame count"
            )

        self.output_dir = Path(output_dir).expanduser().resolve()
        if self.output_dir == self.output_dir.parent:
            raise AnnotatedVideoWriteError("Output directory cannot be a drive root")
        self.metadata = metadata
        self.codec = codec
        self._writer_factory = writer_factory or _OpenCVVideoWriter
        self._capture_factory = capture_factory or _OpenCVFrameCapture

        self._staging_dir: Path | None = None
        self._writer: Any | None = None
        self._writer_released = False
        self._frame_count = 0
        self._verification: VideoWriteVerification | None = None
        self._published = False

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def staging_dir(self) -> Path:
        if self._staging_dir is None:
            raise AnnotatedVideoStorageError("Writer has not been opened")
        return self._staging_dir

    def __enter__(self) -> AnnotatedVideoWriter:
        self._open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if not self._published:
            self.rollback()

    def _open(self) -> None:
        if self._staging_dir is not None:
            raise AnnotatedVideoStorageError("Writer is already open")
        if self.output_dir.exists():
            raise AnnotatedVideoOutputConflictError(
                f"Output directory already exists: {self.output_dir}"
            )

        try:
            self.output_dir.parent.mkdir(parents=True, exist_ok=True)
            self._staging_dir = Path(
                tempfile.mkdtemp(
                    prefix=f".{self.output_dir.name}.staging-",
                    dir=self.output_dir.parent,
                )
            )
            self._writer = self._writer_factory(
                self._staging_dir / "demo.mp4",
                self.metadata.fps,
                (self.metadata.width, self.metadata.height),
                self.codec,
            )
            if self._writer is None:
                raise AnnotatedVideoWriteError(
                    "Video writer factory returned no writer"
                )
        except Exception:
            self.rollback()
            raise

    def append_frame(self, image: Any) -> None:
        """Append one frame while preserving source dimensions and order."""

        if self._writer is None or self._writer_released:
            raise AnnotatedVideoStorageError("Video writer is not active")
        if image is None:
            raise AnnotatedVideoWriteError("Cannot append an empty frame")
        shape = getattr(image, "shape", None)
        if shape is None or len(shape) < 2:
            raise AnnotatedVideoWriteError(
                "Annotated frame must expose a height/width shape"
            )
        if tuple(shape[:2]) != (self.metadata.height, self.metadata.width):
            raise AnnotatedVideoWriteError(
                "Annotated frame dimensions do not match source metadata"
            )

        try:
            self._writer.write(image)
        except Exception as exc:
            raise AnnotatedVideoWriteError(
                f"Could not write annotated frame {self._frame_count}"
            ) from exc
        self._frame_count += 1

    def write_json(self, name: str, payload: Mapping[str, Any]) -> Path:
        """Atomically write one JSON metadata file inside the staging directory."""

        content = json.dumps(
            dict(payload),
            ensure_ascii=False,
            indent=2,
        ) + "\n"
        return self.write_text(name, content)

    def write_jsonl(
        self,
        name: str,
        records: Iterable[Mapping[str, Any]],
    ) -> Path:
        """Write ordered JSON records without retaining an in-memory aggregate."""

        target = self._artifact_path(name)
        temporary = target.with_name(f".{target.name}.tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                for record in records:
                    handle.write(
                        json.dumps(
                            dict(record),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                    )
                    handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        except Exception as exc:
            if temporary.exists():
                temporary.unlink()
            if isinstance(exc, AnnotatedVideoStorageError):
                raise
            raise AnnotatedVideoWriteError(
                f"Could not write metadata artifact: {name}"
            ) from exc
        return target

    def write_text(self, name: str, content: str) -> Path:
        """Atomically write one text artifact inside the staging directory."""

        if not isinstance(content, str):
            raise TypeError("content must be a string")
        target = self._artifact_path(name)
        temporary = target.with_name(f".{target.name}.tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        except Exception as exc:
            if temporary.exists():
                temporary.unlink()
            raise AnnotatedVideoWriteError(
                f"Could not write metadata artifact: {name}"
            ) from exc
        return target

    def verify_output(self, expected_frame_count: int) -> VideoWriteVerification:
        """Release the encoder and verify the staged MP4 by decoding it."""

        if isinstance(expected_frame_count, bool) or not isinstance(
            expected_frame_count, int
        ):
            raise TypeError("expected_frame_count must be an integer")
        if expected_frame_count <= 0:
            raise AnnotatedVideoFrameCountError(
                "Expected output frame count must be positive"
            )
        self._release_writer()
        if self._frame_count != expected_frame_count:
            raise AnnotatedVideoFrameCountError(
                "Written frame count mismatch: "
                f"expected {expected_frame_count}, observed {self._frame_count}"
            )

        video_path = self.staging_dir / "demo.mp4"
        if not video_path.is_file() or video_path.stat().st_size == 0:
            raise AnnotatedVideoWriteError("Staged MP4 is missing or empty")

        capture = None
        try:
            capture = self._capture_factory(video_path)
            if capture is None:
                raise AnnotatedVideoWriteError(
                    "Capture factory returned no decoder"
                )
            observed_count = 0
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame is None:
                    raise AnnotatedVideoWriteError(
                        "Staged MP4 decoder returned no frame"
                    )
                observed_count += 1

            if observed_count != expected_frame_count:
                raise AnnotatedVideoFrameCountError(
                    "Decoded output frame count mismatch: "
                    f"expected {expected_frame_count}, observed {observed_count}"
                )

            width = int(getattr(capture, "width", 0))
            height = int(getattr(capture, "height", 0))
            fps = float(getattr(capture, "fps", 0.0))
            if (width, height) != (self.metadata.width, self.metadata.height):
                raise AnnotatedVideoWriteError(
                    "Decoded output dimensions do not match source metadata"
                )
            if not math.isfinite(fps) or fps <= 0:
                raise AnnotatedVideoWriteError(
                    "Decoded output FPS metadata is invalid"
                )

            size_bytes = video_path.stat().st_size
            self._verification = VideoWriteVerification(
                video_path=video_path.name,
                frame_count=observed_count,
                fps=fps,
                width=width,
                height=height,
                duration_seconds=observed_count / fps,
                sha256=self._sha256(video_path),
                size_bytes=size_bytes,
                codec=self.codec,
            )
            return self._verification
        except AnnotatedVideoStorageError:
            raise
        except Exception as exc:
            raise AnnotatedVideoWriteError(
                "Could not verify the staged MP4 artifact"
            ) from exc
        finally:
            if capture is not None:
                try:
                    capture.release()
                except Exception:
                    pass

    def publish(self) -> PublishedAnnotatedVideo:
        """Atomically rename the complete staging directory to the final path."""

        if self._verification is None:
            raise AnnotatedVideoPublishError(
                "Output cannot be published before frame verification"
            )
        missing = [
            name
            for name in REQUIRED_ARTIFACTS
            if not (self.staging_dir / name).is_file()
        ]
        if missing:
            raise AnnotatedVideoIncompleteOutputError(
                "Output is missing required artifacts: " + ", ".join(missing)
            )
        if self.output_dir.exists():
            raise AnnotatedVideoOutputConflictError(
                f"Output directory already exists: {self.output_dir}"
            )

        staging_dir = self.staging_dir
        try:
            os.replace(staging_dir, self.output_dir)
        except Exception as exc:
            raise AnnotatedVideoPublishError(
                f"Could not publish output directory: {self.output_dir}"
            ) from exc

        self._published = True
        return PublishedAnnotatedVideo(
            output_dir=str(self.output_dir),
            video_path=str(self.output_dir / "demo.mp4"),
            verification=self._verification,
        )

    def rollback(self) -> None:
        """Release resources and remove only this writer's staging directory."""

        release_error: Exception | None = None
        try:
            self._release_writer()
        except Exception as exc:
            release_error = exc
        staging_dir = self._staging_dir
        self._staging_dir = None
        if staging_dir is None or not staging_dir.exists():
            if release_error is not None:
                raise release_error
            return
        parent = staging_dir.parent.resolve()
        if (
            parent != self.output_dir.parent
            or staging_dir.resolve() not in parent.iterdir()
        ):
            raise AnnotatedVideoStorageError(
                "Refusing to remove a staging path outside the output parent"
            )
        try:
            shutil.rmtree(staging_dir)
        except OSError as exc:
            raise AnnotatedVideoWriteError(
                f"Could not remove staging directory: {staging_dir.name}"
            ) from exc
        if release_error is not None:
            raise release_error

    def _release_writer(self) -> None:
        if self._writer is None or self._writer_released:
            return
        try:
            self._writer.release()
        except Exception as exc:
            raise AnnotatedVideoWriteError(
                "Video writer release failed"
            ) from exc
        self._writer_released = True

    def _artifact_path(self, name: str) -> Path:
        if self._staging_dir is None:
            raise AnnotatedVideoStorageError("Writer has not been opened")
        if not isinstance(name, str) or not name.strip():
            raise AnnotatedVideoWriteError("Artifact name cannot be empty")
        candidate = Path(name)
        if candidate.is_absolute() or candidate.name != name or name == "demo.mp4":
            raise AnnotatedVideoWriteError(
                "Metadata artifact must be a safe filename"
            )
        target = self._staging_dir / candidate.name
        if target.parent != self._staging_dir:
            raise AnnotatedVideoWriteError(
                "Metadata artifact must be written inside the staging directory"
            )
        return target

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
