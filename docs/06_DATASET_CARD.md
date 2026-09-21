# Dataset Card

> Phase 1A status: SOURCE VERIFIED / NOT DOWNLOADED
>
> Source metadata is recorded from direct public evidence. The dataset itself
> has not been downloaded, converted, or validated locally.

## V1 Primary Dataset: Construction Site Safety (CSS)

| Field | Value |
| --- | --- |
| Dataset ID | CSS-V1 |
| Dataset Name | Construction Site Safety (CSS) |
| Source | Roboflow Universe original project |
| Publisher | Roboflow Universe Projects |
| Hosting | Roboflow Universe |
| Source URL | https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety |
| Download URL / entry point | https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety/dataset/27 |
| License | Attribution 4.0 International (CC BY 4.0) |
| Dataset license evidence URL | https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety |
| Dataset license evidence | YES: the Roboflow Construction Site Safety project page directly states `License: CC BY 4.0`. |
| License legal terms URL | https://creativecommons.org/licenses/by/4.0/ |
| License Verified | YES: dataset license evidence is separated from the Creative Commons legal terms and both were inspected. |
| Redistribution | Allowed under CC BY 4.0 with attribution, license link, change indication, and no endorsement. Raw data is not committed to this repository. |
| Attribution | Required: credit Roboflow Universe Projects and the Construction Site Safety project; link the license. |
| Download Date | NOT DOWNLOADED |
| Version | Roboflow version 27 (`YOLOv8s`), created 2023-01-10 |
| Original Classes | 25 source classes: `Person`, `Hardhat`, `NO-Hardhat`, `Safety Vest`, `NO-Safety Vest`, `Mask`, `NO-Mask`, `Gloves`, `Safety Cone`, `machinery`, `vehicle`, `Excavator`, `wheel loader`, `dump truck`, `truck and trailer`, `truck`, `semi`, `SUV`, `sedan`, `mini-van`, `van`, `bus`, `trailer`, `Ladder`, `fire hydrant` |
| Selected Classes | person, hardhat, no_hardhat, vest, no_vest |
| Source Annotation Task | Bounding-box object detection |
| Selected Export | Ultralytics YOLO / `yolov8` |
| Target Training Framework | YOLO11 |
| Conversion | Planned: source format -> YOLO format with locked class mapping |
| Reported Image Count | 2,801, reported by Roboflow version 27 source metadata |
| Reported Annotation Count | UNVERIFIED / NOT FROZEN |
| Reported Split | train 2,605 / valid 114 / test 82 |
| Download Method | Roboflow Universe web ZIP or Python SDK/REST download using workspace `roboflow-universe-projects`, project `construction-site-safety`, version `27`, format `yolov8`, and a local `ROBOFLOW_API_KEY`. |
| Downloaded | NO |
| Local Dataset Hash | NOT AVAILABLE — NOT DOWNLOADED |
| Known Problems | Version drift, mirror mismatch, augmentation/near-duplicate risk, source-image provenance, ten-to-five class reduction, and split leakage require Phase 1 validation. |

## Source Count Reconciliation

- Reported by Source A, Roboflow version 27: 2,801 images, 2,605/114/82 split,
  25 classes.
- Reported by Source A, Roboflow version 30: 717 images, 521/114/82 split,
  26 classes.
- Reported by Source A, current project-level record: 3,033 total images,
  717 annotated images, 193 unannotated images.
- Reported by Source B, Kaggle mirror: ten exported classes; no authoritative
  image count was exposed by the metadata inspected in this phase.
- Reported by a third-party project README: 2,801 images and ten classes; this
  is secondary evidence only.

The V1 baseline is frozen to Roboflow version 27. Moving project-level counts
and the Kaggle mirror must not be substituted for that version.

Per-class box counts are available from the source class map, but no direct
single total-annotation-count field was found. The dataset card therefore keeps
Reported Annotation Count as `UNVERIFIED / NOT FROZEN`.

## CSS-V1 Category Semantics

The source contains classes semantically corresponding to all five locked V1
targets. This phase does not perform or approve the mapping itself:

| Locked V1 class | Matching original source class name |
| --- | --- |
| person | Person |
| hardhat | Hardhat |
| no_hardhat | NO-Hardhat |
| vest | Safety Vest |
| no_vest | NO-Safety Vest |

All remaining source classes are outside the V1 five-class output and must be
handled explicitly in Phase 1C without renaming source labels in this document.

## Locked V1 Class Mapping

| ID | Class |
| --- | --- |
| 0 | person |
| 1 | hardhat |
| 2 | no_hardhat |
| 3 | vest |
| 4 | no_vest |

## Future Augmentation Sources

### SHWD

- Purpose: Helmet / No Helmet 补强
- Status: PLANNED / NOT DOWNLOADED
- License, URL, version, classes, and counts: TO VERIFY IN LATER DATA WORK

### Construction-PPE

- Purpose: future Gloves, Boots, Goggles, and other PPE extensions
- Status: PLANNED / NOT DOWNLOADED
- License, URL, version, classes, and counts: TO VERIFY IN LATER DATA WORK

## Safety Harness

本阶段没有可靠主数据源。Safety Harness 属于 Extension E-004，不进入 V1
MUST，也不占用本阶段五个主类别。

## Phase 1 Required Evidence

Phase 1B must download only the selected Roboflow version and record archive
retrieval, license attribution, checksum, conversion, duplicate analysis, split
manifest, and quality report locations.
