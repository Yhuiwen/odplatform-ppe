"""Frozen engines with legal synthetic detections; no changed temporal settings."""
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest
pytest.importorskip("fastapi")
from api.main import app  # Loads the verified business dependency environment.
import numpy as np

from core.detection.schemas import BoundingBox, Detection
from core.schemas.detection import DetectionResult
from core.schemas.video import FrameData
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter, ByteTrackMatch
from core.rendering.annotated_frame import AnnotatedFrameRenderer
from offline.event_collector import OfflineEventCollector, csv_safe
from offline.jobs import JobStorage, JobRepository, ArtifactPublisher, JobError, sha256_file
from offline.worker import JobContext, SingleWorker, ResourceAdmission
from tests.unit.test_offline_video_processor import system, assert_failed


class DeterministicBackend:
    def __init__(self):
        self.calls = 0
        self.resets = 0
    def update(self, detections):
        self.calls += 1
        return tuple(ByteTrackMatch(i, i + 1) for i in range(len(detections)))
    def reset(self):
        self.resets += 1


@pytest.fixture
def setup(tmp_path):
    storage = JobStorage(tmp_path / "jobs")
    repo = JobRepository(storage.root / "jobs.sqlite3")
    def make(job_id="a"*32):
        storage.create(job_id)
        storage.path(job_id,"input","source.mp4").write_bytes(b"synthetic-unit-only")
        repo.create(job_id,"video","unit.mp4",True)
        repo.transition(job_id,"QUEUED")
        context = JobContext(repo.get(job_id),storage,ArtifactPublisher(storage),lambda *a:None,lambda:False)
        backend = DeterministicBackend()
        tracker = ByteTrackPersonTrackingAdapter(backend=backend)
        return OfflineEventCollector(context,tracker=tracker), backend
    return SimpleNamespace(storage=storage,repo=repo,make=make)


def frame(collector, index, *, timestamp=None, people=1, state="violation"):
    source = collector.source
    timestamp = index * .3 if timestamp is None else timestamp
    image = np.zeros((200,260,3),dtype=np.uint8)
    image[:,:,0] = index % 255
    f = FrameData(index,timestamp,image)
    detections = []
    for person in range(people):
        x = person * 130
        items = [(0,"person",(x+10,10,x+110,190))]
        if state != "unknown":
            items += [(2 if state == "violation" else 1,"no_hardhat" if state == "violation" else "hardhat",(x+20,15,x+80,65)),
                      (4 if state == "violation" else 3,"no_vest" if state == "violation" else "vest",(x+20,80,x+90,160))]
        for cid,name,box in items:
            detections.append(DetectionResult(index,timestamp,source,Detection(BoundingBox(*box),cid,name,.95)))
    untouched = f.image.copy()
    annotated = AnnotatedFrameRenderer(("person","hardhat","no_hardhat","vest","no_vest")).render(f,detections)
    assert np.array_equal(untouched,f.image)
    collector(f,tuple(detections),annotated)
    return f,detections,annotated


def test_persistent_violation_two_types_two_tracks_and_evidence(setup):
    collector, backend = setup.make()
    try:
        for i in range(12):
            frame(collector,i,people=2)
        summary = collector.finalize()
        assert summary["confirmed_events"] == 4
        assert summary["events_by_type"] == {"NO_HELMET":2,"NO_VEST":2}
        assert summary["track_observations"] == 24 and summary["unique_track_ids"] == 2
        assert summary["evidence_events"] == 4 and summary["evidence_image_files"] == 8
        rows = json.loads(setup.storage.path(collector.job_id,"staging","events.json").read_text())["items"]
        assert all(r["frame_id"] == 4 and r["video_timestamp_seconds"] == 1.2 for r in rows)
        assert backend.calls == 12
    finally:
        collector.close()
    assert backend.resets == 1


def test_recovery_cooldown_then_new_cycle(setup):
    collector,_ = setup.make()
    try:
        for i in range(5): frame(collector,i)
        for i in range(5,10): frame(collector,i,state="compliant")
        for i in range(10,15): frame(collector,i)
        assert collector.database.connection_handle.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2
        for i in range(15,20): frame(collector,i,timestamp=40.+(i-15)*.3,state="compliant")
        for i in range(20,25): frame(collector,i,timestamp=42.+(i-20)*.3)
        assert collector.finalize()["confirmed_events"] == 4
    finally: collector.close()


