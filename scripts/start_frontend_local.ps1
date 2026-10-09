param([int]$ApiPort = 8765)
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv-frontend-api\Scripts\python.exe'
if (-not (Test-Path (Join-Path $root 'front\dist\index.html'))) { throw '请先在 front 目录执行 npm run build' }
if (-not (Test-Path $python)) { throw '请先安装独立 API 环境' }
Push-Location $root
try { & $python -m uvicorn api.main:app --host 127.0.0.1 --port $ApiPort }
finally { Pop-Location }
