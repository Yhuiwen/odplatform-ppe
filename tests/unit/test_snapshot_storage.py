import hashlib
from datetime import datetime, timezone

import pytest
from PIL import Image

from infra.storage.snapshot_storage import (
    SnapshotEvidenceConflictError,
    SnapshotPathError,
    SnapshotStorage,
)


def test_snapshot_path_generation_is_utc_and_relative() -> None:
    relative_path = SnapshotStorage.build_relative_path(
        "EVT-01",
        datetime(2026, 9, 23, 23, 59, 59, tzinfo=timezone.utc),
    )

    assert relative_path == "20260923/event_EVT-01.jpg"
    assert "\\" not in relative_path
    with pytest.raises(SnapshotPathError):
        SnapshotStorage.build_relative_path(
            "../EVT-01",
            datetime(2026, 9, 23, tzinfo=timezone.utc),
        )


def test_snapshot_save_then_inspect_file(tmp_path) -> None:
    storage = SnapshotStorage(tmp_path / "evidence")
    image = Image.new("RGB", (32, 24), color=(10, 20, 30))

    stored = storage.save_evidence(
        image,
        event_id="EVT-01",
        captured_at="2026-09-23T12:34:56Z",
    )
    path = storage.resolve_path(stored.relative_path)

    assert path.is_file()
    assert stored.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert (stored.width, stored.height) == (32, 24)
    with Image.open(path) as opened:
        assert opened.format == "JPEG"
        assert opened.size == (32, 24)


def test_snapshot_duplicate_is_idempotent_and_conflict_is_rejected(tmp_path) -> None:
    storage = SnapshotStorage(tmp_path / "evidence")
    image = Image.new("RGB", (16, 16), color=(1, 2, 3))
    first = storage.save_evidence(
        image,
        event_id="EVT-01",
        captured_at="2026-09-23T12:34:56Z",
    )
    second = storage.save_evidence(
        image,
        event_id="EVT-01",
        captured_at="2026-09-23T12:34:56Z",
    )

    assert first == second
    with pytest.raises(SnapshotEvidenceConflictError):
        storage.save_evidence(
            Image.new("RGB", (16, 16), color=(9, 9, 9)),
            event_id="EVT-01",
            captured_at="2026-09-23T12:34:56Z",
        )
