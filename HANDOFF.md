# Handoff

## Recommended Transfer

Use GitHub for continued development:

```powershell
git clone https://github.com/A3-77/LJdata.git
cd LJdata
```

Do not send source Excel files, `.env` files, local uploads, `.venv`, `node_modules`, local SQLite files, or Cloudflare login state through Git.

## New Computer Setup

Current usable workflow:

```text
docs/current-usable-workflow.md
```

Read:

```text
docs/new-computer-setup.md
```

First run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

## Normal Local Workflow

Import the workbook into SQLite:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

Start frontend and backend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open:

```text
http://127.0.0.1:5173/
```

These are local ports on the operator's own computer. `127.0.0.1` always means the machine running the command. If a port is occupied, use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -FrontendPort 5174 -BackendPort 8001
```

Health checks:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/ready
```

## Local Ports

| Port | Service | Purpose |
|---:|---|---|
| 5173 | Vite frontend | React dashboard UI |
| 8000 | FastAPI backend | Dashboard API and workbook upload runner |
| 8501 | Streamlit | Optional quick-share UI |

## Cloudflare Snapshot Upload

Cloudflare login is local to each computer. It is not stored in GitHub.

Check before publishing:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1 -CheckCloudflare
```

Login if needed:

```powershell
npx --yes wrangler login
```

Publish reviewed snapshot:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

## API Surface

Health and readiness:

```text
GET /health
GET /ready
```

Dashboard reads:

```text
GET /api/dashboard/overview
GET /api/dashboard/franchises/rank
GET /api/dashboard/sites/rank
GET /api/dashboard/contribution-flow/heatmap
```

Import job reads:

```text
GET /api/import/jobs
GET /api/import/jobs/latest
GET /api/import/jobs/{job_id}
GET /api/import/jobs/{job_id}/validation-results
GET /api/import/jobs/{job_id}/errors
```

Workbook upload:

```text
POST /api/import/files
```

## Current Development Progress

Implemented:

- SQLite no-Docker local workflow.
- Excel workbook inspection, validation, extraction, and load CLI.
- Template profile support through `franchise_contribution_v1`.
- Source file, source sheet, import job, validation result, and import error persistence.
- Dashboard overview API.
- Franchise ranking API.
- Site ranking API.
- Province and weight-band heatmap API.
- Latest import job and import history APIs.
- Import validation and error diagnostics APIs.
- Backend workbook upload API.
- React/Vite dashboard shell.
- Overview, franchise, site, flow, deduction, and import views.
- Import history selection in the UI.
- Upload Excel from the import page.
- Local environment check script.
- Local dependency bootstrap script.
- Local startup script.
- Cloudflare Pages Direct Upload snapshot scripts.
- Streamlit quick-share version.

Verified locally:

- Environment check script passes.
- Frontend build passes.
- Backend compile passes.
- Import service compile passes.
- 202604 workbook imports successfully into SQLite.
- Latest successful import job loaded 155 franchise rows, 293 site rows, 403 region flow rows, and 4433 franchise flow rows.

## Remaining Development Work

- Add asynchronous job execution for large workbooks.
- Add row-level parsing error persistence.
- Add automated tests for parser totals, API contracts, and upload failure cases.
- Add rollback or archival rules for repeated imports of the same period.
- Add pagination/search for full franchise and site detail.
- Add richer drilldowns for fee events, deductions, subsidies, and destination flow.
- Add template management for future workbooks with changed sheet names or headers.

## Optional Advanced Path

The normal handoff and weekly publishing workflow does not need Docker. Optional compatibility notes are isolated here:

```text
docs/optional-postgres-docker.md
```
