"""Lossless task-owned PNG evidence; the frozen SnapshotStorage stays JPEG-only."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import cv2
from PIL import Image
from infra.storage.snapshot_storage import SnapshotStorage
from offline.image_processor import _write_synced
from offline.jobs import JobError, sha256_file


class OfflineEvidenceStore:
    def __init__(self, root: Path):
        # Reuse the existing confined path resolver, without changing JPEG contracts.
        self.paths = SnapshotStorage(root)

    def save(self, filename, bgr):
        target = self.paths.resolve_path(filename)
        if target.exists() or target.is_symlink():
            raise JobError("EVIDENCE_CONFLICT", "证据文件已存在")
        height, width = bgr.shape[:2]
        ok, encoded = cv2.imencode(".png", bgr)
        if not ok:
            raise JobError("EVIDENCE_WRITE_FAILED", "证据图像编码失败")
        payload = encoded.tobytes()
        temporary = self.paths.resolve_path(filename + ".part")
        _write_synced(temporary, payload)
        os.replace(temporary, target)
        metadata = {"filename": filename, "sha256": hashlib.sha256(payload).hexdigest(),
                    "width": width, "height": height, "size_bytes": len(payload)}
        self.verify(target, metadata)
        return metadata

    @staticmethod
    def verify(path, metadata):
        if path.is_symlink() or not path.is_file() or path.stat().st_size != metadata["size_bytes"] or sha256_file(path) != metadata["sha256"]:
            raise JobError("EVIDENCE_CORRUPT", "证据完整性校验失败", 409)
        try:
            with Image.open(path) as image:
                if image.format != "PNG" or image.size != (metadata["width"], metadata["height"]):
                    raise ValueError("dimensions")
                image.verify()
        except Exception as exc:
            raise JobError("EVIDENCE_CORRUPT", "证据图像校验失败", 409) from exc
