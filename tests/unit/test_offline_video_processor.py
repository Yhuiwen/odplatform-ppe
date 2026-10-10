"""Deterministic synthetic media and injected failures; no substitute model."""
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
import json
import shutil
import subprocess
import threading

import pytest
pytest.importorskip("fastapi")
from api.main import app
import numpy as np
from offline.jobs import JobError, JobRepository, JobStorage, OfflineSettings, sha256_file
from offline.image_processor import ImageProcessor
from offline.video_encoder import VideoEncoder
from offline.video_probe import probe_cfr
from offline.video_processor import VideoProcessor, OUTPUTS
from offline.worker import ResourceAdmission, SingleWorker
from core.video.reader import VideoReader, VideoDecodeError


@pytest.fixture
def system(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg unavailable")
    source = tmp_path / "synthetic.mp4"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","testsrc2=s=160x90:r=30000/1001",
                    "-frames:v","6","-an","-c:v","libx264","-pix_fmt","yuv420p",str(source)],check=True,timeout=20)
    storage = JobStorage(tmp_path/"jobs")
    repo = JobRepository(storage.root/"jobs.sqlite3")
    job_id = "a"*32
    storage.create(job_id)
    target = storage.path(job_id,"input","source.mp4")
    shutil.copyfile(source,target)
    repo.create(job_id,"video","synthetic.mp4",True)
    repo.transition(job_id,"QUEUED",updates={"input_sha256":sha256_file(target),"input_size_bytes":target.stat().st_size})
    detector = SimpleNamespace(class_names=("person","hardhat","no_hardhat","vest","no_vest"),runtime_id="SYNTHETIC-UNIT",
                              expected_model_sha256="a"*64)
    calls=[]
    def infer(frame,source):
        calls.append(frame.frame_id)
        return []
    settings = OfflineSettings(root=storage.root,min_free_bytes=1)
    image = ImageProcessor(settings,inference=SimpleNamespace(detector=detector,infer_frame=infer))
    image.preflight=lambda:(True,None)
    processor = VideoProcessor(image)
    admission = ResourceAdmission(lambda:"idle")
    worker = SingleWorker(repo,storage,admission,processors={"video":processor})
    return SimpleNamespace(storage=storage,repo=repo,job_id=job_id,processor=processor,worker=worker,
                           admission=admission,source=target,calls=calls)


def assert_failed(system, code):
    assert system.worker.run_once()
    job=system.repo.get(system.job_id)
    assert job["status"]=="FAILED",job
    assert job["error_code"]==code,job
    assert system.admission.offline_job_id is None
    assert system.source.exists()
    assert not list(system.storage.path(system.job_id,"staging","annotated.mp4").parent.iterdir())
    assert not list(system.storage.path(system.job_id,"output","annotated.mp4").parent.iterdir())


def test_fractional_full_frames_no_detections(system):
    assert system.worker.run_once()
    job=system.repo.get(system.job_id)
    assert job["status"]=="COMPLETED",job
    assert system.calls==list(range(6))
    output=system.storage.artifact(job,"video_verification")[0]
    verification=json.loads(output.read_text())
    assert verification["output"]["fps_rational"]=="30000/1001"
    assert verification["output_decoded_frames"]==6
    assert job["candidate_count"] is None and job["detection_count"]==0
    assert job["progress_percent"]==100
    assert not system.worker.run_once()
    system.storage.artifact(job,"annotated")[0].write_bytes(b"corrupt")
    with pytest.raises(JobError,match="完整性"):
        system.storage.artifact(job,"annotated")


@pytest.mark.parametrize("payload",[b"",b"corrupt",b"\x00\x00\x00\x18ftypisomfake"])
def test_corrupt_input(system,payload):
    system.source.write_bytes(payload)
    assert_failed(system,"INPUT_CORRUPT")


def test_inference_failure(system):
    system.processor.image.inference.infer_frame=lambda *a,**k: (_ for _ in ()).throw(RuntimeError("private secret"))
    assert_failed(system,"PROCESSOR_FAILED")
    assert system.repo.get(system.job_id)["error_message"]=="离线处理失败"


