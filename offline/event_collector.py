"""Per-job orchestration of the existing tracking, association and event engines."""
from __future__ import annotations

import csv
import json
import hashlib
from contextlib import contextmanager
from uuid import uuid4

from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.events.event_engine import EventEngine
from infra.database.database import Database
from infra.database.repository import EventRepository
from offline.evidence_store import OfflineEvidenceStore
from offline.jobs import JobError, sha256_file
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService


class JobEventDatabase(Database):
    """One job-owned connection for repository calls, never a realtime default."""
    def __init__(self, path):
        super().__init__(path)
        self.connection_handle = super().connect()
        try:
            self.connection_handle.execute("""CREATE TABLE offline_evidence (
                event_id TEXT PRIMARY KEY REFERENCES events(event_id),
                evidence_id TEXT UNIQUE NOT NULL, job_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL)""")
        except Exception:
            self.close()
            raise

    @contextmanager
    def connection(self):
        yield self.connection_handle

    @contextmanager
    def transaction(self, *, immediate=True):
        db = self.connection_handle
        db.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        try:
            yield db
            db.execute("COMMIT")
        except Exception:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise

    def close(self):
        if self.connection_handle is not None:
            try:
                self.connection_handle.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self.connection_handle.execute("PRAGMA journal_mode=DELETE")
            finally:
                self.connection_handle.close()
                self.connection_handle = None


def csv_safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")) else text


class DigestWriter:
    """Hash exactly the streamed UTF-8 export, including CSV's BOM."""
    def __init__(self, handle, *, bom=False):
        self.handle = handle
        self.digest = hashlib.sha256(b"\xef\xbb\xbf" if bom else b"")

    def write(self, text):
        self.digest.update(text.encode("utf-8"))
        return self.handle.write(text)


