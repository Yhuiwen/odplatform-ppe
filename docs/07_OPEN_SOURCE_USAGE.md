# Open Source Usage

## V1.2-B offline upload dependencies (2026-10-09)

The separate V1.2 API environment installs `python-multipart==0.0.32` (Apache-2.0) for FastAPI multipart parsing and `Pillow==12.3.0` (MIT-CMU) for image validation. Both license identifiers were checked from installed package metadata. They are used as package-manager dependencies; no source was copied. Exact direct versions are recorded in `locks/frontend-v1.2-api/requirements.txt`. `ffprobe` is invoked as a local external tool for MP4 inspection; no FFmpeg code was copied into the repository.

## Phase 9 Overview reference (2026-10-07)

The [Worksite Safety Monitor](https://github.com/worksite-safety/worksite-safety-monitor)
repository was consulted in REFERENCE mode for its general charts plus event
grid dashboard structure. Its repository states AGPL-3.0-or-later and provides
a [license file](https://github.com/worksite-safety/worksite-safety-monitor/blob/main/LICENSE).
No source code, styles, data, images or assets were copied. The implementation
uses the project's existing Streamlit components, Altair charting and persisted
event repository. Existing VoxDroid and SiteGuard references remain as recorded
below.

## Realtime CPU backend (2026-10-07)

OpenVINO 2025.2.0 is installed as a pinned package-manager dependency for the
user-authorized realtime CPU profile (ADR-025). It executes an export of this
project's frozen YOLO11 checkpoint through Ultralytics' public export/predict
APIs. No OpenVINO source or third-party business code was copied. The local
derived graph is ignored by Git and can be regenerated with
`scripts/export_cpu_openvino.py`. Upstream documentation:
https://docs.openvino.ai/2025/get-started/install-openvino/install-openvino-pip.html
and https://docs.ultralytics.com/integrations/openvino/ . Distribution must
continue to honor the existing Ultralytics AGPL-3.0 review boundary.

## Usage Modes

| Mode | Meaning |
| --- | --- |
| DEPENDENCY | Install and use through a package manager; do not copy source into this project. |
| REFERENCE | Read designs or algorithm ideas, then implement independently. |
| SELECTIVE-REUSE | Reuse a small, clearly identified portion only when the inspected license permits it and provenance is recorded. |

## Phase 0 Verification

Verified on 2026-09-21 by reading each repository's raw license file at the
current default-branch HEAD and recording the commit. Repository API metadata
was not trusted as a substitute for the raw license text.

| Repository | Commit / Version | License | Usage Mode | Used Module | Copied Code? | Modification? | Attribution Required? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| https://github.com/ultralytics/ultralytics | `00be77811a04be36bb7cc00b97b9d99b6bb2b42e` | AGPL-3.0 (`LICENSE`, verified text) | DEPENDENCY + REFERENCE | YOLO11 Train/Val/Predict/Track/ByteTrack integration/Export | NO | NO | YES, follow AGPL-3.0 obligations | Do not copy the package source. Review distribution obligations before delivery. |
| https://github.com/Nduka99/ppe_compliance_detection | `0e690755ba822fc690e55f07f7644623a0284805` | TO VERIFY: no `LICENSE`, `LICENSE.md`, or `LICENSE.txt` found at repository root | REFERENCE | CSS/SHWD/Pictor-PPE fusion, class mapping, MD5/perceptual deduplication, quality filtering, baseline experiments | NO | NO | TO VERIFY | Treat as no-reuse until a license is found and reviewed. Independently implement ideas. |
| https://github.com/VoxDroid/Construction-Site-Safety-PPE-Detection | `9f4c9cf401806dcdd0e16fd7491f179f64e5b3a4` | MIT (`LICENSE`, verified text; Copyright 2025 Izeno) | REFERENCE | Camera flow, detection display, PPE dashboard, demo organization | NO | NO | NO for reference; preserve notice if SELECTIVE-REUSE is later approved | Do not copy the Flask system or YOLOv8 project structure. |
| https://github.com/FoundationVision/ByteTrack | `d1bf0191adff59bc8fcfeaa0b33d3d1642552a99` | MIT (`LICENSE`, verified text; Copyright 2021 Yifu Zhang) | REFERENCE | ByteTrack design and behavior | NO | NO | NO for reference; preserve notice if SELECTIVE-REUSE is later approved | Use through the mature Ultralytics integration instead of copying source. |
| https://github.com/C-Nekopedia/SiteGuard | `1fb67f1aaef4d4458e966ebaea0874ce9c17bf86` | MIT (`LICENSE`, verified text; Copyright 2026 C-Nekopedia) | REFERENCE ONLY | DetectionService, risk rules, risk levels, service boundaries | NO | NO | NO for reference; preserve notice if SELECTIVE-REUSE is later approved | Do not copy the complete business architecture. |

## Phase 0 Declaration

Copied third-party business code: NO.

No third-party source file was copied into `odplatform-ppe`. All business
boundaries in this repository are original placeholders and schemas created for
Phase 0.

## Reuse Procedure

Before any SELECTIVE-REUSE:

1. Re-check the exact upstream commit and license.
2. Confirm the intended file is covered by that license.
3. Record origin, commit, file path, modifications, and required attribution.
4. Add a focused test and update this document before merge.
5. Obtain explicit user approval when the license or obligation is ambiguous.

## Phase 3 Evaluation Dependency Use

EVAL-001 uses Ultralytics 8.4.157 through its public prediction API, PyTorch
2.5.1 CPU / torchvision 0.20.1, NumPy 2.2.6, Pillow and Matplotlib in a separate
Windows environment. Exact installed versions are pinned in
`locks/EVAL-001/requirements.txt`; EXP-001 training locks remain unchanged.
The installed Ultralytics matching/AP source was inspected and used as a runtime
reference check; no third-party business source was copied. The repository's
metric and error-analysis implementation is original and tested against that API.
Existing dependency-license and distribution boundaries remain in force.
## V1.1 frontend/API dependencies (2026-10-08)

The new local interface uses npm packages Vue 3, Vite, Vue Router, Pinia, Element Plus and Icons Vue, Axios, Sass, Vitest (MIT per installed package metadata), and Apache ECharts (Apache-2.0 per installed package metadata). Python API packages are FastAPI, Starlette, Uvicorn and HTTPX. The project imports these packages through normal package managers; it does not copy their source or bundle design screenshots. Exact resolved JavaScript versions are in `front/package-lock.json`; independently pinned API packages are in `locks/frontend-v1.1-api/requirements.txt`. Retain upstream notices and review licenses before redistribution of bundled binaries.

## V1.2-D system FFmpeg use (2026-10-09)

Uses the already installed FFmpeg/ffprobe 8.1.2 Gyan full build as a subprocess dependency, including libx264. No upstream business source or binary was copied into the repository, no new package/model was downloaded. Local `ffmpeg -L` reports GNU GPL and the build has `--enable-gpl --enable-version3`; do not treat this binary as an unrestricted bundled redistributable. Runtime requires an independently installed compatible FFmpeg with actual libx264 encoding self-test. Existing Ultralytics/PyTorch/OpenCV license boundaries and frozen Python/npm locks remain unchanged. H.264 CRF18 is lossy; byte-identical image preservation is not claimed.
