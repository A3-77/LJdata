param(
  [switch]$SkipFrontend,
  [switch]$SkipWorker
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

function Require-Command {
  param([string]$Command)
  if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
    throw "Missing command: $Command. Install it, reopen PowerShell, then rerun this script."
  }
}

Push-Location $RepoRoot
try {
  Require-Command "python"
  Require-Command "npm"

  if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
  }

  Write-Host "Installing Python packages..."
  & $VenvPython -m pip install --upgrade pip
  & $VenvPython -m pip install -e import-service -e backend-api

  if (-not $SkipFrontend) {
    Write-Host "Installing frontend packages..."
    Push-Location (Join-Path $RepoRoot "frontend")
    npm install
    Pop-Location
  }

  if (-not $SkipWorker) {
    Write-Host "Installing Cloudflare Worker packages..."
    Push-Location (Join-Path $RepoRoot "cloudflare\workers")
    npm install
    Pop-Location
  }

  Write-Host ""
  Write-Host "Local dependencies are ready."
  Write-Host "Next: powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1"
} finally {
  Pop-Location
}
