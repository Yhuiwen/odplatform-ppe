"""Atomic evidence snapshot file storage.

The storage boundary owns image encoding and filesystem integrity only. Event
identity and database metadata are handled by the service and repository
layers, so this module never allocates or rewrites a Phase 6 ``event_id``.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from core.schemas.events import format_utc_timestamp, normalize_utc_timestamp
from utils.paths import EVENTS_DIR

__all__ = [
    "EncodedSnapshot",
    "SnapshotEvidenceConflictError",
    "SnapshotFile",
    "SnapshotHashMismatchError",
    "SnapshotPathError",
    "SnapshotRenderError",
    "SnapshotStorage",
    "SnapshotStorageError",
    "SnapshotWriteError",
]

DEFAULT_SNAPSHOT_ROOT = EVENTS_DIR / "snapshots"
JPEG_MIME_TYPE = "image/jpeg"


class SnapshotStorageError(RuntimeError):
    """Base evidence-storage failure with a stable machine code."""

    code = "SNAPSHOT_STORAGE_FAILED"


class SnapshotPathError(SnapshotStorageError):
    code = "SNAPSHOT_INVALID_PATH"


class SnapshotRenderError(SnapshotStorageError):
    code = "SNAPSHOT_RENDER_FAILED"


class SnapshotWriteError(SnapshotStorageError):
    code = "SNAPSHOT_WRITE_FAILED"


class SnapshotHashMismatchError(SnapshotStorageError):
    code = "SNAPSHOT_HASH_MISMATCH"


class SnapshotEvidenceConflictError(SnapshotStorageError):
    code = "SNAPSHOT_CONFLICT"


@dataclass(frozen=True, slots=True)
class EncodedSnapshot:
    """One normalized JPEG payload ready for an atomic evidence write."""

    content: bytes
    sha256: str
    width: int
    height: int
    mime_type: str = JPEG_MIME_TYPE

    def __post_init__(self) -> None:
        if not isinstance(self.content, bytes) or not self.content:
            raise ValueError("content must be non-empty bytes")
        if not isinstance(self.sha256, str) or re.fullmatch(
            r"[0-9a-f]{64}", self.sha256
        ) is None:
            raise ValueError("sha256 must be a lowercase 64-character digest")
        if isinstance(self.width, bool) or not isinstance(self.width, int):
            raise TypeError("width must be an integer")
        if isinstance(self.height, bool) or not isinstance(self.height, int):
            raise TypeError("height must be an integer")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("snapshot dimensions must be positive")
        if self.mime_type != JPEG_MIME_TYPE:
            raise ValueError("snapshot mime_type must be image/jpeg")


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    """Verified metadata for one evidence file on disk."""

    relative_path: str
    sha256: str
    width: int
    height: int
    mime_type: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "width": self.width,
            "height": self.height,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
        }


def _normalize_event_id(event_id: str) -> str:
    if not isinstance(event_id, str) or not event_id.strip():
        raise SnapshotPathError("event_id must be a non-empty string")
    normalized = event_id.strip()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", normalized) is None:
        raise SnapshotPathError(
            "event_id contains characters that are unsafe for an evidence filename"
        )
    return normalized


def _normalize_capture_time(value: datetime | str) -> str:
    if isinstance(value, datetime):
        return format_utc_timestamp(value)
    if isinstance(value, str):
        return normalize_utc_timestamp(value)
    raise TypeError("captured_at must be a datetime or ISO 8601 string")


def _normalize_relative_path(value: str | Path) -> str:
    if isinstance(value, Path):
        if value.is_absolute():
            raise SnapshotPathError("snapshot destination must be relative")
        candidate = value.as_posix()
    elif isinstance(value, str):
        candidate = value.strip()
    else:
        raise TypeError("snapshot destination must be a string or Path")

    if not candidate or "\\" in candidate:
        raise SnapshotPathError(
            "snapshot destination must be a non-empty relative POSIX path"
        )
    path = PurePosixPath(candidate)
    if (
        path.is_absolute()
        or re.match(r"^[A-Za-z]:/", candidate) is not None
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise SnapshotPathError(
            "snapshot destination must be a safe relative POSIX path"
        )
    return path.as_posix()


class SnapshotStorage:
    """Encode and atomically persist JPEG evidence under one root."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or DEFAULT_SNAPSHOT_ROOT).expanduser().resolve()

    @staticmethod
    def build_relative_path(
        event_id: str,
        captured_at: datetime | str,
    ) -> str:
        """Return ``YYYYMMDD/event_<event-id>.jpg`` without writing a file."""

        normalized_event_id = _normalize_event_id(event_id)
        normalized_timestamp = _normalize_capture_time(captured_at)
        captured = datetime.fromisoformat(
            normalized_timestamp.replace("Z", "+00:00")
        )
        return (
            PurePosixPath(captured.strftime("%Y%m%d"))
            / f"event_{normalized_event_id}.jpg"
        ).as_posix()

    def resolve_path(self, relative_path: str | Path) -> Path:
        """Resolve a safe relative evidence path below ``self.root``."""

        normalized = _normalize_relative_path(relative_path)
        resolved = (self.root / PurePosixPath(normalized)).resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise SnapshotPathError("snapshot path escapes the evidence root")
        return resolved

    def encode(self, image: Any) -> EncodedSnapshot:
        """Normalize an image input to an in-memory JPEG payload."""

        if image is None:
            raise SnapshotRenderError("snapshot image cannot be None")

        from PIL import Image, ImageOps

        opened: Any = None
        normalized: Any = None
        try:
            if isinstance(image, Image.Image):
                opened = image.copy()
            elif isinstance(image, (str, Path)):
                source = Path(image).expanduser().resolve()
                if not source.is_file():
                    raise SnapshotRenderError(
                        f"snapshot image does not exist: {source}"
                    )
                opened = Image.open(source)
            elif isinstance(image, (bytes, bytearray, memoryview)):
                opened = Image.open(io.BytesIO(bytes(image)))
            else:
                opened = Image.fromarray(image)

            normalized = ImageOps.exif_transpose(opened).convert("RGB")
            normalized.load()
            buffer = io.BytesIO()
            normalized.save(
                buffer,
                format="JPEG",
                quality=95,
                optimize=False,
            )
            content = buffer.getvalue()
            if not content:
                raise SnapshotRenderError("JPEG encoder returned an empty payload")
            return EncodedSnapshot(
                content=content,
                sha256=hashlib.sha256(content).hexdigest(),
                width=int(normalized.width),
                height=int(normalized.height),
            )
        except SnapshotStorageError:
            raise
        except Exception as exc:
            raise SnapshotRenderError("could not encode snapshot as JPEG") from exc
        finally:
            if normalized is not None:
                normalized.close()
            if opened is not None and opened is not normalized:
                opened.close()

    def save_encoded(
        self,
        encoded: EncodedSnapshot,
        relative_path: str | Path,
    ) -> SnapshotFile:
        """Atomically write one encoded snapshot without overwriting conflict data."""

        if not isinstance(encoded, EncodedSnapshot):
            raise TypeError("encoded must be an EncodedSnapshot")
        normalized = _normalize_relative_path(relative_path)
        target = self.resolve_path(normalized)

        if target.exists():
            existing = self.inspect(normalized)
            if existing.sha256 == encoded.sha256:
                return existing
            raise SnapshotEvidenceConflictError(
                f"snapshot path already contains different evidence: {normalized}"
            )

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.",
                suffix=".tmp",
                dir=target.parent,
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(encoded.content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                if temporary.exists():
                    temporary.unlink()
        except SnapshotStorageError:
            raise
        except OSError as exc:
            raise SnapshotWriteError(
                f"could not write snapshot evidence: {normalized}"
            ) from exc

        return self.verify(
            normalized,
            expected_sha256=encoded.sha256,
            expected_width=encoded.width,
            expected_height=encoded.height,
        )

    def save_evidence(
        self,
        image: Any,
        *,
        event_id: str,
        captured_at: datetime | str,
    ) -> SnapshotFile:
        """Encode and persist one image using the frozen evidence path policy."""

        relative_path = self.build_relative_path(event_id, captured_at)
        return self.save_encoded(self.encode(image), relative_path)

    def save(self, image: Any, destination: str | Path) -> Path:
        """Compatibility boundary returning the absolute file path."""

        encoded = self.encode(image)
        relative_path = self._relative_destination(destination)
        stored = self.save_encoded(encoded, relative_path)
        return self.resolve_path(stored.relative_path)

    def verify(
        self,
        relative_path: str | Path,
        *,
        expected_sha256: str,
        expected_width: int,
        expected_height: int,
    ) -> SnapshotFile:
        """Verify file hash and dimensions against persisted metadata."""

        inspected = self.inspect(relative_path)
        if inspected.sha256 != expected_sha256.lower():
            raise SnapshotHashMismatchError(
                f"snapshot SHA256 mismatch: {inspected.relative_path}"
            )
        if (
            inspected.width != expected_width
            or inspected.height != expected_height
        ):
            raise SnapshotHashMismatchError(
                f"snapshot dimensions mismatch: {inspected.relative_path}"
            )
        return inspected

    def inspect(self, relative_path: str | Path) -> SnapshotFile:
        """Read and hash one existing evidence file."""

        normalized = _normalize_relative_path(relative_path)
        target = self.resolve_path(normalized)
        if not target.is_file():
            raise SnapshotWriteError(
                f"snapshot evidence does not exist: {normalized}"
            )

        try:
            content = target.read_bytes()
            from PIL import Image

            with Image.open(io.BytesIO(content)) as image:
                image.load()
                if (image.format or "").upper() != "JPEG":
                    raise SnapshotRenderError(
                        f"snapshot is not JPEG evidence: {normalized}"
                    )
                width, height = image.size
        except SnapshotStorageError:
            raise
        except OSError as exc:
            raise SnapshotWriteError(
                f"could not read snapshot evidence: {normalized}"
            ) from exc
        except Exception as exc:
            raise SnapshotRenderError(
                f"could not inspect snapshot evidence: {normalized}"
            ) from exc

        return SnapshotFile(
            relative_path=normalized,
            sha256=hashlib.sha256(content).hexdigest(),
            width=int(width),
            height=int(height),
            mime_type=JPEG_MIME_TYPE,
            size_bytes=len(content),
        )

    def _relative_destination(self, destination: str | Path) -> str:
        if isinstance(destination, Path) and destination.is_absolute():
            resolved = destination.expanduser().resolve()
            if resolved != self.root and self.root not in resolved.parents:
                raise SnapshotPathError(
                    "absolute snapshot destination must be inside the evidence root"
                )
            return resolved.relative_to(self.root).as_posix()
        return _normalize_relative_path(destination)
