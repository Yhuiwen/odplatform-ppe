# Phase C-1 Batch-2B2 Frozen Manifest Chain Decision Audit

Date: 2026-09-23
Base HEAD: `a1011f30157e2cb6b057e2261b150186c59be099`
Status: decision audit only; no migration, commit or push.

## Scope

- The working tree was clean at entry. Batch-2A, Batch-2C and Batch-2B1 migrations are committed. This audit addresses only four remaining Phase 2 frozen-chain documents.
- The requested `DOCUMENT_GOVERNANCE_PHASE_C1_BATCH2B_AUDIT_REPORT.md` was explicitly deleted before Batch-2B1 and never committed, so it could not be pre-read. The current manifests, release record, prior Batch-2 audit, source files and tracked references were inspected instead.
- The task text lists all four under `docs/reports/`. In the actual repository, the three `P2-5.x` reports are at the repository root; only the P2-6 request is under `docs/reports/`. No file was moved.

## Candidate Inventory

| File | Type | Asset Relation | Current Path | Possible Target | Risk |
| --- | --- | --- | --- | --- | --- |
| `P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | configuration freeze report | EXP-001 config, dataset and mapping hashes; best-model manifest evidence | root `P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | `docs/reports/phase-02/P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | HIGH |
| `P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | initialization-weight registration report | `yolo11n.pt` provenance/hash; weight and best-model manifests | root `P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | `docs/reports/phase-02/P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | HIGH |
| `P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | runtime/dependency freeze report | EXP-001 lock files and runtime fingerprint; best-model manifest evidence | root `P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | `docs/reports/phase-02/P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | HIGH |
| `P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | one-run training authorization request | EXP-001 dataset, weight, runtime and best-model manifest evidence | `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | `docs/reports/phase-02/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | HIGH |

## Manifest Reference Analysis

| Source | Target | Reference Type | Active/Historical | Migration Impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml:305` | P2-6 request at `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | evidence path | ACTIVE frozen machine-readable record | A pure move leaves this path unresolved; changing it alters manifest bytes. | HIGH |
| `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml:306-308` | three root P2-5.x reports | evidence paths | ACTIVE frozen machine-readable record | A pure move leaves three paths unresolved; changing them alters manifest bytes. | HIGH |
| `EXP-001_RELEASE_MODEL.yaml:51-52` | best-model manifest, SHA256 `5f20a24869e1d481d0c05389cfe4541789c96a0caa0e2c282e8bb79ca3a66e0d` | path plus content hash | ACTIVE frozen release record | Any in-place edit to best-model manifest invalidates this hash. | HIGH |
| `docs/reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md:68,125` | release-model YAML and best-model manifest hashes | release evidence snapshot | HISTORICAL frozen report | Altering either frozen record would conflict with these dated hash statements; do not rewrite history. | HIGH |
| `tests/unit/test_training_preparation.py:30,37,51` | three root P2-5.x reports | fixed filesystem paths | ACTIVE test contract | A move requires path-only test changes; P2-6 has no direct test path here. | HIGH |
| `README.md:251,253`; Changelog; Test Gates; `docs/phases/PHASE_02_TRAINING.md` | P2-5.x reports | current navigation/evidence prose | ACTIVE index or gate entry | A move requires navigation path updates, but this does not repair the manifest chain. | MEDIUM |
| `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md:262-264`; P2-7 and Phase 2 release reports; archived worklog | P2-5.x/P2-6 reports | dated evidence prose | HISTORICAL record | Preserve these statements; they document the path at the time. | MEDIUM |

`docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` identifies the initialization weight and its path/hash but does not list these four report filenames. `EXP-001_RELEASE_MODEL.yaml` does not name the four directly; its hash binding to the best-model manifest creates the indirect dependency. No runtime script or config file directly names these four reports in the tracked text search. The model and dataset files themselves were not read or changed.

## Freeze Chain Analysis

| Candidate | Classification | Evidence carried | Consequence of moving without manifest handling |
| --- | --- | --- | --- |
| P2-5.1 configuration freeze | DOCUMENT_WITH_HASH_EVIDENCE + DOCUMENT_WITH_MANIFEST_REFERENCE + DOCUMENT_WITH_RELEASE_REFERENCE | Canonical training settings, dataset/mapping identity and SHA256 statements | Best-model manifest points to a missing root path; the release record's manifest hash cannot be maintained by silently editing it. |
| P2-5.2 weight registration | DOCUMENT_WITH_HASH_EVIDENCE + DOCUMENT_WITH_MANIFEST_REFERENCE + DOCUMENT_WITH_RELEASE_REFERENCE | `yolo11n.pt` local/remote path, provenance and SHA256 | Best-model manifest points to a missing root path; no weight file needs to move. |
| P2-5.3 dependency freeze | DOCUMENT_WITH_HASH_EVIDENCE + DOCUMENT_WITH_MANIFEST_REFERENCE + DOCUMENT_WITH_RELEASE_REFERENCE | Environment lock and runtime fingerprint hashes | Best-model manifest points to a missing root path; frozen runtime evidence remains separately fixed. |
| P2-6 authorization request | DOCUMENT_WITH_HASH_EVIDENCE + DOCUMENT_WITH_MANIFEST_REFERENCE + DOCUMENT_WITH_RELEASE_REFERENCE | One-run authorization boundary; dataset, weight and runtime evidence | Best-model manifest points to a missing flat-report path. |

