# Dataset Freeze Decision

> Decision status: FROZEN
>
> This decision freezes the V1 training-data identity. It does not modify the
> external dataset, remap classes, convert labels, or start Phase 1C.

## Dataset Decision

Selected:

```text
CSS-PPE-10-V1
```

Rejected candidates:

```text
CSS-V1
```

Reason:

CSS-V1 is blocked because its 25-class / 2,801-image metadata record cannot be
bound to the materialized 10-class / 2,799-image YOLOv8 export. No matching
`data.yaml` or manifest fingerprint exists for the metadata-only identity.
Per ADR-011, verified artifact identity and reproducibility take priority over
the larger reported class count.

## Accepted Candidate

Accepted candidate:

```text
CSS-V1.1 Candidate
```

The accepted candidate is promoted to the immutable V1 dataset identity
`CSS-PPE-10-V1`.

## Artifact fingerprint:

| Field | Frozen value |
| --- | --- |
| Workspace | `roboflow-universe-projects` |
| Project | `construction-site-safety` |
| Version | `27` |
| Format | `yolov8` |
| `data.yaml` SHA256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Manifest SHA256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| Actual images | `2799` |
| Split counts | train `2603` / valid `114` / test `82` |
| Classes | `10` |
| Class list | `Hardhat`, `Mask`, `NO-Hardhat`, `NO-Mask`, `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`, `machinery`, `vehicle` |

The manifest SHA256 hashes the deterministic, source-relative file manifest.
The `data.yaml` SHA256 hashes the unmodified source file. Neither value may be
recomputed after editing the snapshot.

## Dataset identity:

Dataset ID:

```text
CSS-PPE-10-V1
```

Identity:

```text
workspace: roboflow-universe-projects
project: construction-site-safety
version: 27
format: yolov8
data.yaml SHA256: 5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34
manifest SHA256: ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795
images: 2799
splits: train 2603 / valid 114 / test 82
```

The frozen artifact is a generated Roboflow export, not a raw original capture
dataset. The source snapshot remains external to Git and immutable.

## Why selected:

CSS-V1.1 Candidate satisfies the V1 selection criteria in ADR-011:

1. Reproducibility: the materialized export and source-relative manifest are
   available outside Git.
2. Verified artifact identity: workspace, project, version, export format,
   `data.yaml` SHA256, class list, manifest SHA256, and split counts are bound.
3. PPE task relevance: all five locked V1 semantics are present.
4. License clarity: the source is recorded under CC BY 4.0 with evidence.
5. Training feasibility: 2,799 images and the existing train/valid/test split
   are sufficient to proceed to later data preparation after manual review.

The selection does not claim that ten classes are intrinsically better than
25. It selects the artifact whose actual bytes and class list are known.

## Why alternatives rejected:

CSS-V1 is rejected for the V1 freeze because:

- its 25-class / 2,801-image metadata has no verified matching artifact;
- the materialized v27 export contains 10 classes and 2,799 images;
- no artifact fingerprint can prove which bytes correspond to the metadata;
- accepting it would make training data identity ambiguous; and
- maximum class count is not a selection criterion under ADR-011.

This rejection does not erase the historical CSS-V1 evidence. It remains
recorded as `BLOCKED / NEEDS FREEZE CORRECTION` for audit and provenance.

## Training scope:

The frozen source has ten classes. V1 training remains limited to the locked
five-class target:

```text
0 person
1 hardhat
2 no_hardhat
3 vest
4 no_vest
```

Phase 1C must explicitly map only the corresponding source classes and must
account for the remaining five exported classes without silently redefining
them:

```text
Mask, NO-Mask, Safety Cone, machinery, vehicle
```

This decision does not perform that mapping.

## P1C-1 Mapping Update

P1C-1 subsequently selected Strategy C and froze the seven-class training
mapping:

```text
0 person <- [5]
1 hardhat <- [0]
2 no_hardhat <- [2]
3 vest <- [7]
4 no_vest <- [4]
5 machinery <- [8]
6 vehicle <- [9]
```

The first five classes remain the locked compliance classes. `machinery` and
`vehicle` are scene-context classes and do not trigger PPE violations. The
detailed mapping and discard policy are recorded in
`docs/14_CLASS_MAPPING_DECISION.md` and ADR-014.

## P1C input:

P1C input is the immutable, Git-ignored snapshot:

```text
data/external/css-v27-yolov8/source/
```

Required input fingerprint:

```text
data.yaml SHA256:
5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34

manifest SHA256:
ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795
```

Phase 1C remains not started. Before it begins, manual review must accept this
freeze decision. The source snapshot must remain unchanged; conversion output
belongs under `data/interim/` or `data/processed/`.

## Non-Goals

This decision does not:

- download new data
- modify the existing dataset, labels, images, or `data.yaml`
- perform class conversion or remapping
- train a model
- start Phase 1C
- mark M-001 implemented
