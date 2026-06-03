param(
  [string]$Workbook = "",
  [string]$DatabaseUrl = "postgresql://dashboard:dashboard@127.0.0.1:5432/dashboard",
  [string]$RegionCode = "LN",
  [string]$RegionName = "",
  [string]$TemplateCode = "franchise_contribution_v1",
  [switch]$SkipImport
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not $RegionName) {
  $RegionName = -join ([char]0x8FBD, [char]0x5B81, [char]0x533A, [char]0x57DF)
}

if (-not $Workbook) {
  $desktop = [Environment]::GetFolderPath("Desktop")
  $candidate = Get-ChildItem -LiteralPath $desktop -Filter "*202604*.xlsx" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if ($candidate) {
    $Workbook = $candidate.FullName
  }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker command was not found. Install and start Docker Desktop, then rerun this script."
}

if (-not (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe"))) {
  throw "Missing .venv. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e import-service -e backend-api"
}

Write-Host "Starting PostgreSQL container..."
Push-Location $RepoRoot
docker compose up -d postgres

Write-Host "Waiting for PostgreSQL health check..."
$ready = $false
for ($i = 1; $i -le 40; $i++) {
  $status = docker inspect --format "{{json .State.Health.Status}}" liaoning-dashboard-postgres 2>$null
  if ($status -match "healthy") {
    $ready = $true
    break
  }
  Start-Sleep -Seconds 2
}
if (-not $ready) {
  throw "PostgreSQL container did not become healthy. Check: docker compose logs postgres"
}

$schemaReady = docker compose exec -T postgres psql -U dashboard -d dashboard -tAc "select to_regclass('public.source_file')" 2>$null
if ($schemaReady -match "source_file") {
  Write-Host "Database schema already exists. Skipping migration."
} else {
  Write-Host "Applying database schema..."
  Get-Content "database/migrations/001_init.sql" -Encoding utf8 | docker compose exec -T postgres psql -U dashboard -d dashboard
}

$seedCount = docker compose exec -T postgres psql -U dashboard -d dashboard -tAc "select count(*) from dim_region" 2>$null
if ([int]$seedCount.Trim() -gt 0) {
  Write-Host "Seed data already exists. Skipping seeds."
} else {
  Write-Host "Applying seed data..."
  Get-Content "database/seeds/001_seed_core.sql" -Encoding utf8 | docker compose exec -T postgres psql -U dashboard -d dashboard
}

if (-not $SkipImport) {
  if (-not (Test-Path $Workbook)) {
    throw "Workbook not found: $Workbook"
  }
  Write-Host "Importing workbook..."
  $env:PYTHONPATH = "import-service/src"
  & .\.venv\Scripts\python.exe -m import_service.cli load-workbook `
    $Workbook `
    --database-url $DatabaseUrl `
    --region-code $RegionCode `
    --region-name $RegionName `
    --template-code $TemplateCode `
    --replace-period
  if ($LASTEXITCODE -ne 0) {
    throw "Workbook import failed with exit code $LASTEXITCODE"
  }
}

Pop-Location
Write-Host ""
Write-Host "Database is ready."
Write-Host "DATABASE_URL=$DatabaseUrl"
