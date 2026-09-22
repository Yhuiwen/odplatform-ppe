# Dataset Quality Validation Plan

> Status: DESIGN FROZEN / EXECUTED BY P1D-1
>
> P1D-0 defines the observation-only quality framework. P1D-1 executed it
> against `CSS-PPE-10-V1` and produced the real quality report without changing
> the payload.

## Dataset

The validation target is the frozen processed dataset:

```text
data/processed/css-ppe-10-v1/
```

| Field | Value |
| --- | --- |
| Dataset ID | `CSS-PPE-10-V1` |
| Mapping | `PPE-MAPPING-V1` |
| Source `data.yaml` SHA256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Source manifest SHA256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| Processed manifest SHA256 | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |

The report object is implemented by
`services/dataset_quality_service.py`. Pure deterministic metrics live in
`utils/quality_metrics.py`.

## Validation Principles

1. Validation observes the current artifact; it does not repair it.
2. A quality finding is not permission to delete, relabel, resize, remap, or
   move data.
3. Every threshold and issue code must be explicit and reproducible.
4. The validator records dataset manifest hashes before and after analysis and
   must prove that the artifact is unchanged.
5. Exact duplicates are reported, not automatically treated as errors.
6. Roboflow augmentation and near-duplicate candidates remain data owned by the
   frozen source; only a later approved dataset version may change them.
7. Invalid labels or images are reported individually and do not stop unrelated
   statistics from being produced.
8. No quality report is generated from the real dataset during P1D-0.

## Q1 Structure

Required dataset layout:

```text
css-ppe-10-v1/
├── train/images/
├── train/labels/
├── valid/images/
├── valid/labels/
├── test/images/
├── test/labels/
├── data.yaml
└── metadata/
```

Checks:

- `data.yaml` exists and parses as a YAML mapping.
- `nc` matches the class list.
- The class list is exactly `person`, `hardhat`, `no_hardhat`, `vest`,
  `no_vest`, `machinery`, `vehicle`.
- Each split has both `images/` and `labels/`.
- Image and label counts are reported per split.
- Missing labels, orphan labels, duplicate stems, and zero-byte images are
  listed by relative path.

## Q2 Class Distribution

For each split and total, count boxes for:

| ID | Class |
| ---: | --- |
| 0 | `person` |
| 1 | `hardhat` |
| 2 | `no_hardhat` |
| 3 | `vest` |
| 4 | `no_vest` |
| 5 | `machinery` |
| 6 | `vehicle` |

The report records image count, box count, class count, per-class box counts,
class share, and maximum-to-minimum imbalance ratio. `hardhat` and
`no_hardhat` are highlighted as small-object-sensitive classes. Imbalance is
reported as a risk, not repaired by resampling during P1D.

## Q3 Empty Labels

An empty label is an existing `.txt` file containing no non-whitespace records.
It is interpreted as an image with no target objects, provided the matching
image exists.

The report records:

- total empty-label count;
- relative paths;
- per-split counts;
- zero-byte image count separately.

Empty labels are not deleted or treated as missing-label errors.

## Q4 Bounding Boxes

Every non-empty line must contain exactly five fields:

```text
class_id x_center y_center width height
```

Validation rules:

- `class_id` is an integer from `0` through `6`.
- All coordinates are finite numeric values.
- `0 <= x_center <= 1`.
- `0 <= y_center <= 1`.
- `0 < width <= 1`.
- `0 < height <= 1`.
- The derived extent must stay inside the image:
  `x_center - width/2 >= 0`, `x_center + width/2 <= 1`, and the equivalent
  vertical checks.

Issue codes:

```text
malformed_yolo_line
unknown_class_id
x_center_out_of_range
y_center_out_of_range
width_out_of_range
height_out_of_range
bbox_out_of_image_bounds
```

Invalid lines remain in place and are listed in the report.

## Q5 Small Objects

Normalized bounding-box area is:

```text
area = width * height
```

Frozen size buckets:

| Bucket | Definition |
| --- | --- |
| `small` | `area < 0.01` |
| `medium` | `0.01 <= area < 0.09` |
| `large` | `area >= 0.09` |

The thresholds correspond to normalized image area, not pixels. At 640x640,
`0.01` is approximately 4,096 pixels before considering the actual image
dimensions.

Small-object risk by class:

| Risk | Definition |
| --- | --- |
| `NO_DATA` | No valid boxes for the class |
| `LOW` | `small_share < 0.20` |
| `MEDIUM` | `0.20 <= small_share < 0.40` |
| `HIGH` | `small_share >= 0.40` |

The report emphasizes `hardhat` and `no_hardhat`, but records all seven classes.

## Q6 Duplicates

Exact duplicate detection groups files by SHA256:

- image SHA256 across the processed dataset;
- label file SHA256 across the processed dataset.

The report preserves every duplicate path and group. Exact duplicates inside a
single split and across splits are reported separately.

Perceptual duplicate design:

- algorithm: 64-bit difference hash (`dHash`, 8x8);
- candidate threshold: Hamming distance `<= 5`;
- exact duplicates are reported separately from perceptual candidates;
- Roboflow augmentation candidates are not classified as defects;
- no file is removed, renamed, or rewritten.

P1D-0 records the perceptual algorithm design but does not execute perceptual
hashing on the real dataset. P1D-1 owns that execution and must record image
decoder failures explicitly.

## Q7 Leakage

Leakage detection uses exact image SHA256 only:

- group identical image bytes across `train`, `valid`, and `test`;
- report the SHA256, all relative paths, and the involved splits;
- set `leakage.detected` when a group spans more than one split.

The output is evidence for review. P1D does not automatically remove a
cross-split duplicate because generated augmentation may explain some groups.

## Q8 Label Consistency

For every image and label:

- pairing is by matching filename stem;
- missing labels are listed;
- orphan labels are listed;
- duplicate image or label stems are listed;
- malformed lines, unknown classes, and invalid bbox values are listed;
- an empty label is accepted only when its image exists;
- label count per split must equal image count per split.

The consistency report is deterministic and uses relative POSIX paths only.

## Output Report Format

`DatasetQualityService.analyze()` returns a machine-readable mapping suitable
for later JSON serialization. Required top-level sections:

```text
dataset
thresholds
structure
class_distribution
empty_labels
bounding_boxes
small_objects
duplicates
leakage
label_consistency
dataset_hash
```

P1D-1 will produce both JSON and Markdown reports under the Git-ignored report
area. The planned sections are:

1. Dataset identity and fingerprints
2. Validation scope and thresholds
3. Structure and pairing
4. Class distribution and imbalance
5. Empty-label summary
6. Bounding-box issues
7. Small-object risk
8. Exact and perceptual duplicate summary
9. Cross-split leakage summary
10. Label consistency
11. Dataset hash before and after analysis
12. Risks, limitations, and recommended next action

The report must distinguish observations from recommendations and must not
claim that a detected duplicate is invalid without evidence.

## Forbidden Actions

- modifying `data/external/`
- modifying `data/processed/css-ppe-10-v1/`
- deleting images or labels
- changing bbox coordinates or class IDs
- merging or deleting classes
- resplitting train/valid/test
- augmenting data
- auto-fixing findings
- training a model
- treating perceptual similarity as proof of duplicate contamination
- generating a real P1D report before P1D-1