@pytest.mark.parametrize("failure",["unavailable","write","finish"])
def test_encoder_failures(system,failure):
    class Broken(VideoEncoder):
        def __init__(self,*args):
            if failure=="unavailable":
                raise JobError("ENCODER_UNAVAILABLE","编码器不可用")
            super().__init__(*args)
        def write(self,frame):
            if failure=="write":
                self.process.kill()
            return super().write(frame)
        def finish(self):
            if failure=="finish":
                self.process.kill()
            return super().finish()
    system.processor.encoder_factory=Broken
    assert_failed(system,"ENCODER_UNAVAILABLE" if failure=="unavailable" else "ENCODER_FAILED")


@pytest.mark.parametrize("mode",["midframe","dimensions","count"])
def test_decoder_failure(system,mode):
    class Broken(VideoReader):
        def iter_frames(self):
            for frame in super().iter_frames():
                if frame.frame_id==2:
                    if mode=="midframe":
                        raise VideoDecodeError("bad frame")
                    if mode=="count":
                        return
                    frame.image=frame.image[:50]
                yield frame
    # FrameData is frozen; dimension failure instead uses an injected renderer.
    if mode=="dimensions":
        render=system.processor.image.renderer.render
        system.processor.image.renderer.render=lambda f,d:render(f,d)[:50]
        assert_failed(system,"OUTPUT_DIMENSIONS")
    else:
        system.processor.reader_factory=Broken
        assert_failed(system,"VIDEO_PROCESSING_FAILED" if mode=="midframe" else "FRAME_COUNT_MISMATCH")


@pytest.mark.parametrize("phase",["processing","encoding"])
def test_cancel_at_checkpoints(system,phase):
    if phase=="processing":
        original=system.processor.image.inference.infer_frame
        def infer(*a,**k):
            system.repo.cancel(system.job_id)
            return original(*a,**k)
        system.processor.image.inference.infer_frame=infer
    else:
        class Cancel(VideoEncoder):
            def finish(self):
                system.repo.cancel(system.job_id)
                raise JobError("JOB_CANCELLED","收尾已取消")
        system.processor.encoder_factory=Cancel
    assert system.worker.run_once()
    assert system.repo.get(system.job_id)["status"]=="CANCELLED"
    assert system.admission.offline_job_id is None
    assert system.source.exists()
    for name in OUTPUTS:
        assert not system.storage.path(system.job_id,"staging",name).exists()
        assert not system.storage.path(system.job_id,"output",name).exists()


def test_disk_limit(system):
    system.processor.settings=replace(system.processor.settings,max_staging_bytes=1)
    assert_failed(system,"DISK_LIMIT")


def test_admission_and_encoding_restart(system):
    system.admission.monitor_state=lambda:"running"
    assert not system.worker.run_once()
    system.repo.transition(system.job_id,"PROCESSING")
    system.repo.transition(system.job_id,"ENCODING")
    system.repo.recover()
    assert system.repo.get(system.job_id)["status"]=="INTERRUPTED"


def test_odd_dimensions():
    with pytest.raises(JobError) as error:
        VideoEncoder(Path("unused.mp4"),161,90,Fraction(30))
    assert error.value.code=="UNSUPPORTED_DIMENSIONS"


def test_blocked_pipe_timeout(tmp_path,monkeypatch):
    import sys
    original=subprocess.Popen
    def stalled(*args,**kwargs):
        return original([sys.executable,"-c","import time;time.sleep(60)"],**kwargs)
    monkeypatch.setattr("offline.video_encoder.subprocess.Popen",stalled)
    encoder=VideoEncoder(tmp_path/"unused.mp4",1920,1080,Fraction(30),timeout=.2)
    with pytest.raises(JobError) as error:
        encoder.write(np.zeros((1080,1920,3),dtype=np.uint8))
    assert error.value.code=="ENCODER_TIMEOUT"
    assert not encoder.writer_thread.is_alive() and not encoder.stderr_thread.is_alive()
    assert encoder.process.poll() is not None


