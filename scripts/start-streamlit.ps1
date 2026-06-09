param(
  [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

function Test-Port {
  param([int]$Port)
  $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  return $null -ne $connection
}

if (-not (Test-Path $VenvPython)) {
  Write-Host "Creating .venv..."
  Push-Location $RepoRoot
  python -m venv .venv
  Pop-Location
}

Write-Host "Installing Streamlit dependencies..."
Push-Location $RepoRoot
& $VenvPython -m pip install -r requirements.txt
Pop-Location

if (Test-Port $Port) {
  Write-Host "Streamlit is already listening on http://127.0.0.1:$Port/"
  exit 0
}

$Stdout = Join-Path $RuntimeDir "streamlit.out.log"
$Stderr = Join-Path $RuntimeDir "streamlit.err.log"

Write-Host "Starting Streamlit..."
Start-Process `
  -FilePath $VenvPython `
  -ArgumentList @("-m", "streamlit", "run", "streamlit_app.py", "--server.port", "$Port", "--server.headless", "true") `
  -WorkingDirectory $RepoRoot `
  -WindowStyle Hidden `
  -RedirectStandardOutput $Stdout `
  -RedirectStandardError $Stderr | Out-Null

for ($i = 0; $i -lt 20; $i++) {
  if (Test-Port $Port) {
    Write-Host ""
    Write-Host "Streamlit dashboard:"
    Write-Host "  http://127.0.0.1:$Port/"
    Write-Host ""
    Write-Host "Logs:"
    Write-Host "  $RuntimeDir"
    exit 0
  }
  Start-Sleep -Seconds 1
}

Write-Host "Streamlit did not open on port $Port. Check logs:"
Write-Host "  $Stdout"
Write-Host "  $Stderr"
exit 1
