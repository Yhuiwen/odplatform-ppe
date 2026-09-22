# Dataset Candidate Evaluation

> Evaluation status: DECISION GATE RECORDED
>
> This document compares the historical CSS-V1 freeze target with the
> materialized CSS-V1.1 candidate. It does not freeze either candidate,
> modify the dataset, remap classes, or start Phase 1C.

## Decision Scope

The evaluation answers a governance question:

> Which candidate is the better basis for the V1 dataset freeze?

It does not answer whether a new download should be attempted. No new data may
be downloaded, and the immutable source snapshot must not be edited, cleaned,
remapped, or deleted.

## Candidate Comparison

| Criterion | CSS-V1 | CSS-V1.1 Candidate |
| --- | --- | --- |
| Source identity | Roboflow Universe workspace `roboflow-universe-projects`, project `construction-site-safety`, version `27` | Same workspace, project, and version `27` |
| Artifact fingerprint | Public version metadata only; no matching `data.yaml` or manifest fingerprint for the recorded 25-class/2,801-image identity | `data.yaml` SHA256 `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`; manifest SHA256 `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| Image count | Reported: 2,801 total; train/valid/test `2,605/114/82` | Observed: 2,799 total; train/valid/test `2,603/114/82` |
| Class count | Reported: 25 source classes | Observed: 10 exported classes in `data.yaml` |
| PPE relevant classes | `Person`, `Hardhat`, `NO-Hardhat`, `Safety Vest`, `NO-Safety Vest` are present in the reported class list | `Person`, `Hardhat`, `NO-Hardhat`, `Safety Vest`, `NO-Safety Vest` are present in the exported class list |
| Advantages | Matches the historical P1A metadata and the broader 25-class source description; preserves the original project-level scope | Reproducible materialized artifact; complete SHA-256 fingerprint; actual split counts and integrity results are observable; contains all five V1 target semantics |
| Risks | Version metadata and materialized export do not match; no verified artifact fingerprint for the historical 25-class identity; cannot be treated as a frozen training artifact | Smaller exported class list than the historical metadata; origin of the 10-class export is not fully explained; remains a candidate rather than an approved freeze; augmentation and near-duplicate review remains pending |
| Suitability for V1 | `BLOCKED / NEEDS FREEZE CORRECTION`; suitable only as historical source-selection evidence until corrected | `Candidate, not frozen`; suitable as the artifact under evaluation, but not yet approved for training or P1C |

## Shared Evidence

Both candidates identify the same source coordinates:

- Workspace: `roboflow-universe-projects`
- Project: `construction-site-safety`
- Version: `27`
- Export format: `yolov8`

The difference is therefore not a different source project. It is a mismatch
between the frozen metadata identity and the materialized export artifact
identity. ADR-010 requires the complete artifact fingerprint before a freeze
decision.

## Selection Criteria

V1 dataset selection prioritizes:

1. reproducibility
2. verified artifact identity
3. PPE task relevance
4. license clarity
5. training feasibility

Maximum class count is not a selection criterion by itself. A smaller,
fully fingerprinted artifact can be preferable to a broader metadata record
that cannot be tied to the bytes that will actually be trained on.

## Decision Recorded After Evaluation

The P1B.2 evaluation did not freeze a candidate. P1B.3 subsequently accepted
the materialized artifact and recorded the final decision in
`docs/12_DATASET_FREEZE_DECISION.md`.

- CSS-V1 remains `BLOCKED / NEEDS FREEZE CORRECTION` and is rejected for V1.
- CSS-V1.1 Candidate was promoted to `CSS-PPE-10-V1` and is `FROZEN`.
- P1C remains not started until the freeze decision receives manual review.
- M-001 remains `待实现`.

## Required Evidence Before Any Freeze

A future freeze record must bind all of the following to the candidate:

- workspace
- project
- version
- export format
- `data.yaml` SHA-256
- class list
- manifest SHA-256
- actual train, validation, and test counts

The freeze decision also must preserve the license evidence, identify the
source URL, and state whether the selected artifact is a generated Roboflow
export or a raw capture dataset.

## Non-Goals

This evaluation does not:

- download new data
- modify the existing dataset or source snapshot
- change `data.yaml`
- perform class conversion or remapping
- train a model
- start Phase 1C
- mark M-001 implemented
