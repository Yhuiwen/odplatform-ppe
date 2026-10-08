# P9-A.1 FINAL RUNTIME FREEZE REPORT

Date: 2026-09-25. **P9-A RESULT: PASS.**
**FINAL-DEMO-RUNTIME-001: FROZEN / VALIDATED.**
**P9-B READY / WAITING FOR HUMAN AUTHORIZATION.**

## 1. PRE-READ

Re-read `AGENTS.md`, README, Master Plan, Current Status, Technical
Decisions, Test Gates, Risk Register, Phase 9 document and all three P9-A
reports. Phase 8 remains FINAL RELEASED. Only P9-A.1 is authorized; P9-B is
not. M-007 is implemented/real-MP4-validated/human-reviewed, with Charter
final acceptance pending in Phase 9. No new material governance conflict.

## 2. Git Identity

`main`; HEAD and `origin/main` both
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. Origin:
`https://github.com/Yhuiwen/odplatform-ppe.git`. Existing uncommitted P9-A
work was retained. No commit, tag, push, reset or force operation occurred.

## 3. Governance Test Repair

`tests/unit/test_documentation_governance.py` now requires M-007's
implementation PASS, real MP4 PASS, human review PASS and separate Phase 9
Charter final-acceptance pending wording; it rejects premature final
acceptance and retains M-008's pending assertion. The governance slice passed
`31 passed`. Project document scans now exclude the ignored virtual
environment; asset/secret scans likewise exclude that dependency directory.
`tests/__init__.py` prevents a third-party `tests` package from shadowing
local tests in a fresh installation.

## 4. Final Runtime Environment / 5. Dependency Versions

New `.venv-final-demo` created with `py -3.12 -m venv .venv-final-demo`.
Observed: Windows 11, AMD64, Python 3.12.1, pip 23.2.1, CPU only,
`torch.cuda.is_available() == False`. Core installed versions:

| Package | Version |
| --- | --- |
| torch | 2.5.1+cpu |
| torchvision | 0.20.1+cpu |
| ultralytics | 8.4.157 |
| opencv-python | 5.0.0.93 (`cv2.__version__` 5.0.0) |
| numpy | 2.2.6 |
| Pillow | 12.3.0 |
| Streamlit | 1.64.0 |
| pytest | 8.3.4 |
| pyttsx3 | 2.99 |
| plotly | 6.9.0 |
| PyYAML | 6.0.3 |

All 11 imported successfully. The lock contains 78 exact package pins from
the validated environment's `pip freeze`.

## 6. OpenCV Conflict Resolution / 7. pyproject Strategy

Root `requirements.txt` now pins `opencv-python==5.0.0.93`. Frozen
`configs/inference.yaml` and `locks/EVAL-001/requirements.txt` are unchanged.
`pyproject.toml` retains `dependencies = []` with an explicit comment:
package metadata is not the full runtime installer. The final-demo lock is
the authoritative install entry; `pip install --no-deps .` installs the
project package after runtime dependencies. Package import and metadata
version 0.1.0 were tested, and packaging consistency tests were added.

## 8. Clean Install Result / 9. pip check

The new environment installed exact CPU Torch wheels from the PyTorch CPU
index and the candidate package pins, then accepted the corrected root
requirements. `pip install --no-deps .` built/installed the local package;
`core`, `infra`, `services`, `utils`, `web` imported. `pip check`: **No broken
requirements found**. The generated lock passed `pip install --dry-run -r
locks/FINAL-DEMO-RUNTIME-001/requirements.txt` in this environment. A
second independent lock-only environment has not been constructed.

## 10. Full Pytest / 11. Compileall

Final clean-runtime full suite: `676 passed, 0 failed, 0 skipped`.
`python -m compileall -q core infra services utils
web scripts`: PASS. The earlier first-run failures were test namespace
shadowing and ignored virtual-environment files in repository scans; all were
repaired without changing frozen product logic.

## 12. Real Image Validation

