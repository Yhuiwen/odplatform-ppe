# P2-4-G4 Dataset Transfer & Integrity Verification Report

> Date: 2026-09-22
>
> Status: PASS
>
> Training: NOT STARTED
>
> Model weights: NOT DOWNLOADED
>
> Experiment execution: NOT STARTED

## Dataset Identity

| Field | Value |
| --- | --- |
| Dataset ID | `CSS-PPE-10-V1` |
| Mapping | `PPE-MAPPING-V1` |
| Transfer source | `data/processed/css-ppe-10-v1/` |
| Transfer method | Recursive SCP, no compression, no restructuring |
| Remote path | `/root/autodl-tmp/datasets/css-ppe-10-v1/` |
| Immutable snapshot | YES |

The remote copy preserves the frozen processed layout:

```text
css-ppe-10-v1/
├── data.yaml
├── metadata/
│   ├── checksums.sha256
│   ├── class_mapping.json
│   ├── conversion.json
│   ├── counts.json
│   └── quality_report.json
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

## Transfer Inventory

| Item | Local | Remote | Result |
| --- | ---: | ---: | --- |
| Total files | 5,604 | 5,604 | PASS |
| Images | 2,799 | 2,799 | PASS |
| Labels | 2,799 | 2,799 | PASS |
| Train images | 2,603 | 2,603 | PASS |
| Train labels | 2,603 | 2,603 | PASS |
| Valid images | 114 | 114 | PASS |
| Valid labels | 114 | 114 | PASS |
| Test images | 82 | 82 | PASS |
| Test labels | 82 | 82 | PASS |

## Data YAML

Remote `data.yaml`:

```yaml
train: ../train/images
val: ../valid/images
test: ../test/images
nc: 7
names:
  0: person
  1: hardhat
  2: no_hardhat
  3: vest
  4: no_vest
  5: machinery
  6: vehicle
```

Class order matches `PPE-MAPPING-V1` exactly.

| Fingerprint | SHA256 | Result |
| --- | --- | --- |
| Processed `data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | PASS |
| Upstream source `data.yaml` | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` | PASS |
| Source manifest | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` | PASS |
| Processed manifest file | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` | PASS |

The upstream `5c393e...` hash is stored in the processed conversion metadata and
continues to match the external source artifact. It is not the hash of the
transformed seven-class processed `data.yaml`; the latter is independently
verified as `45cc2717...`.

## Integrity Verification

The remote `metadata/checksums.sha256` was checked from the dataset root:

```text
manifest check: PASS
manifest entries checked: 5602
```

A separate full manifest was generated outside the immutable dataset root:

```text
file: css-ppe-10-v1.dataset_manifest.sha256
entries: 5604
sha256: aeb7bb66906245e48ff92c43aecd66154b292d1c0bfdf5181bb43410ebe492cc
full manifest check: PASS
```

The external manifest includes `data.yaml`, `metadata/checksums.sha256`, all
images, all labels, and all metadata files. It is not inside the dataset root
and therefore does not alter the transferred artifact.

## Python Smoke Check

```text
dataset_exists: True
train: ../train/images
val: ../valid/images
test: ../test/images
nc: 7
names: {0: 'person', 1: 'hardhat', 2: 'no_hardhat', 3: 'vest', 4: 'no_vest', 5: 'machinery', 6: 'vehicle'}
images: 2799
labels: 2799
```

## Safety Boundary

| Control | Result |
| --- | --- |
| Training command executed | NO |
| `yolo train` executed | NO |
| Pretrained weights downloaded | NO |
| Labels modified | NO |
| `data.yaml` modified | NO |
| Annotation regeneration performed | NO |
| Class mapping changed | NO |
| EXP-001 configuration modified | NO |

## Decision

`P2-4-G4 PASS`

The frozen `CSS-PPE-10-V1` dataset is transferred and integrity-verified on the
AutoDL host. Training remains prohibited and requires a separate authorization
gate.