@pytest.mark.parametrize("kind",["count","width","codec","fps","audio"])
def test_output_contract_mismatch(system,monkeypatch,kind):
    import offline.video_processor as module
    original=module.probe_cfr
    def altered(path,*args):
        result=original(path,*args)
        if path.name=="annotated.mp4":
            field,value={"count":("input_frame_count",5),"width":("input_width",162),"codec":("input_codec","mpeg4"),
                         "fps":("fps_rational","25"),"audio":("has_audio",True)}[kind]
            result[field]=value
        return result
    monkeypatch.setattr(module,"probe_cfr",altered)
    if kind=="count":
        # Verified timestamp count must also agree with the actual decode count.
        assert system.worker.run_once()
        assert system.repo.get(system.job_id)["status"]=="FAILED"
    else:
        assert_failed(system,"OUTPUT_DIMENSIONS" if kind=="width" else "OUTPUT_FORMAT")


def test_missing_audio_confirmation(system,monkeypatch):
    import offline.video_processor as module
    system.repo.path # keep the same durable record; update fixture confirmation only
    with system.repo._connect() as db:
        db.execute("UPDATE jobs SET audio_discard_confirmed=0 WHERE job_id=?",(system.job_id,))
    original=module.probe_cfr
    monkeypatch.setattr(module,"probe_cfr",lambda *a:original(*a)|{"has_audio":True})
    assert_failed(system,"AUDIO_CONFIRMATION_REQUIRED")


def test_fullhd_encoder_synthetic_only(tmp_path):
    path=tmp_path/"fullhd.mp4"
    encoder=VideoEncoder(path,1920,1080,Fraction(30))
    try:
        for value in (0,80,160):
            encoder.write(np.full((1080,1920,3),value,dtype=np.uint8))
        encoder.finish()
    finally:
        encoder.abort()
    info=probe_cfr(path,OfflineSettings(root=tmp_path))
    assert (info["input_width"],info["input_height"],info["input_frame_count"])==(1920,1080,3)
    with VideoReader(path) as reader:
        for frame in reader:
            assert abs(float(frame.image.mean()) - (0,80,160)[frame.frame_id]) < 3


def test_vfr_rejected(tmp_path):
    path=tmp_path/"vfr.mp4"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","testsrc2=s=160x90:r=30",
        "-frames:v","8","-vf","setpts='if(lt(N,4),N,2*N-4)/(30*TB)'","-fps_mode","vfr","-c:v","libx264",str(path)],check=True,timeout=20)
    with pytest.raises(JobError) as error:
        probe_cfr(path,OfflineSettings(root=tmp_path))
    assert error.value.code=="UNSUPPORTED_TIMING"


def test_corrupt_generated_json(system,monkeypatch):
    import offline.video_processor as module
    original=module._write_synced
    def corrupt(path,payload):
        original(path,payload)
        if path.name=="summary.json":
            path.write_bytes(b"corrupt")
    monkeypatch.setattr(module,"_write_synced",corrupt)
    assert_failed(system,"ARTIFACT_CORRUPT")


def test_graceful_shutdown_cancel(system):
    original=system.processor.image.inference.infer_frame
    def infer(*a,**k):
        system.worker._stop.set()
        return original(*a,**k)
    system.processor.image.inference.infer_frame=infer
    assert system.worker.run_once()
    assert system.repo.get(system.job_id)["status"]=="CANCELLED"
    assert system.admission.offline_job_id is None


def test_same_second_fifo_mixed_jobs(system):
    second="0"*32
    system.storage.create(second)
    system.repo.create(second,"image","second.png",False)
    system.repo.transition(second,"QUEUED")
    with system.repo._connect() as db:
        db.execute("UPDATE jobs SET created_at='2026-10-09T00:00:00Z'")
    assert system.repo.next_queued(("image","video"))["job_id"]==system.job_id
