# P9-B.3 Charter Gate Re-adjudication — 2026-09-25

## Final human sign-off addendum

The user replied **“pass”** on 2026-09-25 to the requested USB Camera 0 Realtime Monitoring visual checklist covering live preview/detection, growing frames/detections/tracks, violation events, Stop/restart, page return, and absence of crash, traceback or fabricated frames. **HUMAN VISUAL REVIEW: PASS.** G1–G13 are PASS; **P9-B RESULT: PASS**. P9-C remains NOT AUTHORIZED. The locked Charter descriptions and acceptance criteria remain unchanged; only evidence-backed M-008/M-009/M-010 status fields are updated to `已经实现`. The governance test assertions that hard-coded M-008 as pending were updated accordingly; final full regression after this edit: **684 passed, 0 failed**.

## 1. Charter authority and exact criteria

`docs/00_PROJECT_CHARTER.md` is the LOCKED TARGET DOCUMENT. Its MUST descriptions and acceptance criteria were not edited. The following quotations are the complete locked criteria relevant to this decision:

| ID | Locked acceptance criterion |
| --- | --- |
| M-008 | 支持 Camera 或 RTSP 流实时读取、检测和展示；断流失败可观察且不会伪造帧结果 |
| M-009 | 使用成熟依赖中的 ByteTrack 对 person 目标获取稳定 track ID，并记录跟踪配置和依赖版本 |
| M-010 | 将 Helmet/Vest 检测关联到对应人员；对可解释失败情况输出未关联结果而非错误归属 |
| M-018 | 页面可启动视频/流检测、显示状态与检测画面，并安全处理空模型、断流和停止操作 |

## 2. Requirement-to-evidence matrix

| Requirement / clause | Existing evidence | Satisfied? |
| --- | --- | --- |
| M-008 Camera **or** RTSP | Real USB Camera 0 opened and read live frames; RTSP is an alternative, not an additional required path | Yes |
| M-008 real-time read | 103 processed live frames in 25.395 s; earlier 143-frame Camera run | Yes |
| M-008 detect | Real YOLO inference: 309 detections in the 103-frame run; NO_HELMET/NO_VEST events | Yes |
| M-008 display | Direct Streamlit browser observation plus user PASS on the visual checklist | Yes; human review PASS |
| M-008 observable failure | Invalid Camera 64 returned SOURCE_OPEN_FAILED | Yes |
| M-008 no fabricated frames | Failure run had 0 frames, 0 events and no preview | Yes |
| M-009 mature ByteTrack on person | `ByteTrackPersonTrackingAdapter` uses Ultralytics BYTETracker with person-only filter | Yes |
| M-009 stable track ID | Real 103-frame USB trace contains track 1 in every processed frame, without observed switch or duplicate | Yes for the observed real scene |
| M-009 config/version recorded | Frozen `configs/tracker.yaml` records policy and Ultralytics 8.4.157; final-demo lock pins Ultralytics 8.4.157 and lap 0.5.13 | Yes |
| M-010 Helmet/Vest to corresponding person | 206 real PPE associations in USB run, with per-candidate confidence, bbox, containment and IoU; selected single visible person track 1 | Yes for observed scene |
| M-010 explainable failure unassociated | Real MP4 low-confidence no_vest is UNKNOWN with no track; deterministic ambiguity and failure tests cover no forced ownership; nearest-distance forced assignment disabled | Yes |
| M-018 start/status/display/stop | Real browser Start, live status/preview, Stop, restart and page return observed | Yes for these clauses |
| M-018 empty model/disconnect handling | Observable source-open failure is evidenced; empty-model and midstream-disconnect cases were not re-audited in P9-B.3 | Full M-018 Charter acceptance remains pending |

## 3. G8 re-adjudication

**P9B-G8: PASS on the locked criterion.** The authorized gate asks for Tracking/Association real-scene evidence recorded. A real USB scene supplies 103 per-frame track records and 206 per-candidate association measurements. The single observed person retained track 1; real associated and real UNKNOWN cases exist. The frozen ByteTrack configuration and dependency versions are recorded. This satisfies M-009 and M-010's stated acceptance clauses for the observed behavior.

Crossing, occlusion, re-entry, multiple-person ambiguity and zero switches across all possible scenes are not written in M-009/M-010 or G8. They remain known robustness coverage limits for later reliability analysis. This decision does not claim those behaviors were validated or that tracking is universally stable.

## 4. G10 re-adjudication and cold-inference Stop classification

**P9B-G10 / M-008: PASS; user visual review PASS.** Camera 0 satisfies the Charter's Camera **or** RTSP path. Real live read, detect and display were observed; index 64 gives an explicit failure and no fabricated result. Five real start/process/stop cycles ended normally. Remote RTSP is not an additional M-008 requirement once Camera is validated.

`MONITORING_STOP_TIMEOUT` remains possible when Stop arrives during an already-running, noninterruptible CPU cold inference. The timeout is reported; the worker later exits and releases the camera. The post-read extra-inference bug was fixed. M-008 does not prescribe a five-second Stop bound or preemptible inference, and G10 is defined as Camera-or-RTSP/M-008. Therefore this known limit does not negate M-008/G10. Under M-018's “安全处理…停止操作” clause, the explicit STOPPING/timeout indication, eventual worker exit and resource release constitute observable safe degradation in the exercised case. This is not a blanket acceptance of every M-018 clause; its Charter status is unchanged.

