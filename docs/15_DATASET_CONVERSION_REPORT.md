# Dataset Conversion Report

> Status: COMPLETED / MANUAL REVIEW PASS
>
> This report covers P1C-2 only. It does not perform P1D quality validation,
> P1E final freezing, model training, commit, or push.

## Input

```text
CSS-PPE-10-V1
```

Frozen source:

```text
data/external/css-v27-yolov8/source/
```

| Input field | Value |
| --- | --- |
| Workspace | `roboflow-universe-projects` |
| Project | `construction-site-safety` |
| Version | `27` |
| Export format | `yolov8` |
| `data.yaml` SHA256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Manifest SHA256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |

The source snapshot remains immutable. No source image, label, `data.yaml`,
manifest, or metadata file was edited.

## Mapping

```text
PPE-MAPPING-V1
```

Contract:

```text
docs/dataset_contracts/CSS-PPE-10-V1-MAPPING.yaml
```

| Source ID | Source class | Target ID | Target class |
| ---: | --- | ---: | --- |
| 0 | `Hardhat` | 1 | `hardhat` |
| 2 | `NO-Hardhat` | 2 | `no_hardhat` |
| 4 | `NO-Safety Vest` | 4 | `no_vest` |
| 5 | `Person` | 0 | `person` |
| 7 | `Safety Vest` | 3 | `vest` |
| 8 | `machinery` | 5 | `machinery` |
| 9 | `vehicle` | 6 | `vehicle` |

Discarded:

```text
1 Mask
3 NO-Mask
6 Safety Cone
```

## Output

Git-ignored output:

```text
data/processed/css-ppe-10-v1/
```

```text
data/processed/css-ppe-10-v1/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
├── data.yaml
└── metadata/
    ├── conversion.json
    ├── class_mapping.json
    ├── counts.json
    └── checksums.sha256
```

The processed `data.yaml` declares seven classes in frozen order and uses:

```text
train: ../train/images
val: ../valid/images
test: ../test/images
```

## Split Statistics

| Split | Source images | Processed images | Source boxes | Kept boxes | Discarded boxes |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 2603 | 2603 | 37378 | 29256 | 8122 |
| valid | 114 | 114 | 697 | 558 | 139 |
| test | 82 | 82 | 760 | 561 | 199 |
| Total | 2799 | 2799 | 38835 | 30375 | 8460 |

All processed splits have an equal number of images and labels.

## Discard Statistics

| Source class | Source ID | Discarded boxes |
| --- | ---: | ---: |
| `Mask` | 1 | 1792 |
| `NO-Mask` | 3 | 3362 |
| `Safety Cone` | 6 | 3306 |
| Total |  | 8460 |

Unknown source class IDs:

```text
[]
```

## Target Box Counts

| Target ID | Target class | Kept boxes |
| ---: | --- | ---: |
| 0 | `person` | 10031 |
| 1 | `hardhat` | 3551 |
| 2 | `no_hardhat` | 2428 |
| 3 | `vest` | 3258 |
| 4 | `no_vest` | 4153 |
| 5 | `machinery` | 5337 |
| 6 | `vehicle` | 1617 |

## Integrity

- Source `data.yaml` SHA256 before and after conversion:
  `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`.
- Source manifest SHA256 before and after conversion:
  `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795`.
- Images are copied byte-for-byte under the same filenames.
- Every processed image was SHA256-compared with its source image.
- Label conversion changes only the class ID and skips explicitly discarded
  boxes; bounding-box coordinate tokens remain unchanged.
- Every processed label class ID is within `0` through `6`.
- The processed `metadata/checksums.sha256` file has SHA256
  `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c`
  and records the other 5,602 output files.
- Metadata contains no API key, token, source-machine path, or absolute
  machine path.

## Conversion Metadata

The conversion emits:

- `metadata/conversion.json`: source identity, mapping version, split
  statistics, discard statistics, target box counts, and unknown IDs.
- `metadata/class_mapping.json`: frozen source classes, target classes,
  source-to-target map, and discard set.
- `metadata/counts.json`: final image, label, and box totals.
- `metadata/checksums.sha256`: deterministic SHA-256 manifest of the processed
  artifact, excluding only the manifest file itself.

## Tests

Offline tests cover:

1. deterministic class mapping;
2. unknown source class ID errors;
3. discard statistics;
4. unchanged bounding-box coordinates;
5. unchanged image hashes;
6. correct processed `data.yaml`;
7. source dataset immutability;
8. repeated conversion producing an identical output tree; and
9. processed label class counts matching metadata.

Default pytest uses synthetic offline fixtures and does not require the real
CSS download.

## Gates

| Gate | Result |
| --- | --- |
| G1C2-1 mapping contract exists | PASS |
| G1C2-2 source immutable | PASS |
| G1C2-3 output generated | PASS |
| G1C2-4 image count preserved | PASS |
| G1C2-5 image hash preserved | PASS |
| G1C2-6 labels converted correctly | PASS |
| G1C2-7 discard stats generated | PASS |
| G1C2-8 processed `data.yaml` correct | PASS |
| G1C2-9 no unknown classes | PASS |
| G1C2-10 conversion deterministic | PASS |
| G1C2-11 no training started | PASS |
| G1C2-12 Charter unchanged | PASS |

## Project Status

- P1B: completed.
- P1C-0: completed.
- P1C-1: completed.
- P1C-2: completed / manual review PASS.
- P1D: not started.
- M-001: `待实现`.

P1D must still validate exact duplicates, perceptual near-duplicates, invalid
coordinates, bad samples, and split leakage before P1E can freeze the final
dataset.

## Non-Goals

This conversion did not:

- modify the source snapshot;
- download new data or model weights;
- resize, augment, normalize, deduplicate, or delete data;
- train or evaluate a model;
- modify `docs/00_PROJECT_CHARTER.md`;
- commit or push; or
- start Phase 1D, Phase 1E, Phase 2, or any later phase.
