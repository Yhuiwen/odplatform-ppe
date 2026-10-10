"""G real image variants and bounded three-video same-process resource test.

No download, substitute checkpoint, inference mock or long-stability claim.
Runtime ZIPs stay in pytest's repository-external temporary directory.
"""
import hashlib
import io
import json
from pathlib import Path
import threading
import time
import zipfile

import pytest
pytest.importorskip('fastapi')
from fastapi.testclient import TestClient
from PIL import Image
from api.main import app
import psutil
from core.schemas.events import EventQuery


def wait(http, job_id, timeout=300):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        response=http.get(f'/api/v1/offline/jobs/{job_id}')
        assert response.status_code==200
        job=response.json()
        if job['status'] in {'COMPLETED','FAILED','CANCELLED','INTERRUPTED'}:
            assert job['status']=='COMPLETED',job
            return job
        time.sleep(.2)
    pytest.fail('real job timeout')


def download(http, job):
    prefix=f"/api/v1/offline/jobs/{job['job_id']}"
    response=http.get(prefix+'/artifacts');assert response.status_code==200
    items=response.json()['items'];data={}
    for item in items:
        result=http.get(prefix+'/artifacts/'+item['key']);assert result.status_code==200
        assert len(result.content)==item['size_bytes']
        assert hashlib.sha256(result.content).hexdigest()==item['sha256']
        data[item['key']]=result.content
    with zipfile.ZipFile(io.BytesIO(data['results'])) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(set(archive.namelist()))
        assert all(not n.startswith('/') and '..' not in n.split('/') for n in archive.namelist())
    return data,items


def setup(monkeypatch,tmp_path):
    if not Path('models/checkpoints/EXP-001/best.pt').is_file():
        pytest.skip('frozen model missing: NOT_EXECUTED')
    monkeypatch.setenv('ODPLATFORM_OFFLINE_ROOT',str(tmp_path/'jobs'))
    for name in ('IMAGE','VIDEO','EVENT'):
        monkeypatch.setenv(f'ODPLATFORM_OFFLINE_{name}_EXECUTION','1')


def test_g_real_image_variants(tmp_path,monkeypatch):
    source=Path('artifacts/validation/P4C-1/input/construction-workers-public-domain.jpg')
    if not source.is_file():pytest.skip('public image missing: NOT_EXECUTED')
    setup(monkeypatch,tmp_path)
    original=source.read_bytes()
    cases=[('original.jpg',original,(1024,766)),('original.jpeg',original,(1024,766))]
    with Image.open(io.BytesIO(original)) as base:
        variants=[('rgb.png',base.convert('RGB'),{}),('rgba.png',base.convert('RGBA'),{}),('gray.png',base.convert('L'),{}),('wide.png',base.resize((1200,300)),{})]
        exif=Image.Exif();exif[274]=6
        variants.append(('exif.jpg',base.convert('RGB'),{'exif':exif}))
        variants.append(('empty.png',Image.new('RGB',(320,240),'white'),{}))
        for name,image,options in variants:
            encoded=io.BytesIO();image.save(encoded,format='JPEG' if name.endswith('jpg') else 'PNG',**options)
            cases.append((name,encoded.getvalue(),(766,1024) if name=='exif.jpg' else image.size))
    records=[]
    with TestClient(app,base_url='http://127.0.0.1:8000') as http:
        before=app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count
        for name,payload,size in cases:
            response=http.post('/api/v1/offline/jobs',files={'file':(name,payload,'image/jpeg' if name.endswith(('jpg','jpeg')) else 'image/png')})
            assert response.status_code==202,response.text
            job=wait(http,response.json()['job_id']);data,items=download(http,job)
            prefix=f"/api/v1/offline/jobs/{job['job_id']}"
            assert http.get(prefix+'/input-image').content==payload
            summary=json.loads(data['summary']);detections=json.loads(data['detections'])['detections']
            assert summary['input_sha256']==hashlib.sha256(payload).hexdigest()
            with Image.open(io.BytesIO(data['annotated'])) as image:
                assert image.size==size;image.verify()
            assert len(detections)==summary['detection_count']==job['detection_count']
            assert sum(summary['class_counts'].values())==len(detections)
            assert all(row['class_name'] in {'person','hardhat','no_hardhat','vest','no_vest'} for row in detections)
            for row in detections:
                x1,y1,x2,y2=row['bbox_xyxy'];assert 0<=x1<x2<=size[0] and 0<=y1<y2<=size[1]
            if name=='empty.png':assert not detections and summary['candidate_count']==0
            assert http.get(prefix).json()['status']=='COMPLETED'
            records.append({'name':name,'size':size,'detections':len(detections),'candidates':summary['candidate_count'],'items':items})
        assert app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count==before
    print('G_IMAGE_RESULT',json.dumps(records))


