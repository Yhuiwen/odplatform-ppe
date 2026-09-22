# Data Source Evidence

> Evidence access date: 2026-09-21
>
> This document records source metadata and licensing evidence. Phase 1B
> downloaded the selected Roboflow API export with the user's account, copied
> it without modification into a Git-ignored snapshot, and recorded actual
> counts and hashes. No dataset image, label, archive, model weight, API key,
> or machine path is committed.

## CSS-V1

### Source A: Roboflow Universe Original Project

| Field | Evidence |
| --- | --- |
| URL | https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety |
| Provider | Roboflow Universe Projects |
| Hosting | Roboflow Universe |
| Accessed | 2026-09-21 |
| Evidence | Roboflow's public project page identifies `Construction Site Safety` as a public object-detection project. The selected frozen version is `27`, named `YOLOv8s`. |
| License | CC BY 4.0 |
| Dataset license evidence URL | https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety |
| Dataset license evidence | The Roboflow Construction Site Safety project page directly states `License: CC BY 4.0`. This page is the evidence that the dataset is offered under that license. |
| License legal terms URL | https://creativecommons.org/licenses/by/4.0/ |
| Reported size | Version 27: 2,801 images; 2,605 train, 114 valid, 82 test; 25 source classes. |
| Reported classes | `Person`, `Hardhat`, `NO-Hardhat`, `Safety Vest`, `NO-Safety Vest`, `Mask`, `NO-Mask`, `Gloves`, `Safety Cone`, `machinery`, `vehicle`, `Excavator`, `wheel loader`, `dump truck`, `truck and trailer`, `truck`, `semi`, `SUV`, `sedan`, `mini-van`, `van`, `bus`, `trailer`, `Ladder`, `fire hydrant`. |
| Source annotation task | Bounding-box object detection. |
| Selected export | Ultralytics YOLO / `yolov8`. |
| Target training framework | YOLO11. The selected `yolov8` export is a YOLO-format data representation; it is not the source annotation task and does not mean the dataset is annotated for YOLOv11. |
| Reported annotation count | UNVERIFIED / NOT FROZEN. The public version metadata exposes per-class box counts, but no direct single total-annotation-count field was found. |
| Download mechanism | Roboflow Universe web download as ZIP, or the Roboflow Python SDK/REST download flow with a local `ROBOFLOW_API_KEY`. The exact Phase 1B target is workspace `roboflow-universe-projects`, project `construction-site-safety`, version `27`, export format `yolov8`. |
| Trust level | PRIMARY / AUTHORITATIVE for source selection and version metadata. |

### Version 27 Metadata Evidence

The fields below were read from the selected version's public metadata shown for
the Roboflow Construction Site Safety project. The version entry point is:

https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety/dataset/27

Accessed: 2026-09-21.

| Field | Value | Direct public metadata field |
| --- | --- | --- |
| Version | 27 | version identifier |
| Version name | YOLOv8s | `name` |
| Created | 2023-01-10T14:21:19.209Z | `created` |
| Images | 2,801 | `images` |
| Train | 2,605 | `splits.train` |
| Valid | 114 | `splits.valid` |
| Test | 82 | `splits.test` |
| Classes | 25 | `classes` map keys |

Version 27 class counts:

| Original class name | Boxes reported in the class map |
| --- | ---: |
| Person | 1,227 |
| Hardhat | 899 |
| NO-Hardhat | 477 |
| Safety Vest | 453 |
| NO-Safety Vest | 629 |
| Mask | 207 |
| NO-Mask | 552 |
| Gloves | 306 |
| Safety Cone | 600 |
| machinery | 45 |
| vehicle | 122 |
| Excavator | 166 |
| wheel loader | 127 |
| dump truck | 157 |
| truck and trailer | 7 |
| truck | 35 |
| semi | 7 |
| SUV | 16 |
| sedan | 54 |
| mini-van | 7 |
| van | 28 |
| bus | 1 |
| trailer | 15 |
| Ladder | 58 |
| fire hydrant | 6 |

The sum of the per-class map values is a derived number, not a direct total
annotation-count field. It must not be frozen as an authoritative dataset
statistic.

The frozen version includes preprocessing and augmentation configuration. Phase
1D must therefore test for duplicated or near-duplicated images before the
final dataset freeze.