The current best-model manifest SHA256 is `5f20a24869e1d481d0c05389cfe4541789c96a0caa0e2c282e8bb79ca3a66e0d`; the release-model YAML contains that exact value. The current release-model YAML SHA256 is `321703a6fecf316f65d05a675abb32cf4f3897f8a4b773e4e44eff467029c29b`, recorded in the Phase 3 final release report. This is a two-level immutable hash chain, not a set of ordinary Markdown links.

## Test Impact

| Test | Finding | Classification |
| --- | --- | --- |
| `tests/unit/test_training_preparation.py` | Hard-codes root paths for P2-5.1, P2-5.2 and P2-5.3; a move would require path-only updates and focused rerun. No direct P2-6 path was found. | Path update required for three reports. |
| `tests/unit/test_documentation_governance.py` | No direct reference to the four filenames or to the best-model manifest path was found; it covers document structure and local links. | No direct path update; rerun as governance validation. |
| Release/integrity checks outside those two modules | Manifest and release hashes are recorded as evidence; a new versioned chain would require semantic acceptance and appropriate integrity tests, not just a path string update. | Semantic update required only if option C is separately authorized. |

## Migration Decision

| Option | Assessment | Decision |
| --- | --- | --- |
| **A — keep original paths, update navigation only where helpful** | Preserves all frozen evidence paths, test contracts and release hash bindings. Current indexes already name the correct files; adding links may improve discoverability without changing identity. | **Recommended now for all four.** No move is needed or authorized. |
| **B — move documents without changing manifest** | All four manifest evidence paths would become stale. Updating only README, Changelog, Test Gates or tests cannot repair that gap. | **Reject for all four.** |
| **C — move documents and version manifest references** | Requires a new best-model manifest version and corresponding release record/evidence decision; old frozen manifest and release YAML must remain intact for historical verification. A pure move also breaks the old manifest unless old paths stay resolvable through preserved originals or another explicitly approved compatibility strategy. | **Possible future project-level decision**, not a routine archive step. Requires separate authorization and frozen-chain design. |

Per candidate: P2-5.1, P2-5.2 and P2-5.3 all have both manifest and test dependencies, so A is recommended; P2-6 has a manifest dependency without a direct test path, and A is likewise recommended. No candidate is DOCUMENT_ONLY. Do not infer that changing a manifest path is harmless because the report's own SHA256 could remain unchanged.

## Historical Integrity Preparation

These values identify the current files for any future separately authorized versioning exercise. No move is proposed by this audit.

| Current Path | Git blob ID | SHA256 | Possible Target |
| --- | --- | --- | --- |
| `P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | `8fe7e533ba26f80f7f6890f6f61ccb03d3f8b259` | `528e8a7851a8a90ef4e76bfe0b59a6823a72d9c117d8181641b62043cd77e294` | `docs/reports/phase-02/P2-5.1_CONFIGURATION_FREEZE_REPORT.md` |
| `P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | `1d55bc27a93717be7d16811426f6973fee631001` | `31c848dbb4a852265dd562e4b7b35533d77264b0be2faf04cf9a4d4ee2f892c1` | `docs/reports/phase-02/P2-5.2_WEIGHT_REGISTRATION_REPORT.md` |
| `P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | `9bba0e4d139e83a8ebf5e46952694fc46579f31d` | `330a0ac36a0951bbe09b9fc3dd99a19051ce0dffc07eb867c6a1e866b97af35f` | `docs/reports/phase-02/P2-5.3_DEPENDENCY_FREEZE_REPORT.md` |
| `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | `cae21e76713a5b63f2decaea901097ec3502df8c` | `022cd055dfc4ab01ecec6a4e19b33b2865a63c54ae7ea242c2707e12685ec48d` | `docs/reports/phase-02/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` |

## Required Actions

1. For the current project, keep all four documents at their present paths. If navigation is needed, link to those actual paths without editing frozen manifests or dated report prose.
2. If physical consolidation is later required, make a separate decision on versioning the best-model manifest and release evidence while retaining the original frozen chain and resolvable historical paths. Review any downstream hash references, Gate decisions and publication semantics before approving work.
3. In any approved future move, require `git mv`/`R100`, unchanged report Git blobs and SHA256, explicit test path updates, a complete local-link and evidence-path check, and focused training/release integrity tests. Do not move weights, datasets or experiment artifacts as part of document governance.

## Validation

- `git diff --check` and `git status --short` are checked after writing this report.
- Expected worktree change: this new Markdown audit report only. No test, YAML/JSON, manifest, code or asset change; no commit or push.
