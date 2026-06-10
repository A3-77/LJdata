param(
  [switch]$CheckCloudflare
)

$ErrorActionPreference = "Continue"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Failures = 0

function Write-Check {
  param(
    [string]$Name,
    [bool]$Ok,
    [string]$Detail,
    [string]$Fix = "",
    [switch]$Optional
  )

  if ($Ok) {
    Write-Host "[OK]   $Name - $Detail" -ForegroundColor Green
    return
  }

  if ($Optional) {
    Write-Host "[WARN] $Name - $Detail" -ForegroundColor Yellow
  } else {
    Write-Host "[MISS] $Name - $Detail" -ForegroundColor Red
    $script:Failures += 1
  }

  if ($Fix) {
    Write-Host "       Fix: $Fix" -ForegroundColor DarkGray
  }
}

function Test-CommandExists {
  param([string]$Command)
  return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-CommandOutput {
  param(
    [string]$Command,
    [string[]]$Arguments
  )

  try {
    $output = & $Command @Arguments 2>$null | Select-Object -First 1
    return ($output | Out-String).Trim()
  } catch {
    return ""
  }
}

function Test-VersionAtLeast {
  param(
    [string]$Actual,
    [string]$Minimum
  )

  try {
    return ([version]$Actual -ge [version]$Minimum)
  } catch {
    return $false
  }
}

Push-Location $RepoRoot
try {
  Write-Host "Checking local dashboard environment..." -ForegroundColor Cyan
  Write-Host "Repo: $RepoRoot"
  Write-Host ""

  $gitOk = Test-CommandExists "git"
  $gitVersion = if ($gitOk) { Get-CommandOutput "git" @("--version") } else { "" }
  Write-Check "Git" $gitOk $gitVersion "Install Git for Windows, then reopen PowerShell."

  $nodeOk = Test-CommandExists "node"
  $nodeVersionRaw = if ($nodeOk) { Get-CommandOutput "node" @("--version") } else { "" }
  $nodeVersion = $nodeVersionRaw.TrimStart("v")
  $nodeSupported = $nodeOk -and (Test-VersionAtLeast $nodeVersion "20.0.0")
  Write-Check "Node.js 20+" $nodeSupported $nodeVersionRaw "Install Node.js 20 LTS or newer."

  $npmOk = Test-CommandExists "npm"
  $npmVersion = if ($npmOk) { Get-CommandOutput "npm" @("--version") } else { "" }
  Write-Check "npm" $npmOk $npmVersion "Install Node.js, which includes npm."

  $npxOk = Test-CommandExists "npx"
  $npxVersion = if ($npxOk) { Get-CommandOutput "npx" @("--version") } else { "" }
  Write-Check "npx" $npxOk $npxVersion "Install Node.js, which includes npx."

  $pythonOk = Test-CommandExists "python"
  $pythonVersion = if ($pythonOk) { Get-CommandOutput "python" @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')") } else { "" }
  $pythonSupported = $pythonOk -and (Test-VersionAtLeast $pythonVersion "3.11.0")
  Write-Check "Python 3.11+" $pythonSupported $pythonVersion "Install Python 3.11 or newer and check 'Add python.exe to PATH'."

  $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
  $venvOk = Test-Path $venvPython
  Write-Check "Python virtualenv" $venvOk ".venv" "Run: powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1"

  if ($venvOk) {
    $pyDepsOutput = Get-CommandOutput $venvPython @("-c", "import fastapi, openpyxl, uvicorn; print('python deps ok')")
    Write-Check "Python dependencies" ($pyDepsOutput -eq "python deps ok") $pyDepsOutput "Run: .\.venv\Scripts\python.exe -m pip install -e import-service -e backend-api"
  }

  $frontendNodeModules = Join-Path $RepoRoot "frontend\node_modules"
  Write-Check "Frontend dependencies" (Test-Path $frontendNodeModules) "frontend/node_modules" "Run: cd frontend; npm install"

  $workerNodeModules = Join-Path $RepoRoot "cloudflare\workers\node_modules"
  Write-Check "Worker dependencies" (Test-Path $workerNodeModules) "cloudflare/workers/node_modules" "Run: cd cloudflare/workers; npm install" -Optional

  $sqlitePath = Join-Path $RepoRoot ".runtime\dashboard.sqlite"
  Write-Check "SQLite data file" (Test-Path $sqlitePath) ".runtime/dashboard.sqlite" "Run: powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook `"C:\path\to\workbook.xlsx`"" -Optional

  if ($CheckCloudflare) {
    if ($npxOk) {
      $wranglerVersion = Get-CommandOutput "npx" @("--yes", "wrangler", "--version")
      Write-Check "Wrangler CLI" ($wranglerVersion -ne "") $wranglerVersion "Run: npm install -g wrangler, or keep using npx --yes wrangler." -Optional

      $whoami = Get-CommandOutput "npx" @("--yes", "wrangler", "whoami")
      $loggedIn = $whoami -match "You are logged in|Account ID|email"
      Write-Check "Cloudflare login" $loggedIn ($whoami -replace "`r?`n", " ") "Run: npx --yes wrangler login, or set CLOUDFLARE_API_TOKEN." -Optional
    } else {
      Write-Check "Cloudflare login" $false "npx is missing" "Install Node.js first." -Optional
    }
  } else {
    Write-Host ""
    Write-Host "Cloudflare login was not checked. Use -CheckCloudflare when preparing snapshot upload." -ForegroundColor DarkGray
  }

  Write-Host ""
  if ($Failures -gt 0) {
    Write-Host "Environment check failed: $Failures required item(s) missing." -ForegroundColor Red
    exit 1
  }

  Write-Host "Environment check passed for required local development items." -ForegroundColor Green
} finally {
  Pop-Location
}
