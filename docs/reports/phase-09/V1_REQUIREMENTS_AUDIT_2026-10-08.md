# V1 requirements audit — 2026-10-08

## Scope and result

Read-only audit requested by the user. Long-duration stability testing and its related freeze notices are excluded from this assessment only; no locked requirement, acceptance status or asset is changed.

Result: **Core functionality is substantially implemented; complete V1 acceptance is not established.** Requirements are evaluated from the locked Charter, current code, dated reports and fresh checks, rather than treating every historical pending status as missing code.

## MUST matrix

| MUST | Finding | Evidence / remaining condition |
| --- | --- | --- |
| M-001 | Partial acceptance | Conversion and auditable splits exist; docs/17_DATASET_QUALITY_REPORT.md records two valid/test perceptual duplicate candidates. No documented final review establishes no cross-split leakage. Candidates are not proof of confirmed leakage. |
| M-002 | Implemented, evidence present | Dataset quality service checks structure, images, labels, coordinates, classes, exact/perceptual duplicates; actual quality report exists. |
| M-003 | Partial | JSON and Markdown generation and distribution tables exist. Distribution chart artifacts/generation were not found in the inspected report writer. |
| M-004–M-005 | Accepted | Reproducible training and evaluation historically accepted in Charter. |
| M-006 | Implemented, runtime evidence | Image inference CLI and real image validation; final Charter disposition remains pending. A Streamlit image page is not explicitly required by the criterion. |
| M-007 | Implemented, runtime evidence | Annotated video script, real 47/47-frame output and human review; final Charter disposition remains pending. |
| M-008–M-010 | Accepted | P9-B.3 real Camera/ByteTrack/association review PASS. Camera OR RTSP satisfies M-008; remote RTSP validation is not an extra mandatory conjunction. |
| M-011–M-014 | Implemented, evidence present | Helmet/Vest, temporal confirmation, recovery and dedup tests; real events and ADR-authorized vest fix. |
| M-015–M-020 | Implemented, evidence present | SQLite/restart, snapshots, native Chinese TTS, realtime page, history/evidence and database-backed statistics. Chinese voice remains separate from English API alert text. |
| M-021 | Implemented; latest real report path needs reconfirmation | Historical real grounded provider report PASS; current DeepSeek report composition has offline tests. Latest live success is assistant planning/selection on temporary data, not a newly generated report from production events. |
| M-022–M-023 | Implemented, evidence present | Validated fallback and controlled query tools; latest real assistant flow success / assistant_llm. |
| M-024 | Coverage exists; current regression gate fails | Unit/integration/E2E present, historical real full chain PASS. Fresh fail-fast result: 1 failed, 52 passed in 36.11s. |
| M-025 | Incomplete delivery evidence | README exists but contains outdated P9-D authorization/native TTS statements. Dedicated current deployment, troubleshooting and recovery guide was not found. |
| M-026 | Partial | Demo/preflight scripts and many metrics/screenshots exist; unified repeatable final demonstration and defense-material index was not found. |

## Fresh checks

- scripts/preflight.py: PASS, including locked package versions, checkpoint hash, reference inference config hash and demo assets.
- Full pytest invocation advanced beyond 88%, showed two failures, then stalled without completing; stopped. No total PASS claim.
- Repeated pytest -q -x: **1 failed, 52 passed in 36.11s**.
- First failure: tests/integration/test_phase8_final_integration.py::test_streamlit_session_retains_projection_without_executing_on_rerun. Expected test-injected adapter call count 1, observed 0. Configuration fingerprint migration replaces an injected runtime lacking fingerprint metadata. This identifies a regression/test-contract mismatch; it does not by itself prove duplicate calls in the production UI. Full remaining regression must be rerun after resolution.
- Current CPU speed evidence is 26–29 processed FPS on one supplied MP4; do not extrapolate to USB/RTSP or universal detection accuracy. 24 FPS is a user-added performance target, not an original Charter acceptance threshold.

## Closure priorities (excluding stability)

1. Resolve session regression and obtain a complete current test result; isolate tests from local real-provider credentials.
2. Review the two near-duplicate candidates with a documented leakage disposition. Any dataset changes require separately authorized versioning/retraining; do not automatically delete candidates.
3. Supply the M-003 distribution charts.
4. Reconfirm current real DeepSeek report generation and fallback from the same persisted demo database.
5. Update README and complete deployment/troubleshooting guide and final demo/defense index.
6. Review final MUST acceptance and synchronize status fields only with sufficient evidence.

Long stability is excluded at the user's request. No new physical camera, remote RTSP, training, broad-scene evaluation or production browser walkthrough was executed. No business code, locked configuration, credential or Charter status was modified.