Command: `.venv-final-demo/Scripts/python.exe scripts/run_image_validation.py
--config artifacts/validation/P9A_final_demo/image_validation.yaml`.
Input: existing P4C-1 public-domain JPEG, 1024x766. Exit 0, 5 detections,
frozen checkpoint hash matched. Cold start 11133.36 ms; warm inference
377.52 ms. Output is isolated under `artifacts/validation/P9A_final_demo`.

## 13. Real MP4 Validation

Command: `.venv-final-demo/Scripts/python.exe scripts/run_video_validation.py
--config artifacts/validation/P9A_final_demo/video_validation.yaml`.
Input: existing P4C-2 real MP4, SHA256
`b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852`.
Exit 0, 47/47 frames, 77 detections, 16.357 s, 2.873 processing FPS; no
silent frame skip. Frozen checkpoint and CPU device recorded in output.
This is runtime capability validation, not P9-B full pipeline acceptance.

## 14. Streamlit Validation

`.venv-final-demo/Scripts/python.exe -m streamlit run web/Home.py
--server.headless=true --server.port=18521`: server started; HTTP root 200.
AppTest imported/rendered Overview, Event Explorer, Evidence Viewer,
Statistics, Realtime Monitoring, AI Report and Safety Assistant with zero
exceptions. Old placeholder pages were not opened. Server was stopped after
the check.

## 15. TTS Validation / 16. USB Capability Check

One `TTSService.speak('安全告警测试')` call through Windows SAPI returned without
exception in 4.222 s. Audio intelligibility was not independently reviewed.
`USBCameraSource(0)` opened at 640x480/30 FPS, read 5 frames and closed.
This does not establish the Phase 9 USB full event chain.

## 17. Preflight Result / 18. run_demo Result

`scripts/preflight.py` is read-only; it checks OS/Python, lock pins, CPU/no
download policy, checkpoint size/hash, inference hash, database/snapshot
paths and demo asset existence. Unit tests cover pass, missing file, hash and
version mismatch, missing package and unsupported Python.
`python scripts/preflight.py`: PASS. `python scripts/run_demo.py --check`:
PASS. Plain `run_demo.py` passes preflight and prints the Streamlit command;
it does not launch devices, modify data or call a provider.

## 19. FINAL-DEMO-RUNTIME-001 Lock

`locks/FINAL-DEMO-RUNTIME-001/requirements.txt`: 78 exact installed pins,
SHA256 `3a22bc1a70801a318aff5e616472af3f3c9ecfb63c6c4e9bf9af370e359984`.
Python 3.12.1 / Windows 11 AMD64 / CPU only is the supported environment.
The earlier `INF-RUNTIME-001` Python 3.10.4 record remains immutable.

## 20. Files Changed

Runtime and delivery: `.gitignore`, `requirements.txt`, `pyproject.toml`,
`scripts/preflight.py`, `scripts/run_demo.py`, final lock, new packaging and
preflight tests, test-package marker and narrowly scoped environment-scan
test repairs. Updated P9-A state/report/README/changelog/gates/worklog.
Earlier P9-A governance clarifications and audit reports remain in the same
uncommitted worktree.

## 21. Frozen Asset Verification / 22. Historical Tag Verification

`best.pt`: 5,479,891 bytes, SHA256
`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
`configs/inference.yaml` SHA256
`0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`.
No Git diff for model, dataset identity, training/inference configs, Phase 8
schemas/contracts or product pipeline. `phase-8-final-integration-complete`
still targets HEAD; no historical tag changed.

## 23. Remaining P9-B Acceptance Gaps

Real full-chain MP4/USB/RTSP acceptance, crossing/occlusion cases, latency,
long-run stability, evidence destruction/reconciliation, Dashboard-to-Agent
upstream traceability and all Phase 9 Charter MUST acceptance remain pending.
Default Web Agent composition has `provider_client=None`; no provider request
was made. Runtime freeze does **not** mean P9-B full pipeline acceptance.

## 24. Final Gate

P9A-G1 through G13: PASS after final test/hash/diff verification.
No P9-B execution is authorized by this freeze.

**P9-A RESULT: PASS**

**FINAL-DEMO-RUNTIME-001: FROZEN / VALIDATED**

**P9-B READY / WAITING FOR HUMAN AUTHORIZATION**