class OfflineEventCollector:
    def __init__(self, context, *, tracker=None, association=None, compliance=None, engine=None):
        self.context, self.job_id = context, context.job["job_id"]
        self.source = f"offline:video:{self.job_id}"
        self.tracker = tracker if tracker is not None else ByteTrackPersonTrackingAdapter()
        self.association = association if association is not None else PPEPersonAssociationAdapter()
        self.compliance = compliance if compliance is not None else ComplianceService()
        # EventEngine directly: EventService's default JSON store is realtime-owned.
        self.engine = engine if engine is not None else EventEngine()
        self.database = JobEventDatabase(context.storage.path(self.job_id, "staging", "events.sqlite3"))
        self.repository = EventRepository(self.database)
        self.ingest = EventIngestService(self.repository)
        self.evidence = OfflineEvidenceStore(context.storage.path(self.job_id, "staging", "events.sqlite3").parent)
        self.track_ids = set()
        self.observations = self.unknown = self.active = self.frames = 0
        self.evidence_bytes = 0
        self.last_timestamp = -1.0
        self.files = {}  # Artifact names only; never retain images/detections.

    def __call__(self, frame, detections, annotated):
        if self.context.cancelled():
            raise JobError("JOB_CANCELLED", "事件分析已取消")
        if frame.frame_id != self.frames or frame.timestamp <= self.last_timestamp or any(
            d.frame_id != frame.frame_id or d.timestamp != frame.timestamp or d.source != self.source for d in detections
        ):
            raise JobError("INVALID_EVENT_CONTEXT", "事件分析帧上下文不一致")
        if annotated.shape != frame.image.shape:
            raise JobError("EVIDENCE_DIMENSIONS", "证据尺寸与视频不一致")
        people = tuple(d for d in detections if d.class_id == 0 and d.class_name == "person")
        ppe = tuple(d for d in detections if d.class_id in {1, 2, 3, 4})
        tracks = self.tracker.update(people, frame_id=frame.frame_id, timestamp=frame.timestamp, source=self.source)
        result = self.association.associate(tracks, ppe, frame_id=frame.frame_id, timestamp=frame.timestamp, source=self.source)
        events = self.engine.process(self.compliance.evaluate(result))
        self.observations += len(tracks)
        self.track_ids.update(t.track_id for t in tracks)
        self.active = len(tracks)  # Current returned observations, not lost backend tracks.
        self.unknown += result.unknown_count
        for event in events:
            track = next((t for t in tracks if t.track_id == event.track_id), None)
            if track is None or event.timestamp != frame.timestamp:
                raise JobError("INVALID_EVENT_CONTEXT", "确认事件与触发帧不一致")
            bbox = dict(zip(("x1", "y1", "x2", "y2"), track.bbox.as_tuple()))
            if self.repository.get(event.event_id) is not None:
                raise JobError("EVENT_DUPLICATE", "离线事件编号重复")
            self.ingest.ingest(event, source=self.source, frame_id=frame.frame_id, bbox=bbox)
            evidence_id = "EVD-" + uuid4().hex
            row = {"job_id": self.job_id, "event_id": event.event_id, "event_type": event.event_type.value,
                   "track_id": event.track_id, "frame_id": frame.frame_id,
                   "video_timestamp_seconds": frame.timestamp, "confidence": event.confidence,
                   "evidence_id": evidence_id, "bbox": bbox, "integrity_status": "VERIFIED"}
            for variant, pixels in (("original", frame.image), ("annotated", annotated)):
                filename = f"{variant}_{event.event_id}.png"
                metadata = self.evidence.save(filename, pixels)
                self.evidence_bytes += metadata["size_bytes"]
                metadata["artifact_key"] = f"{variant}_{evidence_id[4:]}"
                metadata["zip_path"] = f"evidence/{variant}/{event.event_id}.png"
                row[variant] = metadata
                self.files[filename] = (metadata["artifact_key"], metadata["zip_path"])
            with self.database.transaction() as db:
                db.execute("INSERT INTO offline_evidence VALUES (?,?,?,?)", (event.event_id, evidence_id, self.job_id, json.dumps(row, allow_nan=False)))
        self.frames += 1
        self.last_timestamp = frame.timestamp

    def rows(self):
        db = self.database.connection_handle
        for record in db.execute("""SELECT o.metadata_json,e.created_at,e.frame_id,e.source_timestamp,
            e.track_id,e.event_type,e.confidence,e.source,e.bbox_json FROM offline_evidence o
            JOIN events e ON e.event_id=o.event_id ORDER BY e.frame_id,e.event_id"""):
            row = json.loads(record[0])
            row["created_at"] = record[1]
            if (row["job_id"] != self.job_id or row["frame_id"] != record[2] or row["video_timestamp_seconds"] != record[3]
                or row["track_id"] != record[4] or row["event_type"] != record[5] or row["confidence"] != record[6]
                or record[7] != self.source or row["bbox"] != json.loads(record[8])):
                raise JobError("EVENT_EVIDENCE_MISMATCH", "事件与证据元数据不一致")
            yield row

    def finalize(self):
        db = self.database.connection_handle
        total = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        if total != db.execute("SELECT COUNT(*) FROM offline_evidence").fetchone()[0]:
            raise JobError("EVENT_EVIDENCE_MISMATCH", "事件和证据数量不一致")
        counts = {key: count for key, count in db.execute("SELECT event_type,COUNT(*) FROM events GROUP BY event_type")}
        stage = self.context.storage.path(self.job_id, "staging", "events.json").parent
        # Stream exports; do not accumulate the entire event/evidence collection.
        fields = ("job_id", "event_id", "event_type", "track_id", "confidence", "frame_id", "video_timestamp_seconds", "created_at", "evidence_id", "source", "original_sha256", "annotated_sha256", "width", "height", "bbox")
        with (stage / "events.json").open("x", encoding="utf-8", newline="") as event_file, (stage / "evidence_index.json").open("x", encoding="utf-8", newline="") as index_file, (stage / "events.csv").open("x", encoding="utf-8-sig", newline="") as csv_file:
            events, index, csv_stream = DigestWriter(event_file), DigestWriter(index_file), DigestWriter(csv_file, bom=True)
            writer = csv.writer(csv_stream)
            writer.writerow(fields)
            events.write('{"schema_version":"offline-events-v1","job_id":' + json.dumps(self.job_id) + ',"items":[')
            index.write('{"schema_version":"offline-evidence-v1","job_id":' + json.dumps(self.job_id) + ',"items":[')
            for position, row in enumerate(self.rows()):
                if self.context.cancelled():
                    raise JobError("JOB_CANCELLED", "事件导出已取消")
                for variant in ("original", "annotated"):
                    OfflineEvidenceStore.verify(stage / row[variant]["filename"], row[variant])
                row["source"] = self.source
                payload = json.dumps(row, ensure_ascii=False, allow_nan=False)
                events.write(("," if position else "") + payload)
                index.write(("," if position else "") + payload)
                csv_row = row | {"original_sha256": row["original"]["sha256"], "annotated_sha256": row["annotated"]["sha256"],
                                 "width": row["original"]["width"], "height": row["original"]["height"],
                                 "bbox": json.dumps(row["bbox"], separators=(",", ":"))}
                writer.writerow([csv_safe(csv_row[key]) for key in fields])
            for handle in (events, index):
                handle.write("]}")
            import os
            for handle in (event_file, index_file, csv_file):
                handle.flush()
                os.fsync(handle.fileno())
        for filename, stream in (("events.json", events), ("evidence_index.json", index), ("events.csv", csv_stream)):
            if sha256_file(stage / filename) != stream.digest.hexdigest():
                raise JobError("EVENT_EXPORT_CORRUPT", "事件导出写入完整性校验失败")
        self.files.update({"events.json": ("events", "events.json"), "events.csv": ("events_csv", "events.csv"),
                           "evidence_index.json": ("evidence_index", "evidence/index.json"),
                           "events.sqlite3": ("events_db", None)})
        self.database.close()
        if any((stage / ("events.sqlite3" + suffix)).exists() for suffix in ("-wal", "-shm")):
            raise JobError("DATABASE_NOT_CLOSED", "事件数据库尚未关闭")
        return {"event_analysis_status": "COMPLETED", "confirmed_events": total, "events_by_type": counts,
                "track_observations": self.observations, "unique_track_ids": len(self.track_ids),
                "active_tracks": self.active, "active_tracks_scope": "current_frame_returned_observations",
                "unknown_associations": self.unknown, "evidence_events": total, "evidence_count": total,
                "evidence_image_files": total * 2, "event_analysis_frames": self.frames}

    def close(self):
        try:
            self.database.close()
        finally:
            try:
                self.tracker.reset()
            finally:
                self.engine.reset()
                self.track_ids.clear()
