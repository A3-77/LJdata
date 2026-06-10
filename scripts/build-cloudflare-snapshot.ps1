param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [string]$PeriodMonth = "202604",
  [string]$RegionCode = "LN",
  [switch]$SkipFetch,
  [string]$SnapshotName = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FrontendDir = Join-Path $RepoRoot "frontend"
$SnapshotRoot = Join-Path $RepoRoot "snapshots"
$SnapshotDataPath = Join-Path $RepoRoot "frontend\src\snapshotData.ts"
$OriginalSnapshotData = $null

if (-not $SnapshotName) {
  $SnapshotName = "pages-$PeriodMonth-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

try {
  if (-not $SkipFetch) {
    $OriginalSnapshotData = [System.IO.File]::ReadAllText($SnapshotDataPath)
    Write-Host "Creating snapshot data from $ApiBase..."
    Push-Location $RepoRoot
    node scripts/create-snapshot-data.mjs `
      --api-base $ApiBase `
      --period-month $PeriodMonth `
      --region-code $RegionCode `
      --output frontend/src/snapshotData.ts
    Pop-Location
  }

  Write-Host "Building React snapshot..."
  Push-Location $FrontendDir
  $env:VITE_SNAPSHOT_MODE = "true"
  $env:VITE_DEMO_MODE = "false"
  $env:VITE_PERIOD_MONTH = $PeriodMonth
  $env:VITE_REGION_CODE = $RegionCode
  npm install
  npm run build
  Pop-Location

  $SnapshotDir = Join-Path $SnapshotRoot $SnapshotName
  if (Test-Path $SnapshotDir) {
    Remove-Item -LiteralPath $SnapshotDir -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path $SnapshotDir | Out-Null
  Copy-Item -Path (Join-Path $FrontendDir "dist\*") -Destination $SnapshotDir -Recurse -Force

  Write-Host ""
  Write-Host "Snapshot ready:"
  Write-Host "  $SnapshotDir"
  Write-Host ""
  Write-Host "Preview locally:"
  Write-Host "  cd frontend"
  Write-Host "  npm run preview -- --host 127.0.0.1 --port 4173"
  Write-Host ""
  Write-Host "Deploy to Cloudflare Pages:"
  Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/deploy-cloudflare-snapshot.ps1 -SnapshotDir `"$SnapshotDir`" -ProjectName <cloudflare-pages-project>"
} finally {
  if ($null -ne $OriginalSnapshotData) {
    $Utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($SnapshotDataPath, $OriginalSnapshotData, $Utf8NoBom)
  }
  if ((Get-Location).Path -ne $RepoRoot) {
    Pop-Location
  }
}
