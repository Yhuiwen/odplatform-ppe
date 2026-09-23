# Phase 4B-0 Inference Runtime Freeze

Date: 2026-09-23

Status: **COMPLETE / EXECUTION NOT AUTHORIZED**

Phase 4A: COMPLETE

Phase 4B-0: COMPLETE

Phase 4B-1: WAITING

This record freezes the Phase 4 inference boundary for later implementation
and verification. It does not load the release checkpoint, execute inference,
download a model, modify the dataset, or change any training artifact.

## 1. Release checkpoint identity

| Field | Frozen value |
| --- | --- |
| Selection ID | SEL-001 |
| Experiment | EXP-001 |
| Model | YOLO11n Project-trained Model |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Epoch | 75, one-based |
| SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Size | 5,479,891 bytes |
| Dataset identity | `CSS-PPE-10-V1` |
| Mapping | `PPE-MAPPING-V1` |
| Model class order | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest`, `machinery`, `vehicle` |

The checkpoint must be checked against the path, size and SHA256 above before
any future Phase 4B execution. A mismatch must stop the run. The checkpoint
was not loaded during this freeze.

## 2. Runtime version

| Field | Frozen value |
| --- | --- |
| Runtime ID | `INF-RUNTIME-001` |
| Runtime role | Phase 3 evaluation reference runtime reused for Phase 4 implementation |
| OS / architecture | Windows x86_64 |
| Python | 3.10.4 |
| PyTorch | 2.5.1+cpu |
| torchvision | 0.20.1 |
| Ultralytics | 8.4.157 |
| NumPy | 2.2.6 |
| OpenCV | 5.0.0.93 |
| Pillow | 12.3.0 |
| CUDA | Not used |

This is a CPU reference runtime. It is intentionally separate from the Phase 2
AutoDL RTX 4090 training runtime and from the planned broad ranges in
`requirements.txt`. No GPU, CUDA or AutoDL runtime is frozen by Phase 4B-0.

The runtime is a logical freeze, not authorization to create, install or
modify an environment. Installation remains Phase 4B-1 work.

## 3. Dependency source

The exact dependency source is:

```text
locks/EVAL-001/requirements.txt
```

The Phase 3 evaluation report records the resolved runtime as Python 3.10.4,
PyTorch 2.5.1+cpu, torchvision 0.20.1, Ultralytics 8.4.157, NumPy 2.2.6 and
OpenCV 5.0.0.93. The lock file is the machine-readable source of truth for
installed package versions.

`requirements.txt` contains broad planned ranges and is not a valid substitute
for this freeze. Installation must not silently upgrade packages, install a
GPU wheel, or replace Ultralytics 8.4.157.

## 4. Device policy

```text
device: cpu
policy: cpu-only
automatic-device-switching: prohibited
CUDA: not authorized
```

The detector must use CPU for the frozen Phase 4B boundary. It must not
silently switch to CUDA, another device, or a different runtime when a GPU is
present. A later GPU runtime requires a new reviewed freeze and explicit
authorization.

CPU execution does not authorize a real-time performance claim. Camera/RTSP
latency and throughput remain unverified until Phase 4B integration tests.

## 5. Confidence threshold policy

| Parameter | Frozen value | Policy |
| --- | ---: | --- |
| `imgsz` | 640 | Fixed |
| `conf_threshold` | 0.25 | Operating/detection threshold |
| `iou_threshold` | 0.45 | NMS IoU threshold |
| `max_det` | 300 | Maximum detections per frame |
| `class_filter` | `[0, 1, 2, 3, 4]` | Five PPE classes for Phase 4 output |

The threshold is a fixed inference operating policy, not a new evaluation
metric and not a production safety acceptance threshold. Model classes
`machinery` and `vehicle` remain context classes and are outside the five-class
Phase 4 output filter.

Changing a threshold requires a new reviewed configuration change; it must not
be performed ad hoc during a run or tuned against the test set.

## 6. Input format policy

| Input | Accepted format |
| --- | --- |
| Image | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp` |
| Video | `.mp4`, `.avi`, `.mov`, `.mkv` |
| Camera | Explicit device index or camera URI |
| RTSP | `rtsp://` or `rtsps://` |

All sources resolve to the same input-adapter boundary and emit ordered frame
metadata plus source identity. Camera and RTSP must remain real source paths;
an unavailable source must fail observably and must not be replaced with a
local video or fabricated frame.

## 7. Output schema reference

The structured output contract is:

```text
core/schemas/detection.py
DetectionResult
```

Each result carries:

- `frame_id`
- `timestamp`
- `source`
- `class_id`
- `class_name`
- `confidence`
- `bbox`

`DetectionResult.to_dict()` is the JSON-serializable representation. A frame
returns `list[DetectionResult]`. Rendering and annotated-video formats remain
Phase 4B-1 implementation decisions and must preserve this schema.

## 8. Error handling policy

The implementation must fail closed:

| Condition | Required behavior |
| --- | --- |
| Missing checkpoint | Stop before frame processing |
| Checkpoint hash/size mismatch | Stop before frame processing |
| Missing runtime or package | Report `NOT READY`; do not substitute |
| Invalid device request | Stop; do not silently fall back |
| Unsupported input format | Return an explicit unsupported-source error |
| Image/video decode failure | Return an observable failure status |
| RTSP/Camera timeout or disconnect | Expose timeout/disconnect state |
| Model download attempt | Prohibited |
| Class mapping mismatch | Stop; do not remap silently |
| No detections | Valid empty result, not fabricated detections |

No silent frame skipping, source substitution, device substitution, model
substitution or fake success response is allowed.

## 9. Configuration boundary

`configs/inference.yaml` is updated to the frozen Phase 4B-0 configuration
contract. It is configuration only:

- `execution_enabled` remains `false`
- no inference logic is added
- no model is loaded
- no input source is opened
- no output directory is created

Phase 4B-1 may implement against this contract only after a later instruction
authorizes implementation. It must verify the runtime and checkpoint before
the first inference run.

## 10. Phase status

```text
Phase 4A: COMPLETE
Phase 4B-0: COMPLETE
Phase 4B-1: WAITING
Model loading: NOT RUN
Inference execution: NOT RUN
Dataset modification: NONE
Training artifact modification: NONE
```

This freeze grants no model execution, deployment or production-safety
acceptance authority.
