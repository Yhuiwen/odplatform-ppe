param([int]$ApiPort = 8765)
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv-frontend-api\Scripts\python.exe'
if (-not (Test-Path $python)) { throw '请先安装独立 API 环境，见 docs/reports/frontend-v1.1/FRONTEND_ARCHITECTURE.md' }
$api = Start-Process -FilePath $python -ArgumentList '-m','uvicorn','api.main:app','--host','127.0.0.1','--port',"$ApiPort" -WorkingDirectory $root -WindowStyle Hidden -PassThru
try {
  Push-Location (Join-Path $root 'front')
  $env:VITE_API_TARGET = "http://127.0.0.1:$ApiPort"
  npm run dev
} finally {
  Pop-Location
  if (-not $api.HasExited) { Stop-Process -Id $api.Id }
}
