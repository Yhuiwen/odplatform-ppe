# Run from any directory; the credential stays in this process environment.
$projectRoot = Split-Path -Parent $PSScriptRoot
foreach ($settingName in @('PPE_LLM_ENDPOINT', 'PPE_LLM_MODEL', 'PPE_LLM_API_KEY')) {
    if (-not [Environment]::GetEnvironmentVariable($settingName, 'Process')) {
        $savedSetting = [Environment]::GetEnvironmentVariable($settingName, 'User')
        if ($savedSetting) { [Environment]::SetEnvironmentVariable($settingName, $savedSetting, 'Process') }
    }
}
if (-not $env:PPE_LLM_ENDPOINT) { $env:PPE_LLM_ENDPOINT = 'https://api.deepseek.com/chat/completions' }
if (-not $env:PPE_LLM_MODEL) { $env:PPE_LLM_MODEL = 'deepseek-flash' }
if (-not $env:PPE_LLM_API_KEY) {
    $secureKey = Read-Host 'Enter DeepSeek API Key (hidden)' -AsSecureString
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    try { $env:PPE_LLM_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer) }
}
if (-not $env:PPE_LLM_API_KEY) { throw 'API Key is required' }
$activeListener = Get-NetTCPConnection -LocalPort 8502 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($activeListener) {
    $activeProjectProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($activeListener.OwningProcess)"
    if ($activeProjectProcess.CommandLine -notmatch 'streamlit.*web[/\\]Home\.py') {
        throw 'Port 8502 belongs to another application'
    }
    Stop-Process -Id $activeListener.OwningProcess
}
Push-Location -LiteralPath $projectRoot
try {
    & (Join-Path $projectRoot '.venv-final-demo\Scripts\python.exe') -m streamlit run web/Home.py --server.port 8502 --server.headless true
}
finally { Pop-Location }
