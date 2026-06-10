# AI Operator Instructions

This repository is a usable local dashboard workflow:

```text
Excel workbook -> SQLite -> React local preview -> static snapshot -> Cloudflare Pages Direct Upload
```

Default local development does not use Docker.

## First Things To Read

Read these before changing code or operating the project:

```text
README.md
docs/current-usable-workflow.md
docs/new-computer-setup.md
docs/excel-template-change-playbook.md
docs/design-polish-guide.md
docs/snapshot-deploy.md
```

## Normal Weekly Operation

```powershell
git pull
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open:

```text
http://127.0.0.1:5173/
```

After local review:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

## If A Workbook Is Not Recognized

Do not guess, do not force import, and do not publish a snapshot from unverified data.

Follow:

```text
docs/excel-template-change-playbook.md
```

Minimum diagnostic sequence:

```powershell
$env:PYTHONPATH = "import-service/src"
.\.venv\Scripts\python.exe -m import_service.cli inspect "C:\path\to\workbook.xlsx"
.\.venv\Scripts\python.exe -m import_service.cli validate "C:\path\to\workbook.xlsx"
.\.venv\Scripts\python.exe -m import_service.cli extract franchise-summary "C:\path\to\workbook.xlsx" --limit 5
.\.venv\Scripts\python.exe -m import_service.cli extract site-summary "C:\path\to\workbook.xlsx" --limit 5
```

Common safe fixes:

- Sheet name changed only: update `sheet_name_patterns` in `import-service/src/import_service/templates.py`.
- Header/data rows shifted: update the relevant `SheetRule` rows in `templates.py`.
- Contribution matrix column groups shifted: update `DEFAULT_CONTRIBUTION_GROUP_STARTS` or add a new template profile.
- Meaning/metric columns changed: update parser mapping in `import-service/src/import_service/workbook.py` and validation rules.

Prefer adding a new template profile such as `franchise_contribution_v2` when the workbook structure materially changes. Keep `franchise_contribution_v1` working for old files.

## Required Verification Before Publishing

Run at least:

```powershell
python -m compileall backend-api/src import-service/src
cd frontend
npm run build
cd ..
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

Then open the local dashboard and check KPI totals against the import output before publishing.

## Do Not Commit

Do not commit:

```text
.venv/
node_modules/
.runtime/
.wrangler/
snapshots/
data/uploads/
*.xlsx
*.xls
*.csv
.env
```

## Cloudflare Notes

Cloudflare login state is local to each computer. If publishing fails, check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1 -CheckCloudflare
npx --yes wrangler login
```

Do not store Cloudflare API tokens in the repository.

## Design Notes

For UI polish, follow:

```text
PRODUCT.md
docs/design-polish-guide.md
```

Use the local design skills when available:

```text
impeccable
dashboard-dataviz
redesign-existing-projects
minimalist-ui
```

The dashboard should feel like a real operations tool: restrained, readable, auditable, and dense enough for repeated business use. Avoid generic AI dashboard patterns: decorative gradients, glass panels, excessive shadows, over-rounded cards, and flashy dark data-screen styling.
