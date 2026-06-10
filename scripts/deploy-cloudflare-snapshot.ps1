param(
  [Parameter(Mandatory = $true)]
  [string]$SnapshotDir,
  [Parameter(Mandatory = $true)]
  [string]$ProjectName,
  [string]$Branch = $(if ($env:CLOUDFLARE_PAGES_BRANCH) { $env:CLOUDFLARE_PAGES_BRANCH } else { "test-4" })
)

$ErrorActionPreference = "Stop"
$ResolvedSnapshotDir = (Resolve-Path $SnapshotDir).Path

if (-not (Test-Path (Join-Path $ResolvedSnapshotDir "index.html"))) {
  throw "SnapshotDir must point to a built Pages directory that contains index.html."
}

Write-Host "Deploying $ResolvedSnapshotDir to Cloudflare Pages project $ProjectName..."
npx --yes wrangler pages deploy $ResolvedSnapshotDir --project-name $ProjectName --branch $Branch