def test_unknown_empty_frames_and_track_loss(setup):
    collector,backend = setup.make()
    try:
        for i in range(5): frame(collector,i,state="unknown")
        for i in range(5,12): frame(collector,i,people=0)
        summary = collector.finalize()
        assert summary["events_by_type"] == {"PPE_UNKNOWN":1}
        assert summary["active_tracks"] == 0 and backend.calls == 12
        assert summary["unknown_associations"] == 0  # Missing PPE is not an ambiguous association.
    finally: collector.close()


def test_two_jobs_repeated_track_id_isolated(setup):
    results=[]
    for job_id in ("a"*32,"b"*32):
        collector,_=setup.make(job_id)
        try:
            for i in range(5): frame(collector,i)
            assert collector.finalize()["confirmed_events"]==2
            results.append(json.loads(setup.storage.path(job_id,"staging","events.json").read_text())["items"])
        finally: collector.close()
    assert {r["event_id"] for r in results[0]}.isdisjoint(r["event_id"] for r in results[1])
    assert {r["evidence_id"] for r in results[0]}.isdisjoint(r["evidence_id"] for r in results[1])
    assert all(r["track_id"]==1 for rows in results for r in rows)


@pytest.mark.parametrize("mode",["sha","missing","png","relation"])
def test_corrupt_evidence_is_not_finalized(setup,mode):
    collector,_=setup.make()
    try:
        for i in range(5): frame(collector,i)
        row=next(collector.rows())
        path=setup.storage.path(collector.job_id,"staging",row["original"]["filename"])
        if mode=="missing": path.unlink()
        elif mode=="relation":
            row["frame_id"]+=1
            collector.database.connection_handle.execute("UPDATE offline_evidence SET metadata_json=? WHERE event_id=?",(json.dumps(row),row["event_id"]))
        else: path.write_bytes(b"invalid")
        with pytest.raises(JobError): collector.finalize()
    finally: collector.close()


@pytest.mark.parametrize("failure",["cancel","write","sqlite","duplicate","observer"])
def test_failure_after_confirmed_event_is_unpublished(setup,failure,monkeypatch):
    collector,backend=setup.make()
    def process(context):
        collector.context=context
        if failure=="write":
            monkeypatch.setattr(collector.evidence,"save",lambda *a: (_ for _ in ()).throw(OSError("private path")))
        if failure=="sqlite":
            monkeypatch.setattr(collector.ingest,"ingest",lambda *a,**k: (_ for _ in ()).throw(__import__("sqlite3").OperationalError("private path")))
        try:
            for i in range(5): frame(collector,i)
            if failure=="duplicate":
                event=collector.engine.process
                from core.schemas.compliance import ComplianceEvent,ComplianceEventType
                row=next(collector.rows())
                collector.engine.process=lambda *a:(ComplianceEvent(row["event_id"],1,ComplianceEventType.NO_HELMET,.95,1.5,()),)
                frame(collector,5)
            elif failure=="cancel":
                setup.repo.cancel(collector.job_id)
                frame(collector,5)
            else: raise RuntimeError("observer secret")
        finally: collector.close()
    worker=SingleWorker(setup.repo,setup.storage,ResourceAdmission(lambda:"idle"),processors={"video":process})
    assert worker.run_once()
    job=setup.repo.get(collector.job_id)
    assert job["status"] == ("CANCELLED" if failure=="cancel" else "FAILED")
    assert list(setup.storage.path(collector.job_id,"staging","events.json").parent.iterdir()) == []
    assert list(setup.storage.path(collector.job_id,"output","events.json").parent.iterdir()) == []
    assert setup.storage.path(collector.job_id,"input","source.mp4").exists()
    assert worker.admission.offline_job_id is None and backend.resets==1


def test_wrong_context_rejected(setup):
    collector,_=setup.make()
    try:
        with pytest.raises(JobError,match="上下文"):
            collector(FrameData(1,1.,np.zeros((20,20,3),dtype=np.uint8)),(),np.zeros((20,20,3),dtype=np.uint8))
    finally: collector.close()