## 5. Human review and limitations

**ASSISTANT DIRECT BROWSER VISUAL CHECK: PASS. HUMAN VISUAL REVIEW: PASS.** The user replied “pass” to the specified live preview/detection, growing frames/detections/tracks, real events, Stop/restart, page return and absence of traceback, crash or fabricated frames checklist. No independent third-party reviewer is required by the Charter.

Known limitations rather than current G8/G10 blockers: controlled crossing/occlusion/re-entry and ambiguous two-person PPE scenes; remote RTSP; sustained construction-site violation MP4; a cold Stop may exceed the configured five-second join. These were not silently converted into MUST criteria. The actual evidence and scope are preserved in P9-B.2 reports.

## 6. G1–G13 final matrix

| Gate | Locked/authorized criterion | Current evidence | Result |
| --- | --- | --- | --- |
| G1 | Real MP4 full chain | Clean official service 47/47-frame run | PASS |
| G2 | SQLite | MP4/Camera event rows persisted, reopened and queried | PASS |
| G3 | Snapshot | Verified files, hashes and dimensions | PASS |
| G4 | Alert | Real Console/Web delivery, zero failure in runs | PASS |
| G5 | Dashboard | AppTest plus real browser Event Explorer/Evidence/Statistics | PASS |
| G6 | Analytics / Report / Agent | Same-DB grounded analytics/report/controlled Agent projections | PASS |
| G7 | Real event trace | MP4 PPE_UNKNOWN; Camera NO_HELMET and NO_VEST | PASS |
| G8 | Tracking/Association real-scene evidence | 103-frame IDs/bboxes/confidence; 206 candidate scores; associated and UNKNOWN cases | PASS |
| G9 | Temporal/dedup/recovery/cooldown | Deterministic gate tests plus real event confirmation | PASS |
| G10 | Camera or RTSP/M-008 | Real Camera read/detect/display, observable invalid index, no fabricated frame; user visual PASS | PASS |
| G11 | Full tests | Fresh `pytest -q`: 684 passed, 0 failed; compileall PASS | PASS |
| G12 | Frozen runtime/assets | Preflight lock checks, protected hashes, no protected edits | PASS |
| G13 | Git diff | `git diff --check` exit 0, no publication action | PASS |

## 7. Read-only MUST acceptance audit (M-004–M-024)

This matrix records current evidence tiers; it does not bulk-edit Charter statuses. “Pending” means no final Charter acceptance decision is made in P9-B.3.

| MUST | Implementation / runtime evidence | Charter disposition in this task |
| --- | --- | --- |
| M-004 | Reproducible training implemented and historically accepted | Existing `已经实现`; unchanged |
| M-005 | Evaluation implemented and historically accepted | Existing `已经实现`; unchanged |
| M-006 | Image detection implemented and runtime tested | Final acceptance pending |
| M-007 | Annotated MP4 implemented; real 47/47-frame validation and human review PASS | Phase 9 final acceptance pending |
| M-008 | Camera implementation and live runtime/browser/failure criterion satisfied; user visual PASS | `已经实现` accepted in P9-B |
| M-009 | ByteTrack implemented; real stable 103-frame trace and config/version recorded | `已经实现` accepted in P9-B |
| M-010 | Association implemented; real associated/UNKNOWN results and safety tests | `已经实现` accepted in P9-B |
| M-011–M-012 | Helmet/Vest rules implemented; real Camera violation events | Final acceptance pending |
| M-013–M-014 | Temporal confirmation/dedup implemented; deterministic and real-event evidence | Final acceptance pending |
| M-015–M-016 | SQLite/snapshot implemented; real rows and verified evidence | Final acceptance pending |
| M-017 | TTS implemented and Phase 7 runtime validated | Final acceptance pending |
| M-018 | Realtime page implemented; live browser and stop/failure evidence | Full Charter acceptance pending; cold Stop limit recorded |
| M-019–M-020 | Query/dashboard implemented; real Camera browser evidence | Final acceptance pending |
| M-021–M-023 | Phase 8 report/fallback/Agent implemented and released | Phase 9 final acceptance pending |
| M-024 | Unit/integration/E2E tests implemented; 684 passed | Final acceptance pending |

## 8. Regression, frozen assets and final result

In `.venv-final-demo-verify`, final `python -m pytest -q` after human sign-off and governance-test update returned **684 passed, 0 failed**; `compileall -q core infra services utils web scripts`, `scripts/preflight.py`, `scripts/run_demo.py --check`, `pip check` and `git diff --check` all passed. Preflight verified the pinned package set. `best.pt` SHA256 `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`; `configs/inference.yaml` `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`; final-demo lock `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4`; demo MP4 `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852`. No protected dataset, Phase 8 contract or historical tag change appears in the working diff. HEAD and origin/main remain `6c38a4ea51eec9a62f433683a3447c073852cbbd`; `phase-8-final-integration-complete` is unchanged. No production code or runtime package changed in P9-B.3; only the Charter status fields, documentation and outdated governance-test expectations changed.

**P9-B RESULT: PASS. P9-C NOT AUTHORIZED.** The user's visual PASS completes the P9-B sign-off. The Charter M-008/M-009/M-010 status fields are updated to `已经实现`; other MUST statuses and the locked criteria are unchanged.
