# Dataset Card

> V1 dataset status: FROZEN — CSS-PPE-10-V1
>
> Source metadata is recorded from direct public evidence. A Roboflow API
> export was downloaded with the user's account, copied without modification
> into the Git-ignored external snapshot, and hashed. The artifact audit found
> that version metadata and the materialized export do not identify the same
> artifact. The materialized export was subsequently accepted and frozen as
> `CSS-PPE-10-V1`. The historical CSS-V1 record remains for audit.

## CSS-PPE-10-V1 — Frozen V1 Dataset

| Field | Value |
| --- | --- |
| Dataset ID | CSS-PPE-10-V1 |
| Status | FROZEN |
| Source | Roboflow Universe |
| Workspace | `roboflow-universe-projects` |
| Project | `construction-site-safety` |
| Version | `27` |
| Export | `yolov8` |
| Artifact type | Generated Roboflow export, not raw capture |
| `data.yaml` SHA256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Manifest SHA256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| Classes | `10` |
| Class list | `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`, `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`, `vehicle` |
| Actual images | `2799` |
| Split counts | train `2603` / valid `114` / test `82` |
| Locked V1 output classes | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest` |
| Frozen training classes | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest`, `machinery`, `vehicle` |
| Class mapping decision | Strategy C, frozen by ADR-014 and `docs/14_CLASS_MAPPING_DECISION.md` |
| License | CC BY 4.0 with the evidence and legal terms recorded below |
| P1C input | Git-ignored `data/external/css-v27-yolov8/source/` |
| Decision record | `docs/12_DATASET_FREEZE_DECISION.md` |
| P1C-2 output | Git-ignored `data/processed/css-ppe-10-v1/` |
| Processed status | GENERATED / P1C-2 PASS / P1D-1 QUALITY ASSESSED |
| Processed class count | `7` |
| Processed split counts | train `2603` / valid `114` / test `82`; total `2799` |
| Processed boxes | `30375` retained / `8460` discarded from `38835` source boxes |

The frozen input must remain immutable. Phase 1C may consume it but must not
edit it or write transformed output back into `source/`.

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
| Download Date | 2026-09-21 |
| Phase 1B Status | BLOCKED / NEEDS FREEZE CORRECTION |
| Version | Roboflow version 27 (`YOLOv8s`), created 2023-01-10 |
| P1A Reported Source Classes | 25 classes reported by the version metadata: `Person`, `Hardhat`, `NO-Hardhat`, `Safety Vest`, `NO-Safety Vest`, `Mask`, `NO-Mask`, `Gloves`, `Safety Cone`, `machinery`, `vehicle`, `Excavator`, `wheel loader`, `dump truck`, `truck and trailer`, `truck`, `semi`, `SUV`, `sedan`, `mini-van`, `van`, `bus`, `trailer`, `Ladder`, `fire hydrant` |
| Actual Export Classes | 10 classes from `source/data.yaml`: `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`, `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`, `vehicle` |
| Selected Classes | person, hardhat, no_hardhat, vest, no_vest |
| Source Annotation Task | Bounding-box object detection |
| Selected Export | Ultralytics YOLO / `yolov8` |
| Target Training Framework | YOLO11 |
| Conversion | Implemented by `services/dataset_conversion_service.py`; source format -> YOLO format with the frozen `PPE-MAPPING-V1` mapping |
| Reported Image Count | 2,801, reported by Roboflow version 27 source metadata |
| Reported Annotation Count | UNVERIFIED / NOT FROZEN |
| Reported Split | train 2,605 / valid 114 / test 82 |
| Download Method | Roboflow Universe web ZIP or Python SDK/REST download using workspace `roboflow-universe-projects`, project `construction-site-safety`, version `27`, format `yolov8`, and a local `ROBOFLOW_API_KEY`. |
| Downloaded | YES — Roboflow API returned an extracted directory; no archive was produced. |
| Actual Image Count | 2,799: train 2,603 / valid 114 / test 82 |
| Local Dataset Hash | Source manifest SHA-256 `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795`; full manifest remains in the Git-ignored snapshot metadata. |
| Known Problems | Expected metadata: 25 classes / 2,801 images. Observed export: 10 classes / 2,799 images. Actual train/total counts are two below the frozen expectation; the actual export contains 10 classes rather than the reported 25. Version drift, mirror mismatch, augmentation/near-duplicate risk, source-image provenance, ten-to-five class reduction, and split leakage still require Phase 1 validation. |