def test_ambiguous_association_not_forced_violation(setup):
    collector,_ = setup.make()
    try:
        for index in range(5):
            timestamp = index * .3
            image = np.zeros((200,260,3), dtype=np.uint8)
            f = FrameData(index,timestamp,image)
            items = [(0,"person",(10,10,110,190)), (0,"person",(10,10,110,190)),
                     (2,"no_hardhat",(20,15,80,65)), (4,"no_vest",(20,80,90,160))]
            detections = tuple(DetectionResult(index,timestamp,collector.source,Detection(BoundingBox(*box),cid,name,.95)) for cid,name,box in items)
            collector(f,detections,AnnotatedFrameRenderer(("person","hardhat","no_hardhat","vest","no_vest")).render(f,detections))
        summary = collector.finalize()
        assert summary["unknown_associations"] == 10
        assert summary["events_by_type"] == {"PPE_UNKNOWN":2}
    finally: collector.close()


def test_real_bytetrack_empty_updates_and_task_reset(setup):
    for job_id in ("a"*32,"b"*32):
        collector,_ = setup.make(job_id)
        collector.tracker = ByteTrackPersonTrackingAdapter()
        try:
            for i in range(5): frame(collector,i)
            assert collector.track_ids == {1}
            for i in range(5,40): frame(collector,i,people=0)
            assert collector.frames == 40 and collector.active == 0
            assert collector.finalize()["confirmed_events"] == 2
        finally: collector.close()


@pytest.mark.parametrize("value",["=SUM(1,2)"," +1","-1","@cmd","\tvalue","\rvalue"])
def test_csv_formula_boundary(value):
    assert csv_safe(value).startswith("'")


def test_optional_decoder_missing_is_safe_invalid_media(tmp_path,monkeypatch):
    from offline.media import inspect_image
    from offline.jobs import OfflineSettings
    from PIL import Image
    monkeypatch.setattr(Image,"open",lambda *a,**k:(_ for _ in ()).throw(ModuleNotFoundError("optional decoder")))
    with pytest.raises(JobError) as error:
        inspect_image(tmp_path/"invalid.png",".png",OfflineSettings(root=tmp_path))
    assert error.value.code=="INVALID_MEDIA"


def test_export_write_hash_mismatch_rejected(setup,monkeypatch):
    from offline.event_collector import DigestWriter
    collector,_=setup.make()
    write=DigestWriter.write
    def corrupt(self,text):
        count=write(self,text)
        if self.handle.name.endswith("events.json") and text=="]}":
            self.handle.write("bad")
        return count
    monkeypatch.setattr(DigestWriter,"write",corrupt)
    try:
        for i in range(5): frame(collector,i)
        with pytest.raises(JobError) as error: collector.finalize()
        assert error.value.code=="EVENT_EXPORT_CORRUPT"
    finally: collector.close()


def test_video_collector_zero_event_exports_and_one_inference(system):
    system.processor.collector_factory = OfflineEventCollector
    assert system.worker.run_once()
    job = system.repo.get(system.job_id)
    assert job["status"] == "COMPLETED",job
    assert system.calls == list(range(6))
    summary = json.loads(system.storage.artifact(job,"summary")[0].read_text())
    assert summary["event_analysis_status"] == "COMPLETED" and summary["confirmed_events"] == 0
    assert summary["evidence_image_files"] == 0
    assert json.loads(system.storage.artifact(job,"events")[0].read_text())["items"] == []


def test_video_collector_exception_closes_and_prevents_publication(system):
    closed=[]
    class Broken(OfflineEventCollector):
        def __call__(self,*args): raise RuntimeError("private observer details")
        def close(self):
            super().close()
            closed.append(True)
    system.processor.collector_factory = Broken
    assert_failed(system,"PROCESSOR_FAILED")
    assert closed == [True]


def test_zip_generation_failure_cleans_event_database(system,monkeypatch):
    import offline.video_processor as module
    system.processor.collector_factory = OfflineEventCollector
    monkeypatch.setattr(module.zipfile,"ZipFile",lambda *a,**k:(_ for _ in ()).throw(OSError("zip failure")))
    assert_failed(system,"PROCESSOR_FAILED")


@pytest.mark.parametrize("phase",["write","finish"])
def test_encoder_failure_with_collector_cleans_database(system,phase):
    from offline.video_encoder import VideoEncoder
    class Broken(VideoEncoder):
        def write(self,frame):
            if phase=="write": self.process.kill()
            return super().write(frame)
        def finish(self):
            if phase=="finish": self.process.kill()
            return super().finish()
    system.processor.collector_factory = OfflineEventCollector
    system.processor.encoder_factory = Broken
    assert_failed(system,"ENCODER_FAILED")
