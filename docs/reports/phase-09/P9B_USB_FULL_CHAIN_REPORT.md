# P9-B.1 USB Camera Full Chain — 2026-09-25

## Real 30-second business run

Clean `.venv-final-demo-verify`; `scripts/run_p9b_full_chain.py --source usb --camera-index 0 --seconds 30`; run `20260925T094052Z-24a066b4`. Device `usb:0` reported 640×480, source 30 FPS. MonitoringService stopped after 30.376 s with `error_code=None`, 143 frames processed (4.708 processing FPS), 432 detections, 143 track outputs, 288 association results (3 unknown), 2 events, 2 SQLite rows, 2 verified snapshots, 4 delivered Console/Web alerts and 0 alert failures. Final status retained `has_preview=True`. Detection classes: 144 person, 146 no_hardhat and 142 no_vest. Findings: 143 `NO_HELMET:violation`, 142 `NO_VEST:violation`, one `PPE_UNKNOWN:unknown`.

Real Camera event IDs: `EVT-36a94696a2944cd0a07bd8c6191d4d83` (`NO_HELMET`) and `EVT-766d4ad4760e45ca8731f68a91a729f0` (`NO_VEST`), both track 1 at frame 4. Source is a live USB camera, not a construction-site MP4; these are operational event-chain observations, not proof of a sustained construction video violation scene. Full raw trace: `artifacts/p9b/20260925T094052Z-24a066b4/outputs/full_chain.json`.

The Charter's M-008 wording requires Camera **OR** RTSP live reading, detection and display, plus observable failure without fabricated frames. This run establishes real Camera read/detection/tracking/event service output and a nonempty preview state. Prior Streamlit page tests establish the preview rendering binding; actual live page display was not independently visually reviewed in this run. Final Charter acceptance remains pending human Gate review.

## Failure and lifecycle

Index 64 run `20260925T094226Z-159cf2ed` exited 1 with `SOURCE_OPEN_FAILED`, zero frames/detections/events, no preview. This is observable failure without fabricated results.

Three short fresh-process start/stop attempts ended `stopped`, with processed-frame counts 1, 1 and 0. The 0-frame attempt was repeated for 10 seconds and read one frame. The 1-frame short attempts retained `MONITORING_STOP_TIMEOUT` even after later reaching `stopped`: cold model inference exceeded the configured stop wait. Therefore the short-cycle stop behavior is **PARTIAL**, and these runs are not evidence of clean bounded stop. The 30-second principal run stopped without error; a subsequent independent `USBCameraSource(0)` open/read/close succeeded with state `closed`, showing the device could be reacquired. No physical unplug test was attempted. Source logs: `artifacts/p9b/p9b1-usb-*.log`.

## P9-B.2 follow-up

Five real start/processed-frames/stop cycles in `20260925T101508Z-04cd2839` each processed four frames, exited their worker, closed the source and ended STOPPED with no error. A 103-frame Camera run `20260925T101624Z-b0117ef1` yielded two verified violation events and no error. The live browser displayed changing frames, counters and recent events, then stopped and restarted Camera 0 successfully. Invalid index 64, run `20260925T101723Z-4083b33b`, remained `SOURCE_OPEN_FAILED` with zero frames/events. A Stop request during an inference already in progress can still time out after five seconds; G10 remains PARTIAL pending that lifecycle edge and a separate human sign-off. See `P9B_MONITORING_STOP_LIFECYCLE_REPORT.md` and `P9B_M008_FINAL_ACCEPTANCE_REPORT.md`.
