# Open Source Usage

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
