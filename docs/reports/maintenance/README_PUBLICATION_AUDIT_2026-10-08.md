# README publication audit — 2026-10-08

## Current Git Identity

- Repository: `https://github.com/Yhuiwen/odplatform-ppe`
- Branch: `main`
- Local HEAD, `origin/main`, and read-only `ls-remote` for remote main at task start: `4ece9baa0541731e134927e7fb547c7c1faca848`
- Starting worktree: clean. No pull, merge, rebase, reset, clean, restore, commit, tag, or push was executed.

## Files Inspected

Mandatory governance: `AGENTS.md`, `docs/00_PROJECT_CHARTER.md` through `docs/09_REFERENCE_ASSETS.md`, the latest worklog, and `docs/phases/PHASE_09_INTEGRATION_DELIVERY.md`. Publication sources: old `README.md`, `docs/README.md`, `docs/V1_DEPLOYMENT_GUIDE.md`, `docs/V1_DEMO_AND_DEFENSE.md`, `docs/reports/phase-09/V1_COMPLETION_REPORT.md`, `V1_REQUIREMENTS_AUDIT_2026-10-08.md`, `P9_CPU_24FPS_REPORT.md`, `P9C3I_INFERENCE_WORKER_LIFECYCLE_REPORT.md`, `V1_SPLIT_R2_QUALITY.md`, `V1_SPLIT_R2_EVALUATION.json`, P9-D and DeepSeek reports, and `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`.

Repository surfaces inventoried: `configs/`, `core/`, `services/`, `infra/`, `web/`, `scripts/`, `diagnostics/`, `tests/`, `locks/`, `data/`, `models/`, `docs/`, `examples/`, `artifacts/`, `pyproject.toml`, `.gitignore`. The code and tests were inspected for launch, detection, monitoring, event, Web, report, Agent and governance boundaries. Git-tracked LICENSE/COPYING, GitHub Actions and Release material were checked and are absent.

## Outdated Statements Found

The former README devoted most of its space to historical Phase 8 substeps and a long report index. It mixed Phase 0, historical inference and final-demo environment commands; the actual OpenVINO installation and asset restoration prerequisites were not centralized. Product presentation, metric test sets, performance conditions, a single limitations section and code-license disclosure were hard to find. Historical wording such as future Web or earlier Camera/RTSP pending states must not override the latest P9-B, P9-D and V1 records.

## Corrected Statements

The new root README leads with the present local V1 demonstration, six real capability groups, a runtime/training Mermaid diagram, the locked Windows environment path, two separately labeled model evaluations, bounded CPU performance evidence, and current limitations. It points to detailed historical reports instead of copying them. M-008 Camera acceptance is distinguished from remote RTSP validation; P9-C remains PARTIAL / FROZEN. Optional DeepSeek is downstream and read-only. Missing Git-ignored assets and absent independent source-code LICENSE are explicit.

## Claim Evidence Matrix

| Claim | Code / document evidence | Current status | README wording | Risk |
| --- | --- | --- | --- | --- |
| YOLO11 image/MP4 detection | `scripts/infer_image.py`, `scripts/infer_video.py`, Phase 4/P7 reports | Implemented; real image and 47-frame MP4 validated | Implemented with linked evidence | Model assets absent from Git |
| ByteTrack and association | `services/`, P9-B.3 review, Charter M-009/M-010 | Charter accepted for tested scope | Tracks person and retains unknown for ambiguity | Complex crossing/occlusion not broadly proven |
| Temporal events and storage | `services/`, `infra/`, ADR-024, P9-D vest report | Implemented; supplied MP4 full chain passed | Confirmed, deduplicated event and verified snapshot | Vest rule can change false-positive balance |
| Web, Camera and RTSP | `web/`, source adapters, P9-B.3/P9-D reports | Camera M-008 accepted; remote RTSP long behavior unverified; P9-D partial | Local MP4/USB, controlled local RTSP evidence | Browser cadence and remote recovery not inferred |
| Report and assistant | P8/P9-D reports, V1 real report validation, ADR-026/027 | Optional configured provider and validated fallback | Read-only, strict validation, marked degradation | Provider availability, persistent audit and production auth |
| Dataset identity / split R2 | Dataset Card, ADR-028, R2 quality/evaluation | Original 2603/114/82; R2 2603/116/80; train/checkpoint unchanged | Supplemental 80-image result | Hash/dHash checks have bounded coverage |
| Original model metrics | EXP-001 training execution report | Historical validation only | Separate metrics row | Not comparable as a controlled R2 improvement |
| CPU processing speed | P9 CPU report, ADR-025 | 28.836/29.414 FPS; real-alert 26.000 FPS on one MP4 | Exact CPU, input, resolution and pipeline conditions | Not universal USB/RTSP/browser FPS |
| Resource stability | P9-C.3i and risk register | P9-C PARTIAL / FROZEN | Correlation supported, owner and unbounded leak unknown | Long-run gate remains open |
| Deployment | V1 deployment guide, lock, preflight | Local Windows baseline; Git-ignored assets required | Reproducible commands and restoration warning | A clone alone is insufficient |
| Licenses | Dataset Card, Open Source Usage, Git-tracked file inventory | Dataset CC BY 4.0; Ultralytics AGPL-3.0; no project LICENSE | Separate disclosures | Public redistribution requires rights review |

