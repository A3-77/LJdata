param(
  [int]$FrontendPort = 5173,
  [int]$BackendPort = 8000,
  [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendDir = Join-Path $RepoRoot "frontend"
$BackendDir = Join-Path $RepoRoot "backend-api"
$RuntimeDir = Join-Path $RepoRoot ".runtime"
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if (-not $DatabaseUrl) {
  $SqlitePath = (Join-Path $RuntimeDir "dashboard.sqlite").Replace("\", "/")
  $DatabaseUrl = "sqlite:///$SqlitePath"
}

function Test-Port {
  param([int]$Port)
  $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  return $null -ne $connection
}

function Start-HiddenPowerShell {
  param(
    [string]$Name,
    [string]$Command,
    [string]$Stdout,
    [string]$Stderr
  )
  Write-Host "Starting $Name..."
  Start-Process `
    -FilePath "powershell" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $Command) `
    -WindowStyle Hidden `
    -RedirectStandardOutput $Stdout `
    -RedirectStandardError $Stderr | Out-Null
}

if (-not (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe"))) {
  throw "Missing .venv. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e import-service -e backend-api"
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
  Write-Host "Installing frontend dependencies..."
  Push-Location $FrontendDir
  npm install
  Pop-Location
}

if (Test-Port $BackendPort) {
  Write-Host "Backend already listening on http://127.0.0.1:$BackendPort"
} else {
  $backendCommand = "Set-Location -LiteralPath '$BackendDir'; `$env:PYTHONPATH='src'; `$env:DATABASE_URL='$DatabaseUrl'; & '..\.venv\Scripts\python.exe' -m uvicorn dashboard_api.main:app --host 127.0.0.1 --port $BackendPort"
  Start-HiddenPowerShell `
    -Name "backend-api" `
    -Command $backendCommand `
    -Stdout (Join-Path $RuntimeDir "backend.out.log") `
    -Stderr (Join-Path $RuntimeDir "backend.err.log")
}

if (Test-Port $FrontendPort) {
  Write-Host "Frontend already listening on http://127.0.0.1:$FrontendPort"
} else {
  $frontendCommand = "Set-Location -LiteralPath '$FrontendDir'; `$env:VITE_DEV_API_PROXY_TARGET='http://127.0.0.1:$BackendPort'; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
  Start-HiddenPowerShell `
    -Name "frontend" `
    -Command $frontendCommand `
    -Stdout (Join-Path $RuntimeDir "frontend.out.log") `
    -Stderr (Join-Path $RuntimeDir "frontend.err.log")
}

Write-Host ""
Write-Host "Local dashboard:"
Write-Host "  Frontend: http://127.0.0.1:$FrontendPort/"
Write-Host "  Backend:  http://127.0.0.1:$BackendPort/health"
Write-Host "  API proxy: http://127.0.0.1:$BackendPort"
Write-Host "  Database: $DatabaseUrl"
Write-Host ""
Write-Host "Logs:"
Write-Host "  $RuntimeDir"
