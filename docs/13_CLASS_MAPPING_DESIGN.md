# Class Mapping Design

> Design status: CANDIDATE ANALYSIS — NO FINAL SELECTION
>
> This document designs the P1C class-mapping decision space. It does not
> convert labels, create a processed dataset, freeze a mapping, or start P1C.

## 1. Frozen Dataset

Dataset:

```text
CSS-PPE-10-V1
```

The source identity is frozen by artifact fingerprint:

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

The source snapshot remains immutable and Git-ignored. The table below records
the ten original classes exactly as exported. The instance counts are
read-only observations from the current snapshot and are included to make the
class-distribution tradeoffs visible.

| ID | Original class | Train boxes | Valid boxes | Test boxes | Total boxes |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0 | `Hardhat` | 3362 | 79 | 110 | 3551 |
| 1 | `Mask` | 1743 | 21 | 28 | 1792 |
| 2 | `NO-Hardhat` | 2318 | 69 | 41 | 2428 |
| 3 | `NO-Mask` | 3209 | 74 | 79 | 3362 |
| 4 | `NO-Safety Vest` | 3957 | 106 | 90 | 4153 |
| 5 | `Person` | 9691 | 166 | 174 | 10031 |
| 6 | `Safety Cone` | 3170 | 44 | 92 | 3306 |
| 7 | `Safety Vest` | 3156 | 41 | 61 | 3258 |
| 8 | `machinery` | 5238 | 55 | 44 | 5337 |
| 9 | `vehicle` | 1534 | 42 | 41 | 1617 |

Original dataset classes and training classes are separate concepts. Changing
the original file is prohibited; any future conversion must emit new files
from an immutable source.

## 2. Project Objective

V1 is a construction PPE compliance detection and alert platform. Its core
decision surface is:

- detect people;
- detect helmet compliance (`hardhat` versus `no_hardhat`);
- detect vest compliance (`vest` versus `no_vest`);
- track people;
- associate PPE detections with people;
- apply temporal compliance rules;
- create auditable violation events and evidence; and
- support grounded reports from platform data.

Mask detection is not part of the locked V1 compliance rule surface. Scene
objects may still have value for context, but that value must be demonstrated
against a defined downstream capability rather than assumed from label
availability.

## 3. Candidate Mapping A

### Mapping

| Original ID | Original class | Candidate output class |
| ---: | --- | --- |
| 0 | `Hardhat` | `Hardhat` |
| 1 | `Mask` | `Mask` |
| 2 | `NO-Hardhat` | `NO-Hardhat` |
| 3 | `NO-Mask` | `NO-Mask` |
| 4 | `NO-Safety Vest` | `NO-Safety Vest` |
| 5 | `Person` | `Person` |
| 6 | `Safety Cone` | `Safety Cone` |
| 7 | `Safety Vest` | `Safety Vest` |
| 8 | `machinery` | `machinery` |
| 9 | `vehicle` | `vehicle` |

### Analysis

| Dimension | Assessment |
| --- | --- |
| Advantages | Preserves every annotation; keeps mask and scene context; avoids information loss; permits later scene-aware analysis without a new source download |
| Disadvantages | Expands V1 evaluation and rule semantics beyond the locked five classes; keep/ignore policies must be defined; introduces classes with no V1 compliance rule |
| Training impact | One model predicts ten classes; class imbalance ranges from `Person` 10,031 boxes to `vehicle` 1,617 boxes; more output classes can add class-confusion and calibration work but does not itself create additional model size |
| Rule engine impact | Rule engine must explicitly filter to `Person`, helmet, and vest classes; mask and scene classes must not trigger compliance events accidentally |
| Inference complexity | One detector, but downstream filtering and structured result schemas must carry ten classes; NMS and display logic see more class possibilities |
| Suitable scenarios | Broad scene-understanding experiments, multi-task research, or future extensions where every class has an approved consumer |

## 4. Candidate Mapping B

### Mapping

| Original ID | Original class | Candidate output ID | Candidate output class |
| ---: | --- | ---: | --- |
| 0 | `Hardhat` | 1 | `hardhat` |
| 2 | `NO-Hardhat` | 2 | `no_hardhat` |
| 7 | `Safety Vest` | 3 | `vest` |
| 4 | `NO-Safety Vest` | 4 | `no_vest` |
| 5 | `Person` | 0 | `person` |

