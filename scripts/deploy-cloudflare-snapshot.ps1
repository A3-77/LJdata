param(
  [Parameter(Mandatory = $true)]
  [string]$SnapshotDir,
  [Parameter(Mandatory = $true)]
  [string]$ProjectName,
  [string]$Branch = "snapshot"
)

$ErrorActionPreference = "Stop"
$ResolvedSnapshotDir = (Resolve-Path $SnapshotDir).Path

if (-not (Test-Path (Join-Path $ResolvedSnapshotDir "index.html"))) {
  throw "SnapshotDir must point to a built Pages directory that contains index.html."
}

Write-Host "Deploying $ResolvedSnapshotDir to Cloudflare Pages project $ProjectName..."
npx wrangler pages deploy $ResolvedSnapshotDir --project-name $ProjectName --branch $Branch
