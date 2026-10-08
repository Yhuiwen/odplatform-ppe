# 2026-09-25 P9-A.1 Runtime Freeze

Changed: Governance test, isolated-environment scan tests, final-demo lock,
root OpenCV pin, packaging policy note, preflight, safe run_demo entry,
P9-A runtime reports and status documents.

Reason: Close the verified P9-A runtime and documentation gate without
changing frozen model, inference, tracking, association or rules contracts.

Validation: Clean Windows 11 AMD64/Python 3.12.1 CPU environment; `pip check`
PASS; full pytest `676 passed, 0 failed, 0 skipped`; compileall PASS; real JPEG 5 detections;
real MP4 47/47 frames and 77 detections; Streamlit HTTP 200 and seven page
imports; one native SAPI TTS call; USB camera five frames; preflight PASS.

Evidence: `docs/reports/phase-09/P9A_FINAL_DEMO_RUNTIME_FREEZE_REPORT.md`;
ignored `artifacts/validation/P9A_final_demo/` runtime results;
`locks/FINAL-DEMO-RUNTIME-001/requirements.txt`.

Risk: Full pipeline, long run, remote RTSP and Charter final acceptance remain
for P9-B and later gates. The lock was validated in the created clean
environment and dry-run parsed, not installed into a second fresh environment.

Not Verified: P9-B full-chain acceptance, provider calls and subjective TTS
audio quality.

Next Step: Human review of P9-A freeze; P9-B waits for explicit authorization.
