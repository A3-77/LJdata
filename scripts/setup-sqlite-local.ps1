param(
  [string]$Workbook = "",
  [string]$DatabaseUrl = "",
  [string]$RegionCode = "LN",
  [string]$RegionName = "",
  [string]$TemplateCode = "franchise_contribution_v1",
  [switch]$SkipImport
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $RepoRoot ".runtime"
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if (-not $DatabaseUrl) {
  $SqlitePath = (Join-Path $RuntimeDir "dashboard.sqlite").Replace("\", "/")
  $DatabaseUrl = "sqlite:///$SqlitePath"
}

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

if (-not (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe"))) {
  throw "Missing .venv. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e import-service -e backend-api"
}

Push-Location $RepoRoot
try {
  if (-not $SkipImport) {
    if (-not $Workbook) {
      throw "Workbook was not provided and no *202604*.xlsx file was found on the desktop. Pass -Workbook `"C:\path\to\file.xlsx`"."
    }
    if (-not (Test-Path $Workbook)) {
      throw "Workbook not found: $Workbook"
    }
    Write-Host "Importing workbook into SQLite..."
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
  } else {
    Write-Host "SkipImport enabled. SQLite schema will be created when the API or importer first connects."
  }
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "SQLite database is ready."
Write-Host "DATABASE_URL=$DatabaseUrl"
