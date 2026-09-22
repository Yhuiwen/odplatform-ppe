# Class Mapping Decision

> Decision status: FROZEN
>
> This decision freezes the source-to-training class mapping for
> `CSS-PPE-10-V1`. It does not convert labels or create a processed dataset.

## Final Decision

Selected strategy:

```text
Strategy C
```

The V1 training artifact will contain seven classes: the five locked PPE
compliance classes followed by the two approved scene-context classes.

The original `CSS-PPE-10-V1` source remains immutable. Label conversion and
processed dataset generation remain unimplemented and must be performed by a
later P1C implementation step using this frozen mapping contract.

## Original Classes

| Original ID | Original class |
| ---: | --- |
| 0 | `Hardhat` |
| 1 | `Mask` |
| 2 | `NO-Hardhat` |
| 3 | `NO-Mask` |
| 4 | `NO-Safety Vest` |
| 5 | `Person` |
| 6 | `Safety Cone` |
| 7 | `Safety Vest` |
| 8 | `machinery` |
| 9 | `vehicle` |

## Final Training Classes

| New ID | Name | Source IDs |
| ---: | --- | --- |
| 0 | `person` | `[5]` |
| 1 | `hardhat` | `[0]` |
| 2 | `no_hardhat` | `[2]` |
| 3 | `vest` | `[7]` |
| 4 | `no_vest` | `[4]` |
| 5 | `machinery` | `[8]` |
| 6 | `vehicle` | `[9]` |

The first five output classes preserve the locked ADR-003 order exactly.
`machinery` and `vehicle` are scene-context classes, not PPE compliance
classes.

## Mapping Table

| Original ID | Original class | New ID | New class | Disposition |
| ---: | --- | ---: | --- | --- |
| 0 | `Hardhat` | 1 | `hardhat` | Retain and remap |
| 1 | `Mask` |  |  | Discard |
| 2 | `NO-Hardhat` | 2 | `no_hardhat` | Retain and remap |
| 3 | `NO-Mask` |  |  | Discard |
| 4 | `NO-Safety Vest` | 4 | `no_vest` | Retain and remap |
| 5 | `Person` | 0 | `person` | Retain and remap |
| 6 | `Safety Cone` |  |  | Discard |
| 7 | `Safety Vest` | 3 | `vest` | Retain and remap |
| 8 | `machinery` | 5 | `machinery` | Retain for scene context |
| 9 | `vehicle` | 6 | `vehicle` | Retain for scene context |

Frozen source-to-training map:

```text
0 -> 1
2 -> 2
4 -> 4
5 -> 0
7 -> 3
8 -> 5
9 -> 6
```

Frozen discard set:

```text
1, 3, 6
```

## Discard Policy

| Old ID | Name | Reason |
| ---: | --- | --- |
| 1 | `Mask` | Mask is not part of the locked V1 PPE compliance surface. |
| 3 | `NO-Mask` | NO-Mask is not part of the locked V1 PPE compliance surface. |
| 6 | `Safety Cone` | No approved V1 rule, event, or report consumer currently requires Safety Cone. |

Discarding a class means its boxes are omitted from the converted training
labels. Conversion must count and report every discarded box; silent loss is
not allowed. The original source labels remain untouched.

## Rationale

### PPE relevance

The first five output classes directly support the V1 compliance workflow:

- `person` for tracking and association;
- `hardhat` and `no_hardhat` for helmet compliance; and
- `vest` and `no_vest` for vest compliance.

`machinery` and `vehicle` are retained as scene context for future
hazard-area and report capabilities. They must not be interpreted as PPE
compliance states.

### YOLO11 training feasibility

Seven output classes are feasible for YOLO11n on the frozen 2,799-image
dataset. The source contains substantial annotation volume for all retained
classes, while class imbalance remains a training concern:

| Training class | Total source boxes |
| --- | ---: |
| `person` | 10031 |
| `hardhat` | 3551 |
| `no_hardhat` | 2428 |
| `vest` | 3258 |
| `no_vest` | 4153 |
| `machinery` | 5337 |
| `vehicle` | 1617 |

The mapping avoids the three discarded classes and keeps only two additional
scene-context branches. Per-class metrics, confidence calibration, and
small-object validation remain required in later phases.

### Rule Engine compatibility

The Rule Engine must use an explicit compliance allowlist:

```text
person, hardhat, no_hardhat, vest, no_vest
```

`machinery` and `vehicle` must not trigger helmet or vest violations. Keeping
the five compliance classes at IDs 0 through 4 preserves ADR-003 behavior.

### Event Engine compatibility

Only helmet and vest compliance rules may create V1 violation events.
`machinery` and `vehicle` remain context detections until a future approved ADR
defines a hazard-zone or scene-event contract.

## Future Extension

Discarded classes may be reconsidered only through a later evidence-backed
decision. Any reintroduction must:

- start from the immutable `CSS-PPE-10-V1` snapshot;
- define a concrete consumer and evaluation method;
- freeze a new or versioned mapping;
- keep existing training-class IDs stable where compatibility matters; and
- avoid modifying the original source labels or fingerprint.

`Mask` and `NO-Mask` can support a future mask-compliance extension.
`Safety Cone` can support a future work-zone or risk-context extension.
Neither is part of the current V1 training output.

## Impact Analysis

| Layer | Impact |
| --- | --- |
| Detector | Emits seven classes; the five compliance classes retain locked semantics and IDs 0 through 4 |
| Tracker | Tracks only `person`; machinery and vehicle are not identity targets |
| Association | Associates helmet and vest classes to `person`; scene classes are excluded |
| Rule Engine | Uses the five compliance classes only and rejects scene classes from PPE decisions |
| Event Engine | Creates helmet/vest events only; scene classes require a future event contract |
| LLM Report | May use scene context only when it is stored and validated as structured platform data; no unsupported inference |

## Non-Goals

This decision does not:

- modify `data/external/css-v27-yolov8/source/`
- modify `data.yaml` or any label file
- generate a processed dataset
- convert labels
- train a model
- change the frozen `CSS-PPE-10-V1` fingerprint
- mark M-001 implemented