def test_g_real_mixed_fifo_and_queued_cancel(tmp_path,monkeypatch):
    image=Path('artifacts/validation/P4C-1/input/construction-workers-public-domain.jpg')
    video=Path('artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4')
    if not image.is_file() or not video.is_file():pytest.skip('verified media missing: NOT_EXECUTED')
    setup(monkeypatch,tmp_path)
    with TestClient(app,base_url='http://127.0.0.1:8000') as http:
        worker=app.state.offline_worker;inference=worker.processors['image'].inference
        calls=[];original=inference.infer_frame
        def observe(frame,*,source):
            calls.append((source,frame.frame_id))
            return original(frame,source=source)
        inference.infer_frame=observe
        jobs=[]
        for name,source,mime in [('first.mp4',video,'video/mp4'),('second.jpg',image,'image/jpeg'),('third.mp4',video,'video/mp4'),('cancel.jpg',image,'image/jpeg')]:
            with source.open('rb') as handle:
                response=http.post('/api/v1/offline/jobs',files={'file':(name,handle,mime)})
            assert response.status_code==202,response.text
            jobs.append(response.json()['job_id'])
        cancelled=http.post(f'/api/v1/offline/jobs/{jobs[-1]}/cancel')
        assert cancelled.status_code==200 and cancelled.json()['status']=='CANCELLED'
        identities=[]
        for job_id in jobs[:3]:
            job=wait(http,job_id);download(http,job)
            identities.append(id(worker.processors['image'].detector._model))
        order=[]
        for source,frame in calls:
            job_id=source.split(':')[-1]
            if not order or order[-1]!=job_id:order.append(job_id)
        assert order==jobs[:3] and len(set(identities))==1
        assert len(calls)==47+1+47
        assert http.get(f'/api/v1/offline/jobs/{jobs[-1]}/artifacts').json()=={'items':[]}
        print('G_MIXED_FIFO_RESULT',json.dumps({'order':order,'cancelled':jobs[-1],'inference_calls':len(calls),'same_model':True}))


def test_g_three_sequential_real_videos(tmp_path,monkeypatch):
    source=Path('artifacts/validation/test/4afa6b121fe5db806c3ff416bafdf571.mp4')
    if not source.is_file():pytest.skip('verified 570-frame video missing: NOT_EXECUTED')
    setup(monkeypatch,tmp_path)
    process=psutil.Process();peak=[process.memory_info().rss];stop=threading.Event()
    def sample():
        while not stop.wait(.1):peak[0]=max(peak[0],process.memory_info().rss)
    thread=threading.Thread(target=sample);thread.start();records=[];identities=[];worker=None
    try:
        with TestClient(app,base_url='http://127.0.0.1:8000') as http:
            before=app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count
            worker=app.state.offline_worker
            for index in range(3):
                started=time.monotonic();cpu=process.cpu_times()
                with source.open('rb') as handle:
                    response=http.post('/api/v1/offline/jobs',files={'file':(f'repeat-{index}.mp4',handle,'video/mp4')},data={'audio_discard_confirmed':'true'})
                assert response.status_code==202,response.text
                job=wait(http,response.json()['job_id']);data,items=download(http,job)
                summary=json.loads(data['summary']);verification=json.loads(data['video_verification'])
                assert job['processed_frames']==570
                for key in ('input_decoded_frames','inferred_frames','rendered_frames','written_frames','output_decoded_frames'):assert verification[key]==570
                output=verification['output'];source_info=verification['input']
                assert (output['input_width'],output['input_height'],output['input_codec'],output['fps_rational'])==(1280,720,'h264','30')
                assert output['pixel_format']=='yuv420p' and output['has_audio'] is False
                # Container/audio duration can differ by less than one video frame.
                assert abs(output['input_duration_seconds']-570/30)<=1/30
                assert abs(output['input_duration_seconds']-source_info['input_duration_seconds'])<=1/30
                assert summary['detection_count']==1829
                assert summary['confirmed_events']==2 and summary['evidence_image_files']==4
                assert {key:summary['events_by_type'].get(key,0) for key in ('NO_HELMET','NO_VEST','PPE_UNKNOWN')}=={'NO_HELMET':1,'NO_VEST':1,'PPE_UNKNOWN':0}
                identities.append(id(worker.processors['image'].detector._model))
                deadline=time.monotonic()+5
                while app.state.offline_admission.offline_job_id and time.monotonic()<deadline:time.sleep(.01)
                assert app.state.offline_admission.offline_job_id is None
                assert not [c for c in process.children() if 'ffmpeg' in c.name().lower()]
                time.sleep(.3)
                cpu_end=process.cpu_times();elapsed=time.monotonic()-started
                records.append({'job_id':job['job_id'],'wall_seconds':elapsed,'effective_fps':570/elapsed,'end_rss_bytes':process.memory_info().rss,'cpu_seconds':cpu_end.user+cpu_end.system-cpu.user-cpu.system,'output_bytes':sum(i['size_bytes'] for i in items),'db_bytes':app.state.offline_storage.artifact(app.state.offline_jobs.get(job['job_id']),'events_db')[0].stat().st_size,'evidence_bytes':sum(i['size_bytes'] for i in items if i['key'].startswith(('original_','annotated_'))),'verification':verification})
            assert len(set(identities))==1
            assert app.state.dashboard.query_service.query_events(EventQuery(limit=1)).total_count==before
        assert not worker._thread.is_alive()
    finally:
        stop.set();thread.join(2)
        report={'records':records,'peak_rss_bytes':peak[0],'end_rss_bytes':process.memory_info().rss,'worker_alive_after_shutdown':worker._thread.is_alive() if worker else None,'ffmpeg_remaining':[c.name() for c in process.children() if 'ffmpeg' in c.name().lower()]}
        print('G_STABILITY_RESULT',json.dumps(report))
