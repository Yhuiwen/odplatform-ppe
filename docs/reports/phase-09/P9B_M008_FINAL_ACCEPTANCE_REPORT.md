# P9-B.2 M-008 Acceptance Assessment — 2026-09-25

**G10: PARTIAL; Phase 9 final Charter acceptance pending.** The Charter M-008 acceptance text requires Camera **or** RTSP live reading, detection and display, plus an observable disconnected/open failure without fabricated frame results. It does not require a remote RTSP session once the Camera path is established.

Real Camera 0 service run `20260925T101624Z-b0117ef1` processed 103 live frames, 309 detections, 103 track outputs and 206 associated PPE detections in 25.395 s. It produced real `NO_HELMET` and `NO_VEST` events at frame 4, two SQLite rows, two verified snapshots and four delivered Console/Web alerts. There were zero unknown associations and no service error. The failure run with invalid Camera index 64, `20260925T101723Z-4083b33b`, reported `SOURCE_OPEN_FAILED`, zero frames/events and no fabricated preview.

**VISUAL REVIEW BY ASSISTANT: PASS for the observed page behavior.** A real `streamlit run web/Home.py` browser session selected USB Camera 0. The browser showed live person frames, frames rising from 3 to over 200, detections/tracks updating, two recent violation events, Stop to STOPPED without error, second Start reopening Camera 0 and second Stop to STOPPED. Page switching retained the stopped session; Event Explorer showed six real browser-session Camera events, Evidence Viewer showed a `VERIFIED` snapshot, and Statistics showed total 6 (3 `NO_HELMET`, 3 `NO_VEST`). No raw traceback appeared. This was direct browser visual inspection, not AppTest. A separate person has not signed a human review.

The page's initial Start click left Stop disabled until a full-page rerun because button disabled state was computed before `service.start()`. The page now calls `st.rerun()` after Start and Stop; the browser verified Stop became enabled and Start disabled while RUNNING. Browser validation used an isolated `ODPLATFORM_P9B_VALIDATION_ROOT` so its SQLite, snapshots and JSON log did not enter historical release evidence.

The five processed-frame USB cycles exited normally, but a cold Stop requested after inference starts can still exceed the configured 5-second join and emit `MONITORING_STOP_TIMEOUT`; the worker subsequently releases the camera. The user instruction explicitly withholds G10 PASS when this timeout is not fully resolved. Accordingly, the M-008 final Phase 9 acceptance remains pending, even though the live Camera read/detect/display/failure path is evidenced. No remote RTSP run was needed or claimed.

## P9-B.3 Charter clarification

The preceding G10 PARTIAL judgement applied a five-second Stop bound from the prior P9-B.2 work instruction. The locked M-008 criterion contains no such bound: it requires Camera **or** RTSP live read/detect/display, observable failure and no fabricated frames. Existing real Camera and invalid-index evidence satisfies each clause. **G10 is re-adjudicated PASS on M-008's technical criterion.** Cold-inference Stop timeout remains an observable reliability limit and an M-018 safety-handling consideration; the worker ultimately exits and releases the camera. This clarification does not sign for the user or change Charter status. `HUMAN VISUAL REVIEW: AWAITING USER SIGN-OFF`; see `P9B3_CHARTER_GATE_READJUDICATION_REPORT.md`.

## P9-B.3 user sign-off closure

The user replied `pass` to the USB Camera 0 Realtime Monitoring visual checklist on 2026-09-25. **HUMAN VISUAL REVIEW: PASS; M-008 CHARTER ACCEPTANCE: PASS; G10: PASS.** The earlier pending statements remain historical. The locked Charter acceptance wording is unchanged; its M-008 status field is `已经实现`.
