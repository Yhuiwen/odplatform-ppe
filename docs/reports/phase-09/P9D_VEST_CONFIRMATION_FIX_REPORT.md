# P9-D follow-up: vest confirmation false-negative repair

Date: 2026-10-07
Decision: **TARGETED FIX PASS / broader scene accuracy not yet established**

## Scope and authorization

The user approved a minimal rule repair for the missing `NO_VEST` event in `artifacts/validation/test/4afa6b121fe5db806c3ff416bafdf571.mp4`. ADR-024 records the authorized change to frozen vest confirmation semantics. Existing Phase 9 changes and the P9-C resource issue remain untouched.

## Before-state evidence

The video shows an unvested worker around seconds 3–6. Model detections include `no_vest`, but also intermittent `vest` at the same person. The old rule's longest uninterrupted `NO_VEST` sequence was 28 frames / 0.9 seconds; the required duration is one second. The existing database contained only `NO_HELMET` events for two runs of this video. A tested overlapping-box suppression candidate did not improve the longest run.

## Change

`core/rules/temporal_filter.py` now applies a bounded vest-specific evidence window. It requires a five-frame violation run, a one-second span between first and current violation, at least 60% violation observations within 1.5 seconds, and a current violation. Five compliant frames or loss of the track clear the candidate. Other event types use their original temporal confirmation path. No model, event schema, association thresholds, storage policy, or alert adapter changed.

## Validation

- Focused temporal/event tests: pass, including conflict recovery and compliant reset.
- Full pytest: **773 passed**.
- Read-only full-video replay: 570 frames, `NO_VEST` at source time 4.2 seconds on Track 4 and `NO_HELMET` at 14.767 seconds on Track 6; no other event.
- Isolated full-chain smoke: `artifacts/p9b/20261007T070737Z-82c133f8/outputs/full_chain.json` reports `completed`, 570 frames, 2 events, 2 SQLite rows, 2 verified evidence snapshots, 4 delivered alerts, 0 failed alerts.
- The new `NO_VEST` event is `EVT-06a4269825a048c0a94de881861e5a5d`, frame 126, evidence ratio 0.644, span 1.266667 seconds. Its confirming-frame confidence is 0.3007; this is not an aggregate confidence.
- Ordinary Streamlit rerun on the restarted service: 570 frames completed, 2 confirmed events. The monitoring table showed `未穿反光衣` on Track 4 and `未佩戴安全帽` on Track 6, both alerted. Event Explorer displayed both new persisted rows with evidence (`EVT-780a369b...` and `EVT-fa6ffeeb...`).

## Limitations

This one MP4 and synthetic negative tests do not establish false-positive performance across sites, lighting, occlusion, or camera angles. P9-C remains PARTIAL/FROZEN. The isolated smoke uses its own database; the subsequent ordinary Streamlit rerun wrote the two new rows to the dashboard database.

## Git

No commit, tag, or push. All pre-existing working-tree changes were preserved.