### Discarded from Training Output

| Original ID | Original class | Disposition |
| ---: | --- | --- |
| 1 | `Mask` | Explicitly discarded |
| 3 | `NO-Mask` | Explicitly discarded |
| 6 | `Safety Cone` | Explicitly discarded |
| 8 | `machinery` | Explicitly discarded |
| 9 | `vehicle` | Explicitly discarded |

### Analysis

| Dimension | Assessment |
| --- | --- |
| Advantages | Matches the locked V1 class set and compliance surface; simplest labels, evaluation, rules, and model-facing output; removes irrelevant mask and scene classes from the detector objective |
| Disadvantages | Permanently removes mask and scene information from the processed training artifact; any later scene-aware feature needs a new source-derived output or separate model; discarded-box accounting must be auditable |
| Training impact | Five output channels; larger and more balanced share of labels remain PPE-relevant; lower semantic branching than A or C; still retains imbalance across the five target classes |
| Rule engine impact | One-to-one support for Person, helmet, and vest checks; no irrelevant class filtering in the core compliance path |
| Inference complexity | Lowest downstream filtering and schema complexity among the three candidates |
| Suitable scenarios | Focused V1 compliance delivery, rapid baseline training, clean per-class evaluation, and a system whose event rules only use the five locked classes |

## 5. Candidate Mapping C

### Mapping

| Original ID | Original class | Candidate output class |
| ---: | --- | --- |
| 5 | `Person` | `person` |
| 0 | `Hardhat` | `hardhat` |
| 2 | `NO-Hardhat` | `no_hardhat` |
| 7 | `Safety Vest` | `vest` |
| 4 | `NO-Safety Vest` | `no_vest` |
| 8 | `machinery` | `machinery` |
| 9 | `vehicle` | `vehicle` |

### Discarded from Training Output

| Original ID | Original class | Disposition |
| ---: | --- | --- |
| 1 | `Mask` | Explicitly discarded |
| 3 | `NO-Mask` | Explicitly discarded |
| 6 | `Safety Cone` | Explicitly discarded |

### Analysis

| Dimension | Assessment |
| --- | --- |
| Advantages | Keeps machinery and vehicle context for future hazard-zone or scene analysis while retaining all five compliance classes; excludes mask classes with no V1 rule |
| Disadvantages | Seven-class detector exceeds the locked five-class evaluation surface; machinery/vehicle labels may distract from PPE learning; scene features have no approved event contract yet; requires explicit handling of three discarded classes |
| Training impact | Seven output channels; retains `machinery` 5,337 and `vehicle` 1,617 boxes; could improve scene context but may increase class-confusion risk under a small single-model baseline |
| Rule engine impact | Core PPE rules still use five classes; any hazard-zone rule must define how machinery/vehicle coordinates are consumed without creating false PPE violations |
| Inference complexity | Moderate: detector emits seven classes and downstream code must separate compliance classes from scene context |
| Suitable scenarios | A future V1 design that explicitly budgeted machinery/vehicle context and defined its event/report consumer before training |

## 6. Comparison Table

| Criterion | Candidate A: 10-class | Candidate B: 5-class PPE core | Candidate C: 7-class PPE + scene |
| --- | --- | --- | --- |
| Class count | 10 | 5 | 7 |
| PPE relevance | Mixed: five compliance classes plus mask and scene classes | Direct: all five locked compliance classes | Direct for five compliance classes plus scene context |
| Training complexity | Higher semantic surface and more filtering | Lowest semantic surface; matches locked output | Medium semantic surface with unproven scene consumers |
| Inference complexity | Highest class/schema surface | Lowest | Medium |
| Rule engine complexity | Requires filtering of five non-compliance classes | Direct mapping to helmet and vest rules | Requires separation of scene classes from PPE rules |
| Future extensibility | Widest retention of current labels | Narrowest processed output; extensions need another artifact | Retains two scene classes, but mask still needs another artifact |
| Risk | Unapproved V1 semantics and class distraction | Information loss for mask/scene-based future features | Scope creep and unclear event/report requirements |

### Required Question Analysis

**Should Mask be retained?**

