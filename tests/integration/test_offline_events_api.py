"""Read-only task/event/evidence HTTP boundary with deterministic legal inputs."""
import json
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from api.main import app
from offline.event_collector import OfflineEventCollector
from offline.jobs import sha256_file
from offline.worker import SingleWorker
from core.tracking.bytetrack_adapter import ByteTrackPersonTrackingAdapter
from tests.unit.test_offline_event_collector import frame, DeterministicBackend


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv("ODPLATFORM_OFFLINE_ROOT",str(tmp_path/"jobs"))
    monkeypatch.setenv("ODPLATFORM_OFFLINE_IMAGE_EXECUTION","0")
    from services.alert_service import AlertService
    monkeypatch.setattr(AlertService,"dispatch_event",lambda *a,**k:pytest.fail("offline task called realtime alerts"))
    monkeypatch.setattr(AlertService,"dispatch",lambda *a,**k:pytest.fail("offline task called realtime alerts"))
    with TestClient(app,base_url="http://127.0.0.1:8000") as http:
        from core.schemas.events import EventQuery
        before = app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count
        monitor = app.state.monitoring
        monitor_status = monitor.status() if monitor is not None else None
        def make(job_id, complete=True):
            storage,repo=app.state.offline_storage,app.state.offline_jobs
            storage.create(job_id)
            source=storage.path(job_id,"input","source.mp4")
            source.write_bytes(b"unit-only-video")
            repo.create(job_id,"video","unit.mp4",True)
            repo.transition(job_id,"QUEUED",updates={"input_sha256":sha256_file(source),"input_size_bytes":source.stat().st_size})
            if not complete: return
            def process(context):
                collector=OfflineEventCollector(context,tracker=ByteTrackPersonTrackingAdapter(backend=DeterministicBackend()))
                try:
                    for i in range(5): frame(collector,i)
                    collector.finalize()
                    return {key:context.publisher.publish(job_id,key,name,sha256_file(storage.path(job_id,"staging",name))) for name,(key,_) in collector.files.items()}
                finally: collector.close()
            worker=SingleWorker(repo,storage,app.state.offline_admission,processors={"video":process})
            assert worker.run_once()
            assert repo.get(job_id)["status"]=="COMPLETED"
        make("a"*32)
        make("b"*32)
        make("c"*32,False)
        assert app.state.monitoring is monitor
        assert (monitor.status() if monitor is not None else None) == monitor_status
        assert app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count == before
        yield http


def test_pagination_filter_details_variants_and_job_isolation(client):
    base="/api/v1/offline/jobs/"+"a"*32
    page=client.get(base+"/events",params={"limit":1}).json()
    assert page["total"]==2 and len(page["items"])==1
    row=page["items"][0]
    assert client.get(base+"/events",params={"event_type":"NO_VEST"}).json()["total"]==1
    assert client.get(base+"/evidence",params={"offset":2}).json()["items"]==[]
    assert client.get(base+"/events",params={"event_type":"invented"}).status_code==422
    assert client.get(base+"/events/"+row["event_id"]).json()==row
    assert client.get(base+"/evidence/"+row["evidence_id"]).json()==row
    assert "filename" not in row["original"]
    for variant in ("original","annotated"):
        response=client.get(base+f"/evidence/{row['evidence_id']}/image",params={"variant":variant})
        assert response.status_code==200 and response.headers["content-type"]=="image/png"
    assert client.get(base+f"/evidence/{row['evidence_id']}/image",params={"variant":"../../secret"}).status_code==422
    assert client.get("/api/v1/offline/jobs/"+"b"*32+"/events/"+row["event_id"]).status_code==404
    assert client.get("/api/v1/offline/jobs/"+"b"*32+"/evidence/"+row["evidence_id"]).status_code==404
    assert client.get(base+"/events/invalid").status_code==404
    assert client.get(base+"/artifacts/events_db").status_code==404
    assert "events_db" not in client.get(base).json()["artifact_keys"]
    assert client.patch(base+"/events/"+row["event_id"],json={"handled":True}).status_code==405


@pytest.mark.parametrize("suffix",["events","evidence"])
def test_unfinished_cancelled_missing_job_unavailable(client,suffix):
    base="/api/v1/offline/jobs/"+"c"*32
    assert client.get(base+"/"+suffix).status_code==404
    client.post(base+"/cancel")
    assert client.get(base+"/"+suffix).status_code==404
    assert client.get("/api/v1/offline/jobs/"+"d"*32+"/"+suffix).status_code==404


@pytest.mark.parametrize("mode",["sha","missing","database"])
def test_corruption_never_reports_verified(client,mode):
    job_id="a"*32
    base="/api/v1/offline/jobs/"+job_id
    row=client.get(base+"/events").json()["items"][0]
    key="events_db" if mode=="database" else row["original"]["artifact_key"]
    path=app.state.offline_storage.artifact(app.state.offline_jobs.get(job_id),key)[0]
    if mode=="missing": path.unlink()
    else: path.write_bytes(b"damaged")
    response=client.get(base+"/evidence/"+row["evidence_id"])
    assert response.status_code==409
    assert str(path) not in response.text
