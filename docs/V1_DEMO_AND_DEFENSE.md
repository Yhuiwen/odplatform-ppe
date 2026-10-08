# V1 demonstration and defense index

## Reproducible demonstration (about 10 minutes)

1. Run preflight, start the server using `docs/V1_DEPLOYMENT_GUIDE.md`, open Overview.
2. Open Monitoring, choose MP4, supply `artifacts/validation/test/4afa6b121fe5db806c3ff416bafdf571.mp4`; click Start once.
3. Show annotated processed frames, actual processed FPS and session state. Prior measured 26–29 FPS is evidence on this file, not a universal speed guarantee.
4. Let the clip finish. Show confirmed Helmet/Vest events if generated; unknown cases remain unknown. Record this run's actual results instead of assuming prior counts.
5. Event Explorer: filter this run's time/source, open a row in Evidence Viewer, show timestamp/track and actual snapshot.
6. Change an event to handled; refresh and verify persistent status. Statistics/Overview must agree with the same filtered database scope. Explain that channel alert deliveries differ from event count.
7. Safety Assistant: ask for event statistics and compare numbers with Statistics.
8. AI Report: select the same period, generate a report, show data scope, findings and evidence. If provider fails, show the marked local fallback and record the failure accurately.
9. Optional Camera demonstration: choose the real USB ID, click Start and Stop once and show observable state; remote RTSP is excluded.
10. Restart the server and verify historical event/evidence/status retention.

## Evidence to capture for this run

Overview; Monitoring annotated frame/FPS; Event Explorer filtered results; Evidence Viewer; handled status after refresh; Statistics; report/provider mode; assistant result; preflight/test summary. Preserve timestamps and raw IDs in validation records even though display tables hide IDs. Credentials must never appear in captures.

## Defense material index

| Topic | Evidence |
| --- | --- |
| Scope / architecture | docs/00_PROJECT_CHARTER.md; README.md |
| Dataset, labels and original quality | docs/06_DATASET_CARD.md; docs/17_DATASET_QUALITY_REPORT.md |
| Leak candidate disposition and new split | docs/reports/phase-09/V1_SPLIT_R2_QUALITY.md; V1_SPLIT_R2_REVISION.json |
| Training and metrics | docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml; docs/reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md |
| Real full chain | docs/reports/phase-09/P9B3_CHARTER_GATE_READJUDICATION_REPORT.md |
| CPU improvement | docs/reports/phase-09/P9_CPU_24FPS_REPORT.md |
| Event evidence/UI | docs/reports/phase-09/P9D_EVENT_OPERATOR_FLOW_REPORT.md; P9D_OVERVIEW_SOURCE_SORT_REPORT.md |
| LLM/Agent contracts | docs/03_TECHNICAL_DECISIONS.md ADR-026/027; Phase 8 reports |
| Local deployment/recovery | docs/V1_DEPLOYMENT_GUIDE.md |
| Current V1 closure | docs/reports/phase-09/V1_COMPLETION_REPORT.md |

## Suggested presentation outline

1. Problem and V1 scope (Helmet/Vest; no identity recognition).
2. Data preparation, split integrity and known original-metric caveats.
3. YOLO11n training and five PPE output classes; two scene classes remain training context.
4. ByteTrack → association → temporal confirmation → deduplication.
5. SQLite → evidence → alerts → UI operational handling.
6. CPU profiling and measured improvement with explicit test scope.
7. Grounded LLM report, fallback and controlled read-only Agent.
8. Live demonstration, tests, remaining limitations and next steps.

This is the defense content index and speaker outline; it does not claim a slide deck or a fresh human-reviewed full walkthrough was produced. Long stability and RTSP are excluded by the user; broad-scene accuracy, cloud/public deployment and multi-camera identity are not inferred.
