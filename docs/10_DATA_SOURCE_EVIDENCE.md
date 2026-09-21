# Data Source Evidence

> Evidence access date: 2026-09-21
>
> This document records source metadata and licensing evidence only. No dataset
> archive, image set, label set, model weight, or generated export was
> downloaded for this phase.

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

CSS-V1 will use Roboflow Universe version 27 as the canonical V1 source. Phase
1B must download that exact version through the Roboflow Universe download
mechanism with a local API key and record the resulting archive hash. The
Kaggle mirror is evidence of an accessible redistribution, not a reproducibility
baseline.

## Verification Status

`SOURCE VERIFIED` for the canonical Roboflow source, dataset license evidence,
version metadata, source class names, reported size, split, and download
mechanism.

`NOT DOWNLOADED`: this phase did not retrieve the dataset or any export.
