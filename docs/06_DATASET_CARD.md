# Dataset Card

> Phase 0 status: PLANNED / NOT DOWNLOADED
>
> No dataset statistics, hashes, image counts, label counts, or local paths are
> recorded as facts before an approved Phase 1 download and validation.

## V1 Primary Dataset: Construction Site Safety (CSS)

| Field | Value |
| --- | --- |
| Dataset Name | Construction Site Safety (CSS) |
| Source | TO VERIFY IN PHASE 1 |
| Download URL | TO VERIFY IN PHASE 1 |
| License | TO VERIFY IN PHASE 1 |
| Download Date | NOT DOWNLOADED |
| Version | PLANNED / NOT DOWNLOADED |
| Original Classes | TO VERIFY IN PHASE 1 |
| Selected Classes | person, hardhat, no_hardhat, vest, no_vest |
| Annotation Format | TO VERIFY IN PHASE 1 |
| Conversion | Planned: source format -> YOLO format with locked class mapping |
| Image Count | NOT AVAILABLE - DATASET NOT DOWNLOADED |
| Label Count | NOT AVAILABLE - DATASET NOT DOWNLOADED |
| Train | PLANNED / NOT CREATED |
| Val | PLANNED / NOT CREATED |
| Test | PLANNED / NOT CREATED |
| Hash / Version evidence | NOT AVAILABLE - DATASET NOT DOWNLOADED |
| Known Problems | Class semantics, source license, duplicate risk, and split leakage require Phase 1 checks |

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

Phase 1 must replace every TO VERIFY/NOT AVAILABLE field with inspected evidence
and must record source retrieval, license, checksum, conversion, duplicate
analysis, split manifest, and quality report locations.
