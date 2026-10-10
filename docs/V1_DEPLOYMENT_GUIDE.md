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
# V1.2-F 本地前端补充

Vue新增 `/offline` 图片/视频/历史工作台；先在front执行 `npm ci`、`npm test`、`npm run build`，再从项目根目录执行 `scripts/start_frontend_local.ps1 -ApiPort 8768`。确认旧实例没有活动任务后退出旧实例，正式离线root只能运行一个Worker。独立测试设置ODPLATFORM_OFFLINE_ROOT到仓库外专属目录，避免测试ZIP触发资产门禁；Vite开发代理由VITE_API_TARGET指向实际API。原Streamlit回退方式保留。详见[工作台运行、测试与限制](reports/v1.2/V12_F_FRONTEND_REPORT.md)。F等待人工审核，P9-C保持未决，不自动发布。


## V1.2-G 部署与审核状态（2026-10-10）

当前离线流程、PowerShell启动/Ctrl+C安全停止、默认上传限额、音轨移除、原尺寸/CRF18有损、FIFO与取消/中断恢复、类别语义、回退开关详见 [V1.2用户指南](V1_2_OFFLINE_USER_GUIDE.md)。G首次CFR准入异常仍为发布阻塞，不能宣称全规格或长稳完成；[验收报告](reports/v1.2/V12_G_FINAL_ACCEPTANCE_REPORT.md)。API版本字段1.2.0不表示已发布。正式8768本轮未重启；仓库外root的单实例8775仅用于审核。P9-C PARTIAL/FROZEN；未commit/push/tag。
