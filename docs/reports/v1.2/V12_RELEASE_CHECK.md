# ODPlatform-PPE V1.2 Release Check

Date: 2026-10-10. Branch: main. Base HEAD: 1d283dcbe37d853dab3240ebe4cc6084c7be9e42. Target tag: v1.2.0 (new tag only).

## Scope and authorization

User explicitly authorized completing version alignment and audio/assistant validation, then commit/push/publish V1.2, temporarily accepting points 1 and 4 from the release audit. ADR-029 records this exception. Historical G-CFR-01/RISK-030 remains OPEN; P9-C remains PARTIAL/FROZEN. Neither is repaired or reclassified as PASS. Real-time/offline simultaneous execution remains deferred. This is a local demonstration release with known limits, not production readiness.

## Version alignment

front/package.json, both package-lock root version fields and pyproject.toml: 1.2.0. API health: 1.2.0. Dependency versions and frozen demonstration locks unchanged. README has current release scope, direct Python PowerShell startup and retained Streamlit rollback.

## Verification

- Frontend: npm test — 37 PASS; npm run build — PASS, existing bundle size warning.
- Independent API/business focused combined set — 134 PASS / 0 FAIL (72.80 seconds, release audit earlier in this session).
- Frozen business full regression — 820 PASS / 13 API file-level SKIP, 422.17 seconds; complete pytest suite via frozen interpreter with torch preloaded. No deselected tests. API skips use separate environment/historical real-media evidence, not counted as passes..
- compileall api services web offline and git diff --check — PASS.
- Two real supplied MP4 cached-audio runs — each completed, 570 frames, 2 confirmed events, 2 successful speech receipts. First 47.906 seconds includes cold initialization; second 14.406 seconds. Speech text only event type. Frame progress during playback: run1 71/110, run2 127/117 frames across sampled speech intervals. This proves detection progressed during speech; does not establish browser30FPS or human audibility. Isolated temporary SQLite/snapshots, no synthetic detection or replacement weights. First validation script failed because it used wrong receipt field; corrected instrumentation and repeated both runs.
- Actual configured provider — assistant_llm status; stored NO_HELMET/Track6 pending-event facts matched SQLite query, referenced images returned200, contextual interpretation included; assistant_mutations=false.
- Actual browser — pending details, two real event cards, model verified indicator, two loaded images, evidence zoom opened; 1366x768 and1920x1080 no document horizontal overflow, header/aside y=0, error logs empty.

Evidence: V12_RELEASE_CACHED_AUDIO_MP4.json; V12_RELEASE_ASSISTANT_PROVIDER.json; V12_RELEASE_ASSISTANT_BROWSER.json; screenshots/release-assistant-1366.png, release-assistant-1920.png, release-assistant-evidence-zoom.png.

## Known limitations retained

CFR intermittent rejection root cause unresolved. P9-C long stability unresolved. FullHD/4K/long videos and multi-browser/zoom coverage not established. Actual sound audibility requires human confirmation. Backend receipts are current-session memory only. AI interpretation remains selected validated contextual statements, no unrestricted generated facts or mutation. Single process offline scheduler and real-time/offline mutual exclusion retained.

## Git checks

Before staging, scan all modified/untracked candidates for secret patterns, prohibited source designs/model/video/database/build artifacts and large files; no such matches in prior166 candidate scan. Recheck final index before commit. Never overwrite or move existing tags. Publish v1.2.0 with known risks in release notes.


## Final decision

READY FOR AUTHORIZED RELEASE WITH KNOWN RISKS (ADR-029). Final frozen command: `.venv-final-demo/Scripts/python.exe -u -c "import torch, pytest; raise SystemExit(pytest.main(['-vv', '-x', '--tb=short']))"`;820 PASS/13 SKIP, exit0. Earlier two runs were interrupted after long silent scans (one reported1 failure without final diagnosis); neither counted as PASS. After all release documents existed, standalone governance31 PASS and full verbose rerun PASS. Detailed progress showed recursive asset/source scans, not evidence of an established native deadlock. No test requirements were relaxed.

Version changes only; frozen detector/configuration/training/locks unchanged. GitHub Release/tag creation is authorized, contingent on final index scan and remote fast-forward check; publication result is represented by the release URL and Git tag.