### Source B: Kaggle Mirror

| Field | Evidence |
| --- | --- |
| URL | https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow |
| Provider | Snehil Sanyal |
| Hosting | Kaggle |
| Accessed | 2026-09-21 |
| Evidence | The public page identifies the original Roboflow project and describes a YOLO-format mirror with `metadata.csv` and `count.csv`. |
| License | Attribution 4.0 International (CC BY 4.0) |
| Dataset license evidence URL | https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow |
| Dataset license evidence | The Kaggle dataset page and dataset API metadata state `Attribution 4.0 International (CC BY 4.0)`. This is secondary mirror evidence only. |
| License legal terms URL | https://creativecommons.org/licenses/by/4.0/ |
| Reported size | No authoritative image count was exposed by the mirror metadata inspected in this phase. The mirror version is `3`, last updated 2023-02-23. |
| Reported classes | Ten exported classes: `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`, `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`, `vehicle`. |
| Source annotation task | Object detection; the mirror reports YOLO `.txt` labels plus `metadata.csv` and `count.csv`. |
| Download mechanism | Kaggle dataset download. This is not selected for V1 because its exact relationship to a frozen Roboflow version has not been proven. |
| Trust level | SECONDARY / MIRROR only. |

### Secondary Reference

The public README for `Nduka99/ppe_compliance_detection` reports CSS as
2,801 images with ten classes and describes a ten-to-five class reduction. This
is third-party evidence only and is not used to override the original source
record.

## Conflicts

| Conflict | Observed evidence | Resolution |
| --- | --- | --- |
| Roboflow version count drift | Version 27 has 2,801 images and 25 classes. Version 30 has 717 images and 26 classes. The current parent project record also exposes 3,033 total images, 717 annotated images, and 193 unannotated images. | Freeze version 27 for V1. Do not use a moving project-level count. |
| Mirror class definition | Kaggle reports ten exported classes, while Roboflow version 27 reports 25 source classes. | Use the original Roboflow version 27 class record as authoritative. Kaggle is excluded from the V1 download path. |
| Mirror image count | Kaggle's inspected metadata does not expose an authoritative image count; a third-party README reports 2,801. | Do not infer a bit-for-bit mirror relationship. Verify the downloaded version 27 archive during Phase 1B. |
| Downloaded v27 export counts | The public version metadata reports 2,801 images and 25 classes. The direct Roboflow API `yolov8` export contains 2,799 images and a 10-class `data.yaml`. | Preserve the direct export unchanged, record both observations, and block P1B until the discrepancy is resolved against the canonical v27 source. Do not edit the snapshot to match the metadata. |
| Kaggle version number | Kaggle labels its dataset version `3`; Roboflow version 27 is selected. These version numbers are from different systems and are not equivalent. | Record both identifiers and never equate them. |
| Underlying image provenance | The project is labeled CC BY 4.0, but the source and privacy status of every underlying image are not independently documented. | Use the licensed source for course/development work, retain attribution and modification notices, keep raw data outside Git, and reassess before any public redistribution. |

Conflict status: RESOLVED FOR V1 SOURCE SELECTION.

The mirror-correspondence question remains intentionally unresolved, but it is
not a blocker because the mirror is not part of the selected reproducible
download path.

## License Legal Terms

Evidence URL:
https://creativecommons.org/licenses/by/4.0/

This URL provides the legal terms for CC BY 4.0. By itself, it does not prove
that any particular dataset uses CC BY 4.0. The dataset-license evidence for
CSS-V1 is the Roboflow Construction Site Safety project page identified above.

Recorded terms:

- Share: copy and redistribute the material in any medium or format, for any
  purpose, including commercially.
- Adapt: remix, transform, and build upon the material, for any purpose,
  including commercially.
- Attribution: give appropriate credit, link the license, and indicate whether
  changes were made.
- No endorsement: attribution must not suggest that the licensor endorses the
  project or its use.
- No additional restrictions: do not impose legal or technological
  restrictions that prevent others from exercising the licensed rights.
- Notice: the license does not clear unrelated publicity, privacy, or moral
  rights.

Research and education use are not separately restricted by CC BY 4.0 beyond
the attribution and notice conditions.

## Decision