## CSS-V1.1 Candidate

CSS-V1.1 is an audit candidate derived from the materialized v27 export. It is
not frozen and cannot be used as the Phase 1 training baseline until the
freeze correction is approved.

| Field | Value |
| --- | --- |
| Source | Roboflow Universe |
| Workspace | `roboflow-universe-projects` |
| Project | `construction-site-safety` |
| Version | `27` |
| Export | `YOLOv8` |
| `data.yaml` SHA256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Class list | `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`, `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`, `vehicle` |
| Classes | `10` |
| Images | `2799` |
| Split counts | train `2603` / valid `114` / test `82` |
| Manifest SHA256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| Historical status | Candidate, not frozen |
| Final disposition | Promoted to `CSS-PPE-10-V1` and frozen by ADR-012 |

## Source Snapshot Semantics

Roboflow version 27 is a **FROZEN GENERATED DATASET VERSION**, not a
**RAW ORIGINAL CAPTURE DATASET**.

The public version record includes generated preprocessing and augmentation,
including Auto-Orient, resize to 640x640, class modification, and augmentation
outputs. Therefore:

- `data/external/` means an unmodified third-party export snapshot.
- It does not mean original, unprocessed capture photographs.
- `source/` must remain immutable after extraction and verification.
- All later project transformations belong under `data/interim/` or
  `data/processed/`.

Phase 1D must distinguish exact duplicates from legal augmented or
near-duplicate outputs. Perceptual similarity alone must not trigger automatic
deletion.

## Phase 1B Download Status

The user downloaded workspace `roboflow-universe-projects`, project
`construction-site-safety`, version `27`, format `yolov8` through the Roboflow
API with their own account. Roboflow returned an extracted directory rather
than a ZIP, so no archive SHA-256 exists. The extracted directory was copied
without modification to the Git-ignored
`data/external/css-v27-yolov8/source/` snapshot.

The full snapshot manifest contains 5,601 files. Pair validation found zero
missing labels, zero orphan labels, 23 empty label files, and zero zero-byte
images. The actual `data.yaml` contains 10 classes and includes all five
required target semantics. The count and exported-class metadata nevertheless
conflict with the P1A-frozen expectations, so the snapshot remains immutable
but its validation status is `FAILED - EXPECTED COUNT OR CLASS MISMATCH`.

No source file was renamed, deleted, relabelled, or remapped to resolve the
conflict.

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
- Observed in the direct Roboflow API export: 2,799 images and ten classes in
  `data.yaml`; this conflicts with the version-page metadata already recorded
  for v27 and is not silently replaced by the observed values.

The historical V1 baseline request targeted Roboflow version 27, but the
artifact identity check now blocks that freeze. Moving project-level counts and
the Kaggle mirror must not be substituted for a corrected artifact fingerprint.

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

The five compliance classes remain locked in this order. The complete V1
training mapping adds two scene-context classes after the compliance classes
and is frozen in `docs/14_CLASS_MAPPING_DECISION.md`.

| ID | Class |
| --- | --- |
| 0 | person |
| 1 | hardhat |
| 2 | no_hardhat |
| 3 | vest |
| 4 | no_vest |
| 5 | machinery |
| 6 | vehicle |

## P1C-2 Processed Dataset

P1C-2 generated a Git-ignored YOLO-ready training artifact from the immutable
`CSS-PPE-10-V1` source:

```text
data/processed/css-ppe-10-v1/
├── train/images + labels
├── valid/images + labels
├── test/images + labels
├── data.yaml
└── metadata/
    ├── conversion.json
    ├── class_mapping.json
    ├── counts.json
    └── checksums.sha256
```

