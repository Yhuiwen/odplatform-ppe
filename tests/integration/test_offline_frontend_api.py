"""F restricted original-image, HEAD, Range and immutable-cache boundary."""
import hashlib
from pathlib import Path
from uuid import uuid4
import pytest
pytest.importorskip('fastapi')
from api.main import app
from fastapi.testclient import TestClient
from offline.jobs import sha256_file

@pytest.fixture
def completed(tmp_path,monkeypatch):
    monkeypatch.setenv('ODPLATFORM_OFFLINE_ROOT',str(tmp_path/'jobs'))
    monkeypatch.setenv('ODPLATFORM_OFFLINE_IMAGE_EXECUTION','0')
    monkeypatch.setenv('ODPLATFORM_OFFLINE_VIDEO_EXECUTION','0')
    with TestClient(app,base_url='http://127.0.0.1:8000',raise_server_exceptions=False) as http:
        repo=app.state.offline_jobs;storage=app.state.offline_storage
        job_id=uuid4().hex;storage.create(job_id);repo.create(job_id,'image','safe.png',False)
        data=b'0123456789abcdef';source=storage.path(job_id,'input','source.png');source.write_bytes(data)
        repo.transition(job_id,'QUEUED',updates={'input_mime':'image/png','input_sha256':hashlib.sha256(data).hexdigest(),'input_size_bytes':len(data)})
        repo.transition(job_id,'PROCESSING')
        repo.record_image_result(job_id,0,0,0.1)
        path=storage.path(job_id,'output','annotated.mp4');path.write_bytes(data)
        manifest={'annotated':{'filename':'annotated.mp4','verified':True,'size_bytes':len(data),'sha256':sha256_file(path)}}
        repo.transition(job_id,'COMPLETED',updates={'artifact_manifest':manifest})
        yield http,job_id,path,source,data

def test_standard_ranges_head_and_416(completed):
    http,id,path,source,data=completed;url=f'/api/v1/offline/jobs/{id}/artifacts/annotated'
    for value,expected,content_range in [('bytes=2-5',data[2:6],'bytes 2-5/16'),('bytes=12-',data[12:],'bytes 12-15/16'),('bytes=-4',data[-4:],'bytes 12-15/16')]:
        response=http.get(url,headers={'Range':value});assert response.status_code==206;assert response.content==expected;assert response.headers['content-range']==content_range;assert response.headers['content-type']=='video/mp4'
    assert http.get(url,headers={'Range':'bytes=20-'}).status_code==416
    assert http.head(url).status_code==200
    assert not http.head(url).content
    assert 'annotated.mp4' in http.head(url).headers['content-disposition']

def test_cache_avoids_repeat_hash_and_invalidates_mutation(completed,monkeypatch):
    import offline.jobs as jobs
    http,id,path,source,data=completed;url=f'/api/v1/offline/jobs/{id}/artifacts/annotated'
    original=jobs.sha256_file;calls=[]
    def counted(path):calls.append(path);return original(path)
    monkeypatch.setattr(jobs,'sha256_file',counted)
    for _ in range(3):assert http.get(url,headers={'Range':'bytes=0-2'}).status_code==206
    assert len(calls)==1
    path.write_bytes(b'X'+data[1:])
    assert http.get(url,headers={'Range':'bytes=0-2'}).status_code==409

def test_confined_original_image_and_corruption(completed):
    http,id,path,source,data=completed;url=f'/api/v1/offline/jobs/{id}/input-image'
    response=http.get(url);assert response.status_code==200;assert response.content==data;assert response.headers['content-type']=='image/png'
    assert http.get(f'/api/v1/offline/jobs/{uuid4().hex}/input-image').status_code==404
    assert http.get(f'/api/v1/offline/jobs/{id}/artifacts/events_db').status_code==404
    source.write_bytes(b'corrupt')
    assert http.get(url).status_code==409

