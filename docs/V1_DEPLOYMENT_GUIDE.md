# V1 local deployment and recovery

## Supported baseline

Windows local deployment, Python 3.12 and the pinned final-demo environment. CPU monitoring uses the project-trained checkpoint through the authorized OpenVINO 416 profile. Offline evaluation retains the original 640 profile. Camera or MP4 is the assessed V1 input; remote RTSP and long stability are excluded from this delivery review.

## Installation

From the project root in PowerShell:

```powershell
py -3.12 -m venv .venv-final-demo
& '.\.venv-final-demo\Scripts\python.exe' -m pip install -r locks/FINAL-DEMO-RUNTIME-001/requirements.txt
& '.\.venv-final-demo\Scripts\python.exe' -m pip install openvino==2025.2.0
& '.\.venv-final-demo\Scripts\python.exe' -m pip install --no-deps .
& '.\.venv-final-demo\Scripts\python.exe' scripts/preflight.py
```

Model files and dataset payloads are outside Git. Restore the approved OpenVINO export to `models/exports/best_cpu_416_openvino_model` and the approved checkpoint to `models/checkpoints/EXP-001/best.pt` from the authorized project artifact backup. Do not download substitute weights. A missing or mismatched artifact must fail preflight. For strict reproducibility use the final-demo dependency lock indexed in `docs/reports/phase-09/P9A_FINAL_DEMO_RUNTIME_FREEZE_REPORT.md`; historical `.venv-inference` is not the current web launch environment.

## Private DeepSeek configuration

Create `configs/llm.local.json` locally (already configured on this workstation):

```json
{
  "PPE_LLM_ENDPOINT": "https://api.deepseek.com/chat/completions",
  "PPE_LLM_MODEL": "deepseek-flash",
  "PPE_LLM_API_KEY": "YOUR_PROJECT_KEY"
}
```

This file is ignored by Git and overrides stale process/user variables. Never force-add it. Verify with `git check-ignore configs/llm.local.json` and `git ls-files configs/llm.local.json` (the latter must be empty). No key is needed to run the deterministic fallback. Do not paste credentials into screenshots, reports, logs or issue bodies.

## Launch and shutdown

```powershell
& '.\.venv-final-demo\Scripts\python.exe' -m streamlit run web/Home.py --server.port 8502 --server.address 127.0.0.1 --server.headless true
```

Open `http://localhost:8502/`. Stop detection in Monitoring before stopping the server with Ctrl+C. Binding to localhost avoids exposing the demo application; production authentication is outside this assessed local deployment. Use the Python command directly if PowerShell execution policy blocks `.ps1`; no system-wide policy change is needed.

## Data and backup

Persistent events: `artifacts/events/odplatform.sqlite3`; evidence is under `artifacts/events/snapshots`. Stop monitoring/server before copying the database and evidence together into a dated backup. Keep original file paths or restore the complete project-relative directory tree. SQLite status changes survive restarts. Never delete history to make a demo appear successful.

## Troubleshooting

| Symptom | Check and recovery |
| --- | --- |
| Port 8502 occupied | Identify the owning process with `Get-NetTCPConnection -LocalPort 8502`; stop the correct project server or choose another port. |
| Missing model/hash mismatch | Run preflight; restore the approved artifact. Do not edit expected hashes to bypass the check. |
| USB cannot open | Close other camera applications, check Windows camera permission and choose the correct camera ID; stop/restart detection. |
| Frozen/ended preview | Check processing state and frame counter. A completed MP4 must end; USB failure must be visible. Stop the session before restarting. |
| Low FPS | Confirm CPU-fast profile and OpenVINO export availability; inspect processed FPS rather than browser refresh alone. MP4 measurements do not guarantee USB throughput. |
| No event from one frame | Continuous confirmation intentionally requires multiple observations. Inspect PPE_UNKNOWN and evidence; never force a violation. |
| Alert total differs from event total | Alerts count channel deliveries; one event may deliver Console/Web/TTS messages. |
| No sound | Check Windows output/volume and SAPI; failures should be recorded without blocking event persistence. |
| LLM authentication/rate/timeout | Check local config and provider account; refresh after configuration changes. Fallback remains available. |
| Report refused/grounding fallback | Check selected date range and recorded data; provider statements must pass strict structure and grounding. |
| Evidence missing | Restore snapshots matching the database references. Do not invent placeholder evidence. |

## Verification commands

```powershell
& '.\.venv-final-demo\Scripts\python.exe' scripts/preflight.py
& '.\.venv-final-demo\Scripts\python.exe' -m pytest -q
```

Offline pytest isolates project-local provider configuration; real-provider validation is separate. Current gate and limitations are in the V1 completion report.