Mask is not a V1 MUST or compliance rule. Candidate A retains it; Candidates B
and C discard it. Retaining it would require a justified downstream consumer
and an explicit decision that it is useful context rather than merely
available data. Discarding it requires a recorded disposition and box counts,
not silent omission.

**Should machinery / vehicle be retained?**

They could support site-context analysis, hazard-area reasoning, or grounded
LLM report context. However, no V1 event contract currently consumes them.
Candidate A retains both, Candidate C retains both with a seven-class scope,
and Candidate B removes both from the processed output. The decision should
depend on a named downstream use case, not on the possibility of future use
alone.

**Is Safety Cone valuable?**

Safety Cone could help identify work zones, temporary barriers, or risk-event
context, but no V1 requirement currently consumes cone detections. Candidate A
retains it, while B and C discard it. It should remain an explicit
discard-or-retain decision with evidence from the downstream design.

**How does class count affect YOLO11?**

The frozen data has 2,799 images and highly imbalanced instance counts, from
`Person` at 10,031 boxes to `vehicle` at 1,617 boxes. A YOLO11 detector can
handle multiple classes, so class count alone is not the primary limitation.
The practical effects are:

- more classes create more classification branches and more opportunities for
  inter-class confusion;
- rare or context-heavy classes can receive weaker learning signals even when
  their raw box count is not tiny;
- small objects such as distant PPE or scene objects can be harder than large
  people or machinery;
- evaluation and rule logic become harder to interpret when classes have no
  approved V1 consumer; and
- a simpler five-class output is easier to audit against the Charter, while a
  context model may require a distinct objective and evaluation.

**How do the system layers differ?**

| System layer | Candidate A | Candidate B | Candidate C |
| --- | --- | --- | --- |
| Detector | Emits ten classes; must preserve non-PPE classes in schema | Emits the five locked classes directly | Emits seven classes; splits PPE and scene outputs |
| Tracker | Tracks `Person`; other classes must be ignored for identity | Tracks `Person` with the simplest class filter | Tracks `Person`; scene classes are non-tracked context |
| Association | Associates helmet/vest classes to people; must exclude Mask and scene classes | Directly associates the four PPE classes to `person` | Associates the same four PPE classes; machinery/vehicle remain separate |
| Rule Engine | Needs strict allowlists so mask or scene classes cannot trigger compliance decisions | Smallest and clearest helmet/vest rule set | Needs an explicit PPE-versus-scene rule boundary |
| Event Engine | Could emit additional context events only if separately specified | Produces only the approved compliance-event surface | May add hazard-zone context only after event contracts are defined |
| LLM Report | Can mention context classes, but must ground every claim in stored structured events | Reports the five-class event surface without unsupported context claims | Can include scene context if persisted and validated by the event engine |

## 7. Recommendation Criteria

No final selection is made in this document. A later decision gate should
evaluate candidates against:

1. Compatibility with ADR-003 and the locked five-class V1 output.
2. Preservation or explicit disposal of every original class.
3. Evidence that a retained non-PPE class has a named downstream consumer.
4. Impact on detector evaluation, rule correctness, event semantics, and
   report grounding.
5. Class imbalance and small-object effects observed in the frozen artifact.
6. Ability to keep the original snapshot immutable and make conversion
   reproducible.
7. A complete source-to-output map with no ambiguous or implicit drops.
8. A testable conversion contract before any label conversion begins.

## 8. Open Questions

- Is Mask an approved V1 context feature, an Extension, or an explicit discard?
- Are machinery and vehicle required by a future hazard-zone or report feature?
- Is Safety Cone required by any approved V1 event or report contract?
- Should non-PPE scene classes be handled by a separate detector or a later
  extension artifact instead of the V1 detector?
- What exact validation evidence will approve a mapping before conversion?
- How will per-class metrics, discarded boxes, and mapping coverage be
  reported to prove that no class was silently lost?

This document deliberately does not choose A, B, or C. P1C conversion remains
blocked until a separate Class Mapping Decision Gate is reviewed and frozen.

> Subsequent decision: P1C-1 selected Strategy C and froze the seven-class
> mapping in `docs/14_CLASS_MAPPING_DECISION.md` and ADR-014. This document
> remains the historical design record and does not perform conversion.
