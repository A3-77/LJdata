param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [string]$PeriodMonth = "202604",
  [string]$RegionCode = "LN",
  [string]$ProjectName = $env:CLOUDFLARE_PAGES_PROJECT,
  [string]$Branch = $(if ($env:CLOUDFLARE_PAGES_BRANCH) { $env:CLOUDFLARE_PAGES_BRANCH } else { "test-4" }),
  [string]$SnapshotName = "",
  [switch]$SkipFetch,
  [switch]$SkipReadyCheck,
  [switch]$BuildOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if (-not $SnapshotName) {
  $SnapshotName = "pages-$PeriodMonth-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

$SnapshotDir = Join-Path (Join-Path $RepoRoot "snapshots") $SnapshotName

if (-not $SkipReadyCheck) {
  Write-Host "Checking local API: $ApiBase/ready"
  try {
    $Ready = Invoke-RestMethod -Uri "$ApiBase/ready" -TimeoutSec 10
    if ($Ready.status -ne "ready") {
      throw "API returned status '$($Ready.status)'"
    }
  } catch {
    throw "Local API is not ready. Start local services first with: powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1"
  }
}

Write-Host "Building snapshot: $SnapshotName"
& (Join-Path $PSScriptRoot "build-cloudflare-snapshot.ps1") `
  -ApiBase $ApiBase `
  -PeriodMonth $PeriodMonth `
  -RegionCode $RegionCode `
  -SnapshotName $SnapshotName `
  -SkipFetch:$SkipFetch

if (-not (Test-Path (Join-Path $SnapshotDir "index.html"))) {
  throw "Snapshot build failed. index.html was not found in $SnapshotDir"
}

if ($BuildOnly) {
  Write-Host ""
  Write-Host "BuildOnly enabled. Snapshot generated but not deployed:"
  Write-Host "  $SnapshotDir"
  exit 0
}

if (-not $ProjectName) {
  Write-Host ""
  Write-Host "Snapshot generated:"
  Write-Host "  $SnapshotDir"
  throw "Cloudflare Pages project name is required. Pass -ProjectName <name> or set `$env:CLOUDFLARE_PAGES_PROJECT."
}

Write-Host "Checking Cloudflare Wrangler login..."
try {
  npx --yes wrangler whoami | Out-Host
} catch {
  throw "Wrangler is not logged in. Run once: npx --yes wrangler login"
}

& (Join-Path $PSScriptRoot "deploy-cloudflare-snapshot.ps1") `
  -SnapshotDir $SnapshotDir `
  -ProjectName $ProjectName `
  -Branch $Branch

Write-Host ""
Write-Host "Done."
Write-Host "Snapshot:"
Write-Host "  $SnapshotDir"
Write-Host "Cloudflare project:"
Write-Host "  $ProjectName"