| Field | Value |
| --- | --- |
| Conversion contract | `docs/dataset_contracts/CSS-PPE-10-V1-MAPPING.yaml` |
| Mapping version | `PPE-MAPPING-V1` |
| Source image counts | train `2603` / valid `114` / test `82` |
| Processed image counts | train `2603` / valid `114` / test `82` |
| Processed label counts | train `2603` / valid `114` / test `82` |
| Source boxes | `38835` |
| Retained boxes | `30375` |
| Discarded boxes | `8460` |
| Discarded classes | `Mask` `1792`, `NO-Mask` `3362`, `Safety Cone` `3306` |
| Unknown source class IDs | `[]` |
| Output checksum manifest | `metadata/checksums.sha256`, SHA256 `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |

`checksums.sha256` records the other 5,602 output files and does not include
itself. The processed data remains untracked under the project Git policy.
P1C-2 does not establish final split-leakage or duplicate-quality acceptance;
those checks remain P1D/P1E work. M-001 remains `待实现`.

## P1D-0 Quality Validation Framework

P1D-0 defines a read-only quality framework for the generated processed
dataset. The plan freezes:

- structure, class-distribution, empty-label, bbox, small-object, exact
  duplicate, perceptual duplicate candidate, leakage, and label-consistency
  checks;
- bbox size buckets `small < 0.01`, `medium < 0.09`, and `large >= 0.09`;
- small-object risk thresholds of `20%` and `40%`; and
- a planned 64-bit dHash perceptual candidate threshold of Hamming distance
  `<= 5`.

`services/dataset_quality_service.py` returns observations only. It has no
repair or write API, and it recomputes the dataset manifest before and after
analysis to confirm that the source bytes did not change.

P1D-0 has not executed the validator against the real
`data/processed/css-ppe-10-v1/` dataset and has not generated a real quality
report. Perceptual duplicate hashing is recorded as
`DESIGNED_NOT_EXECUTED`; P1D-1 owns real-data execution. No image, label,
`data.yaml`, manifest, or processed metadata file was modified.

## P1D-1 Real Quality Validation

> Status: QUALITY ASSESSED / PAYLOAD IMMUTABLE

P1D-1 executed the observation-only validator against the real payload:

```text
data.yaml
train/images + labels
valid/images + labels
test/images + labels
```

| Field | Result |
| --- | --- |
| Payload files | `5599` |
| Payload hash before | `bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b` |
| Payload hash after | `bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b` |
| Structure | `PASS` |
| Images / labels | `2799` / `2799` |
| Boxes | `30375` valid boxes |
| Invalid bbox | `0` |
| Exact image duplicate groups | `0` |
| Perceptual dHash candidate pairs | `5` |
| Perceptual cross-split candidate groups | `2` (`valid` / `test`) |
| Empty labels | `32` retained as image-without-object |
| Report | `docs/17_DATASET_QUALITY_REPORT.md` |
| Machine-readable report | Git-ignored `metadata/quality_report.json` |

Risk flags are recorded for P1E: perceptual split-leakage candidates, HIGH
small-object risk for `hardhat`, `no_hardhat`, `vest`, and `vehicle`, class
imbalance, and empty-label observations. No cleaning, deletion, relabeling,
remapping, resizing, or resplitting occurred. Perceptual candidates remain
risk evidence only and must not be auto-deleted. `quality_report.json` is a
report artifact outside the payload hash and outside the existing
`metadata/checksums.sha256` payload manifest.

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

Phase 1B must preserve only the selected Roboflow version and record snapshot
retrieval, license attribution, checksums, conversion, duplicate analysis,
split manifest, and quality report locations. ADR-010 requires the complete
artifact fingerprint before a freeze decision; ADR-012 freezes the accepted
artifact as `CSS-PPE-10-V1`. Phase 1C-2 implements the frozen seven-class
mapping without modifying the frozen source. P1D-1 has now completed quality
assessment; final release and training-preparation decisions remain with P1E.