def test_missing_and_cross_origin_denied(completed):
    http,id,path,source,data=completed
    assert http.get(f'/api/v1/offline/jobs/{id}/artifacts/missing').status_code==404
    assert http.get(f'/api/v1/offline/jobs/{id}/artifacts/annotated',headers={'Origin':'https://invalid.example'}).status_code==403
    path.unlink()
    assert http.get(f'/api/v1/offline/jobs/{id}/artifacts/annotated').status_code==409


def test_invalid_ranges_and_local_origin_boundaries(completed):
    http,id,path,source,data=completed;url=f'/api/v1/offline/jobs/{id}/artifacts/annotated'
    for value in ('not-a-range','items=0-1','bytes=x-y','bytes=5-2'):
        response=http.get(url,headers={'Range':value})
        assert response.status_code==400
        assert 'Traceback' not in response.text
    response=http.get(url,headers={'Range':'bytes=100-200'})
    assert response.status_code==416 and response.headers['content-range']=='*/16'
    assert http.get(url,headers={'Origin':'http://127.0.0.1:8000'}).status_code==200
    assert http.get(url,headers={'Host':'remote.example'}).status_code==403
    assert http.get(url,headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
    response=http.get(url,headers={'Range':'bytes=0-1'})
    assert response.status_code==206 and response.headers['cache-control']=='no-store'


def test_upload_disk_low_and_write_error_are_safe(completed,monkeypatch):
    import io
    from PIL import Image
    from types import SimpleNamespace
    import api.offline as endpoint
    http,*_=completed
    payload=io.BytesIO();Image.new('RGB',(16,16),'white').save(payload,'PNG')
    upload={'file':('sample.png',payload.getvalue(),'image/png')}
    with monkeypatch.context() as patch:
        patch.setattr(endpoint.shutil,'disk_usage',lambda _:SimpleNamespace(free=0))
        response=http.post('/api/v1/offline/jobs',files=upload)
        assert response.status_code==507 and response.json()['detail']['code']=='DISK_LOW'
    with monkeypatch.context() as patch:
        def denied(_):raise PermissionError('PRIVATE_ABSOLUTE_PATH must stay private')
        patch.setattr(endpoint.os,'fsync',denied)
        response=http.post('/api/v1/offline/jobs',files=upload)
        assert response.status_code==500
        assert 'PRIVATE_ABSOLUTE_PATH' not in response.text and 'Traceback' not in response.text
    assert not list(app.state.offline_storage.root.rglob('upload.part'))


def test_missing_probe_bad_mp4_and_rotation_metadata(completed,monkeypatch,tmp_path):
    from offline.jobs import OfflineSettings,JobError
    from offline.media import inspect_video
    import offline.media as media
    http,*_=completed
    response=http.post('/api/v1/offline/jobs',files={'file':('bad.mp4',b'not an mp4','video/mp4')})
    assert response.status_code==415
    header=b'\x00\x00\x00\x18ftypisom'+b'\x00'*20
    with monkeypatch.context() as patch:
        def missing(*a,**kw):raise FileNotFoundError('private ffprobe path')
        patch.setattr(media.subprocess,'run',missing)
        response=http.post('/api/v1/offline/jobs',files={'file':('probe.mp4',header,'video/mp4')})
        assert response.status_code==503 and response.json()['detail']['code']=='PROBE_UNAVAILABLE'
        assert 'private ffprobe path' not in response.text
    # Metadata contract negative test; not a real model/video resolution claim.
    path=tmp_path/'rotation.mp4';path.write_bytes(header)
    probe={'format':{'duration':'1'},'streams':[{'codec_type':'video','codec_name':'h264','width':640,'height':480,'avg_frame_rate':'30/1','r_frame_rate':'30/1','nb_frames':'30','side_data_list':[{'rotation':90}]}]}
    with pytest.raises(JobError) as error:inspect_video(path,OfflineSettings(root=tmp_path),probe=probe)
    assert error.value.code=='UNSUPPORTED_ROTATION'
