# P9-B.1 Runtime Drift Repair — 2026-09-25

## Root cause and authorized repair

The first P9-B real ByteTrack run installed `lap==0.5.13` into the original `.venv-final-demo`. Ultralytics 8.4.157 imports `lap` in `trackers/utils/matching.py`; if absent it calls `check_requirements("lap>=0.5.12")`, whose default AutoUpdate path installs the package. The wheel's ordinary `Requires-Dist` list does not include `lap`, so the original 78-pin lock missed this lazy runtime dependency. This is a real matching dependency, not a logging issue.

The uncommitted `FINAL-DEMO-RUNTIME-001` lock was revised to include `lap==0.5.13` (79 pins). Root `requirements.txt` now declares it explicitly. Old lock SHA256: `3a22bc1a70801a318aff5e616472af3f3c9ecfb63c6c4e9bf9af370e359984`; revised lock SHA256: `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4`. `INF-RUNTIME-001`, model, dataset, inference configuration and Phase 8 contracts were not changed.

`scripts/preflight.py` now checks exact versions for every final lock pin and the named critical packages, including `lap`. An installed critical package omitted from the lock fails preflight. Normal extra installer tooling such as pip/setuptools is not treated as drift. New unit tests cover missing/mismatched transitive packages and the original unpinned-lap scenario.

## Independent clean environment and stability test

- Created Git-ignored `.venv-final-demo-verify` using Python 3.12.1, without copying the old virtual environment or global site packages.
- Installed revised lock and the local project with `pip install --no-deps .`. Install log: `artifacts/p9b/p9b1-clean-install.log`.
- Initial `pip check`: no broken requirements; enhanced preflight: PASS.
- Captured `artifacts/p9b/p9b1-before-freeze.txt` and `p9b1-before-inventory.json` before real inference.
- Executed `.venv-final-demo-verify/Scripts/python.exe scripts/run_p9b_full_chain.py --source mp4`, full stdout/stderr in `artifacts/p9b/p9b1-clean-mp4.log`. Run `20260925T093935Z-c9530763` completed 47/47 frames with real ByteTrack, one SQLite event and verified evidence.
- Captured `p9b1-after-freeze.txt` and `p9b1-after-inventory.json`. `Compare-Object` returned no `pip freeze` difference; package inventories were byte-for-byte equal. No `requirements missing`, `AutoUpdate`, `pip install lap`, `Installing collected packages`, or `Successfully installed` text appeared in the runtime log.
- After subsequent USB runs, `p9b1-after-usb-freeze.txt` also matched the before list; `pip check` remained clean.

**Runtime stability: PASS for the exercised real MP4 and USB paths.** The revised, still-unpublished `FINAL-DEMO-RUNTIME-001` may be called **RE-FROZEN / VERIFIED STABLE** only together with the final clean-environment regression result. This does not assert P9-B or Charter acceptance.

## Remaining limits

The original `.venv-final-demo` still contains the dynamically added package; it was not used for clean stability evidence. The check is exact for the 79 locked packages and named critical extras, not a rejection of every unrelated installed development tool. No historical release tag was changed.
