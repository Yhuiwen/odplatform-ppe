"""One-image offline processor using the frozen detector and frame renderer."""
from __future__ import annotations

import hashlib
import json
import os
import time
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from core.inference.detector import CheckpointIntegrityError, InferenceError, InferenceRuntimeError
from core.rendering.annotated_frame import AnnotatedFrameRenderer
from core.schemas.video import FrameData
from offline.jobs import JobError, OfflineSettings, sha256_file
from offline.media import clean_filename
from services.inference_service import InferenceService


OUTPUTS = ("annotated.png", "detections.json", "summary.json", "results.zip")


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _write_synced(path: Path, payload: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


class ImageProcessor:
    def __init__(self, settings: OfflineSettings, *, inference: InferenceService | None = None, config_path: Path | None = None):
        self.settings = settings
        self.config_path = config_path or Path("configs/inference.yaml")
        self.inference = inference or InferenceService(config_path=self.config_path, execution_enabled=True)
        self.detector = self.inference.detector
        self.renderer = AnnotatedFrameRenderer(self.detector.class_names)
        self.config_sha256 = sha256_file(self.config_path)

    def preflight(self) -> tuple[bool, str | None]:
        if self.settings.image_config_sha256 and self.config_sha256 != self.settings.image_config_sha256:
            return False, "冻结推理配置指纹不符"
        model = self.detector.model_path
        if not model.is_file():
            return False, "冻结模型文件缺失"
        if model.stat().st_size != self.detector.expected_model_size or sha256_file(model) != self.detector.expected_model_sha256:
            return False, "冻结模型指纹不符"
        return True, None

    @staticmethod
    def _checkpoint(context, stage: str):
        if context.cancelled():
            raise JobError("JOB_CANCELLED", f"图片处理在{stage}检查点取消")

    def _decode(self, source: Path):
        try:
            with Image.open(source) as original:
                raw_width, raw_height = original.size
                if raw_width <= 0 or raw_height <= 0 or raw_width * raw_height > self.settings.max_pixels:
                    raise JobError("PIXEL_LIMIT", "原始图片像素尺寸超过限制", 413)
                orientation = int(original.getexif().get(274, 1))
                if orientation not in range(1, 9):
                    raise JobError("INVALID_EXIF", "图片 EXIF 方向无效", 422)
                with ImageOps.exif_transpose(original) as oriented:
                    width, height = oriented.size
                    if width <= 0 or height <= 0 or width * height > self.settings.max_pixels:
                        raise JobError("PIXEL_LIMIT", "标准化图片像素尺寸超过限制", 413)
                    # Deterministic alpha policy: composite onto white in RGB.
                    if "A" in oriented.getbands() or "transparency" in oriented.info:
                        rgba = oriented.convert("RGBA")
                        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                        rgb = Image.alpha_composite(background, rgba).convert("RGB")
                        alpha_policy = "white_background"
                    else:
                        rgb = oriented.convert("RGB")
                        alpha_policy = "not_applicable"
                    import cv2
                    import numpy as np
                    bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
                    return bgr, {"encoded_width":raw_width,"encoded_height":raw_height,"exif_orientation":orientation,
                                 "normalized_width":width,"normalized_height":height,"alpha_policy":alpha_policy}
        except JobError:
            raise
        except (OSError, ValueError, ImportError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise JobError("INVALID_MEDIA", "图片解码失败", 422) from exc

    def __call__(self, context) -> dict[str, dict]:
        started = time.monotonic()
        job_id = context.job["job_id"]
        if context.job["media_type"] != "image":
            raise JobError("UNSUPPORTED_PROCESSOR", "当前处理器仅支持图片")
        if self.settings.image_config_sha256 and sha256_file(self.config_path) != self.settings.image_config_sha256:
            raise JobError("CONFIG_INTEGRITY_FAILED", "冻结推理配置指纹不符")
        suffix, _, _ = clean_filename(context.job["original_filename"])
        source = context.storage.path(job_id, "input", "source" + suffix)
        if not source.is_file() or source.stat().st_size != context.job["input_size_bytes"] or sha256_file(source) != context.job["input_sha256"]:
            raise JobError("INPUT_CORRUPT", "输入图片完整性校验失败")
        self._checkpoint(context, "解码前")
        context.progress(0, 1)
        bgr, image_info = self._decode(source)
        self._checkpoint(context, "推理前")
        frame = FrameData(frame_id=0, timestamp=0.0, image=bgr)
        inference_started = time.monotonic()
        source_id = f"offline:image:{job_id}"
        try:
            detections = self.inference.infer_frame(frame, source=source_id)
        except CheckpointIntegrityError as exc:
            raise JobError("MODEL_INTEGRITY_FAILED", "冻结模型缺失或指纹不符") from exc
        except InferenceRuntimeError as exc:
            raise JobError("MODEL_RUNTIME_UNAVAILABLE", "冻结推理运行环境不可用") from exc
        except InferenceError as exc:
            raise JobError("MODEL_INFERENCE_FAILED", "图片推理失败") from exc
        inference_seconds = round(time.monotonic() - inference_started, 6)
        if any(item.frame_id != frame.frame_id or item.timestamp != frame.timestamp or item.source != source_id for item in detections):
            raise JobError("INVALID_DETECTION_CONTEXT", "图片推理结果不属于当前输入")
        self._checkpoint(context, "推理后")
        height, width = bgr.shape[:2]
        plan = self.renderer.annotation_plan(detections, width=width, height=height)
        if len(plan) != len(detections):
            raise JobError("INVALID_DETECTION_BOX", "检测框超出图片范围或退化")
        rows = []
        for detection, annotation in zip(detections, plan):
            rows.append({"class_id": detection.class_id, "class_name": detection.class_name,
                         "confidence": detection.confidence, "bbox_xyxy": list(annotation.bbox),
                         "raw_bbox_xyxy": list(detection.bbox.as_tuple())})
        counts = Counter(row["class_name"] for row in rows)
        candidates = [dict(item, candidate_type="SUSPECTED_NO_HELMET" if item["class_name"] == "no_hardhat" else "SUSPECTED_NO_VEST")
                      for item in rows if item["class_name"] in {"no_hardhat", "no_vest"}]
        self._checkpoint(context, "标注前")
        annotated = self.renderer.render(frame, detections)
        if tuple(annotated.shape[:2]) != (height, width):
            raise JobError("OUTPUT_DIMENSIONS", "标注图片尺寸与标准化输入不一致")
        import cv2
        encoded_ok, encoded = cv2.imencode(".png", annotated)
        if not encoded_ok:
            raise JobError("OUTPUT_ENCODE_FAILED", "标注 PNG 编码失败")
        unfiltered = []
        loaded_model = getattr(self.detector, "_model", None)
        names = getattr(loaded_model, "names", None)
        if isinstance(names, dict):
            unfiltered = [{"class_id": int(index), "class_name": str(name), "status": "NOT_EVALUATED"}
                          for index, name in names.items() if int(index) not in self.detector.class_filter]
        elif isinstance(names, (list, tuple)):
            unfiltered = [{"class_id": index, "class_name": str(name), "status": "NOT_EVALUATED"}
                          for index, name in enumerate(names) if index not in self.detector.class_filter]
        detection_doc = {"schema_version":"offline-image-detections-v1", "job_id":job_id,
                         "image_width":width,"image_height":height,"coordinate_system":"exif_normalized_display_pixels",
                         "model_runtime_id":self.detector.runtime_id,"model_sha256":self.detector.expected_model_sha256,
                         "config_sha256":self.config_sha256,"detections":rows}
        elapsed = round(time.monotonic() - started, 6)
        summary = {"schema_version":"offline-image-summary-v1","job_id":job_id,"input_mime":context.job["input_mime"],
                   "input_sha256":context.job["input_sha256"],"image":image_info | {"output_width":width,"output_height":height},
                   "model_runtime_id":self.detector.runtime_id,"model_sha256":self.detector.expected_model_sha256,
                   "config_sha256":self.config_sha256,"detection_count":len(rows),
                   "class_counts":{name:counts[name] for name in self.detector.class_names},
                   "not_evaluated_classes":unfiltered,"candidate_count":len(candidates),
                   "candidates":candidates,"candidate_policy":"single_frame_detection_items_not_confirmed_events",
                   "inference_seconds":inference_seconds,"inference_scope":"infer_frame_including_lazy_model_load_if_needed",
                   "processing_seconds":elapsed,"processing_scope":"decode_inference_annotation_before_artifact_publish"}
        payloads = {"annotated.png":encoded.tobytes(),"detections.json":_json_bytes(detection_doc),"summary.json":_json_bytes(summary)}
        try:
            for filename, payload in payloads.items():
                self._checkpoint(context, "写入产物前")
                _write_synced(context.storage.path(job_id, "staging", filename), payload)
            archive_path = context.storage.path(job_id, "staging", "results.zip")
            with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
                for filename, payload in payloads.items():
                    archive.writestr(filename, payload)
            self._verify_staging(context, payloads, width, height)
            self._checkpoint(context, "发布前")
            if sha256_file(source) != context.job["input_sha256"]:
                raise JobError("INPUT_CORRUPT", "处理期间输入图片被修改")
            manifest = {}
            for filename in OUTPUTS:
                self._checkpoint(context, "发布中")
                key = filename.split(".")[0]
                staged = context.storage.path(job_id, "staging", filename)
                manifest[key] = context.publisher.publish(job_id, key, filename, sha256_file(staged))
            context.storage.verify_manifest(job_id, manifest)
            self._checkpoint(context, "完成前")
            if context.record_result is None:
                raise JobError("RESULT_CONTRACT_MISSING", "图片统计登记接口不可用")
            context.record_result(len(rows), len(candidates), round(time.monotonic() - started, 6))
            context.progress(1, 1)
            return manifest
        except Exception:
            for filename in OUTPUTS:
                context.storage.path(job_id, "staging", filename).unlink(missing_ok=True)
                context.storage.path(job_id, "output", filename).unlink(missing_ok=True)
            raise

    @staticmethod
    def _verify_staging(context, payloads: dict[str, bytes], width: int, height: int):
        from PIL import Image
        for filename, payload in payloads.items():
            path = context.storage.path(context.job["job_id"], "staging", filename)
            if sha256_file(path) != hashlib.sha256(payload).hexdigest():
                raise JobError("ARTIFACT_CORRUPT", "暂存产物内容校验失败")
        image_path = context.storage.path(context.job["job_id"], "staging", "annotated.png")
        with Image.open(image_path) as image:
            if image.size != (width, height) or image.format != "PNG":
                raise JobError("OUTPUT_DIMENSIONS", "标注 PNG 无法按原尺寸解码")
            image.load()
        detections = json.loads(payloads["detections.json"])
        summary = json.loads(payloads["summary.json"])
        if (len(detections["detections"]) != summary["detection_count"]
                or sum(summary["class_counts"].values()) != summary["detection_count"]
                or len(summary["candidates"]) != summary["candidate_count"]):
            raise JobError("RESULT_INCOMPLETE", "检测结果与统计不一致")
        archive_path = context.storage.path(context.job["job_id"], "staging", "results.zip")
        with zipfile.ZipFile(archive_path) as archive:
            if set(archive.namelist()) != set(payloads) or archive.testzip() is not None:
                raise JobError("ZIP_INVALID", "结果压缩包校验失败")
            for name, payload in payloads.items():
                if archive.read(name) != payload or Path(name).name != name:
                    raise JobError("ZIP_INVALID", "压缩包内容与产物不一致")
