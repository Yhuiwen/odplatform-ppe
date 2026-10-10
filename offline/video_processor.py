"""Full-frame, bounded-memory MP4 inference using the unchanged frozen detector."""
from __future__ import annotations

import json
import hashlib
import os
import shutil
import time
import zipfile
import subprocess
from collections import Counter
from fractions import Fraction

from core.schemas.video import FrameData
from core.video.reader import VideoReader, VideoError
from core.inference.detector import InferenceError
from offline.image_processor import ImageProcessor, _json_bytes, _write_synced
from offline.jobs import JobError, sha256_file
from offline.video_encoder import VideoEncoder
from offline.video_probe import probe_cfr
from offline.media import clean_filename

OUTPUTS = ("annotated.mp4", "frames.jsonl", "summary.json", "video_verification.json", "results.zip")


class VideoProcessor:
    def __init__(self, image_processor: ImageProcessor, *, frame_observer=None, encoder_factory=VideoEncoder, reader_factory=VideoReader, collector_factory=None):
        self.image = image_processor
        self.settings = image_processor.settings
        self.collector_factory = collector_factory
        self.frame_observer = frame_observer  # E consumes these same detections, never reruns YOLO.
        self.encoder_factory, self.reader_factory = encoder_factory, reader_factory

    def preflight(self):
        ready, reason = self.image.preflight()
        if not ready:
            return ready, reason
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            return False, "FFmpeg 或 ffprobe 不可用"
        try:
            result = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=32x32:r=30",
                "-frames:v", "1", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-f", "null", "-"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10)
            if result.returncode:
                return False, "H.264 libx264 编码自检失败"
        except (OSError, subprocess.TimeoutExpired):
            return False, "FFmpeg 编码自检不可用或超时"
        return True, None

    @staticmethod
    def checkpoint(context):
        if context.cancelled():
            raise JobError("JOB_CANCELLED", "视频处理已取消")

    def __call__(self, context):
        started = time.monotonic()
        job_id = context.job["job_id"]
        source = context.storage.path(job_id, "input", "source.mp4")
        staged = lambda name: context.storage.path(job_id, "staging", name)
        encoder = None
        collector = None
        try:
            if context.job["media_type"] != "video":
                raise JobError("UNSUPPORTED_PROCESSOR", "视频处理器要求 MP4")
            if clean_filename(context.job["original_filename"])[0] != ".mp4":
                raise JobError("UNSUPPORTED_MEDIA", "视频处理器只支持 MP4")
            if not source.is_file() or source.stat().st_size != context.job["input_size_bytes"] or sha256_file(source) != context.job["input_sha256"]:
                raise JobError("INPUT_CORRUPT", "输入视频完整性校验失败")
            ready, reason = self.image.preflight()
            if not ready or sha256_file(self.image.config_path) != self.image.config_sha256:
                raise JobError("MODEL_INTEGRITY_FAILED", reason or "冻结配置被修改")
            self.checkpoint(context)
            metadata = probe_cfr(source, self.settings, context.cancelled)
            if metadata["has_audio"] and not context.job["audio_discard_confirmed"]:
                raise JobError("AUDIO_CONFIRMATION_REQUIRED", "必须确认视频输出不含音轨", 422)
            width, height = metadata["input_width"], metadata["input_height"]
            fps = Fraction(metadata["fps_rational"])
            total = metadata["input_frame_count"]
            context.progress(0, total)
            collector = self.collector_factory(context) if self.collector_factory else None
            counts = dict(input_decoded_frames=0, inferred_frames=0, rendered_frames=0, written_frames=0)
            classes = Counter()
            lines_hash = hashlib.sha256()
            encoder = self.encoder_factory(staged("annotated.mp4"), width, height, fps, context.cancelled)
            with self.reader_factory(source) as reader, staged("frames.jsonl").open("x", encoding="utf-8", newline="\n") as lines:
                for raw in reader:
                    self.checkpoint(context)
                    if raw.frame_id != counts["input_decoded_frames"] or raw.image.shape[:2] != (height, width):
                        raise JobError("INPUT_DIMENSIONS", "输入帧顺序或尺寸改变")
                    counts["input_decoded_frames"] += 1
                    frame = FrameData(raw.frame_id, float(Fraction(raw.frame_id, 1) / fps), raw.image)
                    source_id = f"offline:video:{job_id}"
                    detections = self.image.inference.infer_frame(frame, source=source_id)
                    if any(d.frame_id != frame.frame_id or d.timestamp != frame.timestamp or d.source != source_id for d in detections):
                        raise JobError("INVALID_DETECTION_CONTEXT", "推理结果不属于当前帧")
                    counts["inferred_frames"] += 1
                    self.checkpoint(context)
                    plan = self.image.renderer.annotation_plan(detections, width=width, height=height)
                    if len(plan) != len(detections):
                        raise JobError("INVALID_DETECTION_BOX", "视频检测框无效")
                    rows = [{"class_id":d.class_id,"class_name":d.class_name,"confidence":d.confidence,
                             "bbox_xyxy":list(a.bbox),"raw_bbox_xyxy":list(d.bbox.as_tuple())} for d,a in zip(detections,plan)]
                    classes.update(d.class_name for d in detections)
                    if self.frame_observer:
                        self.frame_observer(frame, tuple(detections))
                    annotated = self.image.renderer.render(frame, detections)
                    counts["rendered_frames"] += 1
                    if collector:
                        collector(frame, tuple(detections), annotated)
                    self.checkpoint(context)
                    encoder.write(annotated)
                    counts["written_frames"] += 1
                    record = json.dumps({"frame_id":frame.frame_id,"timestamp":frame.timestamp,
                        "width":width,"height":height,"detection_count":len(rows),"detections":rows}, ensure_ascii=False, allow_nan=False) + "\n"
                    lines.write(record)
                    # Text writer explicitly uses LF, matching the canonical digest.
                    lines_hash.update(record.encode("utf-8"))
                    context.progress(counts["written_frames"], total)
                    video_size = staged("annotated.mp4").stat().st_size if staged("annotated.mp4").exists() else 0
                    if video_size + lines.tell() + (collector.evidence_bytes if collector else 0) > self.settings.max_staging_bytes or shutil.disk_usage(staged("annotated.mp4").parent).free < self.settings.min_free_bytes:
                        raise JobError("DISK_LIMIT", "视频产物超限或磁盘剩余空间不足")
                lines.flush()
                os.fsync(lines.fileno())
            self.checkpoint(context)
            if context.finalizing is None:
                raise JobError("RESULT_CONTRACT_MISSING", "视频收尾状态接口不可用")
            context.finalizing()
            encoder.finish()
            output = probe_cfr(staged("annotated.mp4"), self.settings, context.cancelled)
            decoded = 0
            with self.reader_factory(staged("annotated.mp4")) as reader:
                for frame in reader:
                    self.checkpoint(context)
                    if frame.image.shape[:2] != (height,width):
                        raise JobError("OUTPUT_DIMENSIONS", "输出实际解码尺寸不一致")
                    decoded += 1
            counts["output_decoded_frames"] = decoded
            if any(value != total for value in counts.values()) or output["input_frame_count"] != total or output["timestamp_frames"] != total:
                raise JobError("FRAME_COUNT_MISMATCH", "输入、推理、标注、编码和输出帧数不一致")
            if output["fps_rational"] != str(fps) or output["input_codec"] != "h264" or output["pixel_format"] != "yuv420p" or output["has_audio"]:
                raise JobError("OUTPUT_FORMAT", "输出编码、帧率或音轨不符")
            if (output["input_width"],output["input_height"]) != (width,height):
                raise JobError("OUTPUT_DIMENSIONS", "输出视频尺寸不一致")
            if sha256_file(source) != context.job["input_sha256"]:
                raise JobError("INPUT_CORRUPT", "处理期间输入视频被修改")
            event_summary = collector.finalize() if collector else {}
            elapsed = time.monotonic() - started
            verification = {"schema_version":"offline-video-verification-v1","status":"VERIFIED", **counts,
                "input":metadata,"output":output,"source_sha256":sha256_file(source),
                "output_sha256":sha256_file(staged("annotated.mp4")),"output_size_bytes":staged("annotated.mp4").stat().st_size,
                "full_frame_preservation":True,"original_resolution_preservation":True}
            summary = {"schema_version":"offline-video-summary-v1","job_id":job_id, **counts,
                "source_sha256":verification["source_sha256"],"output_sha256":verification["output_sha256"],
                "input_width":width,"input_height":height,"output_width":width,"output_height":height,
                "source_fps":str(fps),"output_fps":output["fps_rational"],"source_has_audio":metadata["has_audio"],"output_has_audio":False,
                "model_sha256":self.image.detector.expected_model_sha256,"config_sha256":self.image.config_sha256,
                "model_runtime_id":self.image.detector.runtime_id,"class_counts":{name:classes[name] for name in self.image.detector.class_names},
                "detection_count":sum(classes.values()),"not_evaluated_classes":["machinery","vehicle"],
                "not_evaluated_status":"NOT_EVALUATED","event_analysis_status":"NOT_IMPLEMENTED",
                "confirmed_events":None,"evidence_count":None,"audio_policy":"discarded_with_confirmation" if metadata["has_audio"] else "no_source_audio",
                "playback_fps":float(fps),"fps_rational":str(fps),"processed_fps":total/elapsed,
                "processing_seconds":elapsed,"processing_scope":"decode_inference_render_encode_output_verification",
                "encoder":{"codec":"libx264","actual_codec":"h264","crf":18,"preset":"medium","pixel_format":"yuv420p","faststart":True,"lossless":False}}
            summary.update(event_summary)
            if collector:
                summary["processing_scope"] = "decode_inference_render_events_evidence_encode_output_verification_exports"
            files = {name: (name.split(".")[0], name) for name in OUTPUTS[:-1]}
            if collector:
                files.update(collector.files)
            zip_files = {name: entry[1] for name, entry in files.items() if entry[1] is not None}
            for name,document in (("summary.json",summary),("video_verification.json",verification)):
                payload = _json_bytes(document)
                _write_synced(staged(name), payload)
                if sha256_file(staged(name)) != hashlib.sha256(payload).hexdigest():
                    raise JobError("ARTIFACT_CORRUPT", "视频摘要或验证报告写入损坏")
            if sha256_file(staged("frames.jsonl")) != lines_hash.hexdigest():
                raise JobError("ARTIFACT_CORRUPT", "视频逐帧明细写入损坏")
            hashes = {name:sha256_file(staged(name)) for name in files}
            with zipfile.ZipFile(staged("results.zip"), "x") as archive:
                for name in zip_files:
                    self.checkpoint(context)
                    info = zipfile.ZipInfo(zip_files[name])
                    info.compress_type = zipfile.ZIP_STORED if name.endswith("mp4") else zipfile.ZIP_DEFLATED
                    with staged(name).open("rb") as source_file, archive.open(info, "w", force_zip64=True) as member:
                        for chunk in iter(lambda: source_file.read(1024*1024), b""):
                            self.checkpoint(context)
                            member.write(chunk)
                            if sum(staged(item).stat().st_size for item in (*files, "results.zip") if staged(item).exists()) > self.settings.max_staging_bytes or shutil.disk_usage(staged(name).parent).free < self.settings.min_free_bytes:
                                raise JobError("DISK_LIMIT", "打包产物超限或磁盘空间不足")
            with zipfile.ZipFile(staged("results.zip")) as archive:
                if archive.namelist() != list(zip_files.values()) or archive.testzip():
                    raise JobError("ZIP_INVALID", "视频压缩包目录或 CRC 校验失败")
                for name in zip_files:
                    digest = hashlib.sha256()
                    with archive.open(zip_files[name]) as member:
                        for chunk in iter(lambda: member.read(1024*1024), b""):
                            self.checkpoint(context)
                            digest.update(chunk)
                    if digest.hexdigest() != hashes[name]:
                        raise JobError("ZIP_INVALID", "视频压缩包内容指纹不符")
            with staged("frames.jsonl").open(encoding="utf-8") as lines:
                observed = 0
                for line in lines:
                    row = json.loads(line)
                    if row["frame_id"] != observed or row["detection_count"] != len(row["detections"]) or row["timestamp"] != float(Fraction(observed,1)/fps):
                        raise JobError("RESULT_INCOMPLETE", "逐帧明细顺序错误")
                    observed += 1
                if observed != total:
                    raise JobError("RESULT_INCOMPLETE", "逐帧明细数量不一致")
            manifest = {}
            files["results.zip"] = ("results", "results.zip")
            for name, (key, _) in files.items():
                self.checkpoint(context)
                manifest[key] = context.publisher.publish(job_id, key, name, hashes.get(name) or sha256_file(staged(name)))
            context.storage.verify_manifest(job_id, manifest)
            self.checkpoint(context)
            if context.record_video_result:
                context.record_video_result(sum(classes.values()), time.monotonic()-started)
            return manifest
        except (VideoError, InferenceError) as exc:
            raise JobError("VIDEO_PROCESSING_FAILED", "视频解码或冻结模型推理失败") from exc
        finally:
            try:
                if encoder:
                    encoder.abort()
            finally:
                if collector:
                    collector.close()
            # Worker removes any unpublished/partially published files on failure.