## README Before / After Lines

The old file had 552 physical lines; the publication-ready revision has 139. This is below the requested approximate 180–260 range because historical subphase detail is linked rather than reproduced, while all required sections are retained.

## README Section Outline

Title and intro → Project display → Six capabilities → Mermaid architecture → Technology stack → PowerShell quick start → Dataset and training → Model and throughput metrics → Directory map → Status and limitations → Documentation navigation → Licenses and acknowledgments.

## Dataset and Model Metrics Verification

- Frozen source: 2,799 images; 2603/114/82; R2: 2603/116/80. Source: Dataset Card and R2 quality report.
- Original EXP-001 validation: P 0.899, R 0.649, mAP50 0.767, mAP50-95 0.480. Source: training execution report.
- R2 unchanged-checkpoint test, 80 images, seven classes: P 0.795859, R 0.709828, mAP50 0.729892, mAP50-95 0.462068. Source: R2 evaluation JSON.
- R2 train files and checkpoint unchanged; dHash threshold 5 and exact-hash cross-split candidates zero. This is not proof of all possible scene leakage.

## Runtime and Installation Verification

README commands follow `docs/V1_DEPLOYMENT_GUIDE.md`: verify `py -3.12 --version` reports Python 3.12.1 before creating the virtual environment; final-demo lock; OpenVINO 2025.2.0; `pip install --no-deps .`; preflight; local headless Streamlit on 8502. `pyproject.toml` has no automatic runtime dependencies. The lock pins the displayed core versions, and the local preflight confirms Python 3.12.1 and approved checkpoint on this machine. Another clone needs authorized asset restoration.

## Screenshot / Diagram Status

The linked screenshot `docs/reports/phase-09/P9D_DEEPSEEK_ASSISTANT_STATUS.png` is a Git-tracked real browser capture, inspected for secrets and presented with its actual timeout state. No screenshot was fabricated. Older local overview/monitoring captures depict an obsolete English UI; the monitoring capture also shows a person and full event ID, so they were not added. Current privacy-reviewed overview/monitoring/evidence captures remain a publication asset gap. The Mermaid diagram uses GitHub's `flowchart LR` syntax and separates training from runtime, with Agent downstream of persisted events; a GitHub rendered visual inspection is still recommended.

## License and Dependency Disclosures

No Git-tracked independent code LICENSE, LICENSE.md, LICENSE.txt or COPYING is present. README therefore does not select a code license. It distinguishes Construction Site Safety dataset CC BY 4.0 from Ultralytics AGPL-3.0, links the data origin and `docs/07_OPEN_SOURCE_USAGE.md`, and does not imply that a dataset license grants project-code rights.

## Internal Link Validation

README has 38 Markdown links, including 30 repository-relative links; all 30 targets exist. The linked image exists and is Git-tracked. The one internal heading anchor matches the displayed section. External URLs are source links, not part of the local existence check. Heading inspection found one H1 followed by H2 sections; code fences are balanced. Mermaid syntax was statically inspected, but GitHub rendering was not directly observed.

## Tests Executed and Actual Results

- Read-only Git identity and initial `git diff --check`: PASS.
- `scripts/preflight.py`: PASS on this workstation.
- `scripts/check_v1_delivery.py`: PASS, with RTSP/long stability excluded by its own scope.
- Documentation governance and reference-asset pytest: 38 passed.
- Full `pytest -q` with the final-demo Python: **810 passed in 320.17 seconds**.
- README-only publication refinement: documentation governance and reference-asset pytest **38 passed in 59.32 seconds**; full suite not rerun for this documentation-only follow-up.
- README links and image existence: PASS (30/30 internal targets).
- Pattern scan of the three changed documents: no API-key-like strings, token assignments or machine absolute paths.
- `git diff --check`: PASS; `git status --short` lists only the authorized README and two new documents. Git emitted only a line-ending conversion advisory, not a whitespace error.

Historical 810-pass evidence in the V1 report is not substituted for this run.

## Outstanding Publication Issues

1. Add a real, privacy-reviewed full-chain product screenshot after human capture and review.
2. Complete human review of README wording and GitHub-rendered Mermaid; P9-D responsive UI and P9-C resource gates retain their existing status.
3. Obtain a separate authorized code-license decision before claiming the repository is freely reusable.
4. Keep RTSP remote recovery, long stability, broad-scene accuracy, production authentication and durable Agent audit outside current acceptance claims.

## Changed Files and Final Decision

This task changes only `README.md`, this maintenance report, and one worklog / concise changelog entry if needed. Production code, frozen governance, models, data, dependency locks and status gates are untouched.

**README PUBLICATION READINESS: PARTIAL** pending human publication review and a stronger public product screenshot. All local documentation and regression checks above passed.

**P9-C: PARTIAL / FROZEN**

**PRODUCTION CODE MODIFIED: NO**

**GIT COMMIT/PUSH AT AUDIT REVIEW: NOT EXECUTED.** Subsequent publication requires explicit user authorization, which was granted after this audit; the resulting commit and remote ref must be verified separately.