The historical CSS-V1 decision selected Roboflow Universe version 27 as the
intended V1 source. The P1B identity audit found that version metadata and the
materialized export artifact are not interchangeable identities, so the freeze
is blocked pending correction. The Kaggle mirror remains evidence of an
accessible redistribution, not a reproducibility baseline.

## Phase 1B Download Record

- Dataset ID: `CSS-V1`
- Dataset: Construction Site Safety
- Workspace: `roboflow-universe-projects`
- Project: `construction-site-safety`
- Version: `27`
- Format: `yolov8`
- Download method: Roboflow API with the user's account
- Dataset extracted directory: `Construction-Site-Safety-27`
- Archive: unavailable because the Roboflow API returned an extracted
  directory; no archive SHA-256 may be claimed
- Snapshot location: Git-ignored `data/external/css-v27-yolov8/source/`
- Source data.yaml SHA-256:
  `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`
- Snapshot manifest SHA-256:
  `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795`
- Manifest files: `5,601`
- Actual counts: train `2,603`, valid `114`, test `82`, total `2,799`
- Frozen expected counts: train `2,605`, valid `114`, test `82`, total `2,801`
- Count result: FAIL, train and total are each two images below expectation
- Actual classes: `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`,
  `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`,
  `vehicle`
- Class-count result: FAIL against the P1A-reported 25 source classes
- Required semantics: PASS; all five target semantics are present
- Pair/integrity result: zero missing labels, zero orphan labels, 23 empty
  label files, zero zero-byte images
- Exact SHA-256 duplicate files: 22, retained without deletion
- Machine path recorded: NO
- Secret saved: NO
- Snapshot status: `IMMUTABLE`
- Validation status: `FAILED - EXPECTED COUNT OR CLASS MISMATCH`

Required follow-up: resolve the count and exported-class discrepancy against
the canonical version 27 source before P1C starts. Do not modify the snapshot
to force a match.

## P1B.1 Identity Audit

- Observed artifact:
  - Class count: `10`
  - Classes: `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`,
    `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`,
    `vehicle`
  - Images: `2,799`
  - Splits: train `2,603`, valid `114`, test `82`
  - `data.yaml` SHA256:
    `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`
- Expected metadata:
  - Class count: `25`
  - Images: `2,801`
  - Splits: train `2,605`, valid `114`, test `82`
- The materialized export identifies workspace `roboflow-universe-projects`,
  project `construction-site-safety`, and version `27`; the generated README
  also identifies v27 and provides a generation timestamp consistent with the
  version creation timestamp.
- The actual 10 classes are a subset of the 25 metadata classes. The artifact
  is internally consistent: class IDs `0` through `9` are used and no invalid
  class IDs were found.
- Root cause: `CONFIRMED: export artifact mismatch`.
- Exact Roboflow internal reason: `UNKNOWN`; an authenticated API re-query was
  unavailable because no user credential was configured during this audit.

## P1B.3 Final Freeze Decision

- Rejected dataset identity: `CSS-V1`
- Accepted candidate: `CSS-V1.1 Candidate`
- Frozen dataset ID: `CSS-PPE-10-V1`
- Decision record: `docs/12_DATASET_FREEZE_DECISION.md`
- Frozen workspace: `roboflow-universe-projects`
- Frozen project: `construction-site-safety`
- Frozen version: `27`
- Frozen format: `yolov8`
- Frozen `data.yaml` SHA256:
  `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`
- Frozen manifest SHA256:
  `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795`
- Frozen classes: `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`,
  `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`,
  `vehicle`
- Frozen counts: train `2603`, valid `114`, test `82`, total `2799`
- P1C input remains the immutable Git-ignored
  `data/external/css-v27-yolov8/source/` snapshot.
- No dataset file was modified while recording this decision.

## Verification Status

`SOURCE VERIFIED` for the canonical Roboflow source, dataset license evidence,
version metadata, source class names, reported size, split, and download
mechanism.

`SNAPSHOT CREATED`: the direct API export is preserved as an immutable,
Git-ignored source snapshot with a full manifest and reproducible integrity
checks.

`BLOCKED / NEEDS FREEZE CORRECTION`: the historical CSS-V1 metadata and the
materialized export artifact have different identities. `CSS-V1.1 Candidate`
is now recorded as promoted to the frozen `CSS-PPE-10-V1` identity by ADR-012;
P1C remains not started until manual review.
