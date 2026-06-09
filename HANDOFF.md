# Handoff

## Recommended Transfer

Use a private GitHub repository for continued development.

Do not send source Excel files, `.env` files, local uploads, `.venv`, `node_modules`, or Docker volumes. They are intentionally ignored by Git.

## Local Requirements

- Git
- Node.js 20+
- Python 3.11+
- Docker Desktop

## First-Time Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e import-service -e backend-api

cd frontend
npm install
cd ..

cd cloudflare/workers
npm install
cd ..\..
```

## Run Locally

For packaged-code troubleshooting and the simplest reviewer workflow, see `docs/local-handoff.md`.

Start Docker Desktop first.

Initialize PostgreSQL and import the default workbook if the file exists on the desktop:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-postgres-docker.ps1
```

Start frontend and backend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open:

```text
http://127.0.0.1:5173/
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
| 8000 | FastAPI backend | Dashboard API, import status, workbook upload runner |
| 5432 | PostgreSQL Docker container | Local database |
| 8787 | Wrangler dev, optional | Cloudflare Worker local dev |
| 18000 | Temporary test only | Used when manually testing the backend container |

Expected local URLs:

```text
Frontend: http://127.0.0.1:5173/
Backend health: http://127.0.0.1:8000/health
Backend readiness: http://127.0.0.1:8000/ready
PostgreSQL: postgresql://dashboard:dashboard@127.0.0.1:5432/dashboard
```

## Backend API Surface

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

Local upload defaults to no token. Production can protect this endpoint with:

```text
DASHBOARD_IMPORT_API_TOKEN
X-Import-Token
```

## Cloudflare Worker Surface

```text
GET /health
POST /api/import/files
GET /api/*
```

Worker responsibilities:

- Receive workbook upload.
- Store the source workbook in R2.
- Send an import message to Cloudflare Queue.
- Queue consumer reads the workbook from R2.
- Queue consumer calls the backend `POST /api/import/files`.
- `GET /api/*` proxies dashboard reads to the backend.

Worker production variables and secrets:

```text
REGION_CODE
BACKEND_API_BASE_URL
IMPORT_API_TOKEN
SOURCE_FILES R2 binding
IMPORT_QUEUE Queue binding
```

## Current Development Progress

Implemented:

- PostgreSQL schema and seed data.
- Local PostgreSQL Docker Compose service.
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
- Optional backend import token for production.
- React/Vite dashboard shell.
- Overview, franchise, site, flow, deduction, and import views.
- Import history selection in the UI.
- Upload Excel from the import page.
- Demo data mode for frontend-only inspection.
- Local startup script.
- Local PostgreSQL setup/import script.
- Backend readiness check.
- Backend Dockerfile for container deployment.
- Cloudflare Pages config.
- Cloudflare Worker API gateway.
- Cloudflare R2 upload path.
- Cloudflare Queue producer and consumer.
- Streamlit quick-share version with Excel upload and in-memory parsing.

Verified locally:

- Frontend build passes.
- Backend compile passes.
- Import service compile passes.
- Cloudflare Worker typecheck passes.
- Docker backend image builds.
- Backend container `/health` runs.
- 202604 workbook imports successfully.
- Latest successful import job loaded 155 franchise rows, 293 site rows, 403 region flow rows, and 4433 franchise flow rows.

## Remaining Development Work

Highest priority:

- Choose a backend hosting target for the backend container.
- Choose managed PostgreSQL for production.
- Configure Cloudflare Pages, Worker, R2, Queue, and secrets in a real Cloudflare account.
- Set production `BACKEND_API_BASE_URL`.
- Set production `DASHBOARD_IMPORT_API_TOKEN` and Worker `IMPORT_API_TOKEN`.
- Run a production upload/import test.

Important engineering follow-ups:

- Make backend import execution asynchronous for large workbooks.
- Add a real job status record before parsing starts, so uploads can return immediately with a task id.
- Add user authentication or at least operator-level upload protection at the Worker layer.
- Add automated tests for parser totals, API contracts, and upload failure cases.
- Add database migration management beyond the current SQL file.
- Add rollback or archival rules for repeated imports of the same period.
- Add better frontend states for queued/running Cloudflare imports.
- Add pagination/search for full franchise and site detail.
- Add richer drilldowns for fee events, deductions, subsidies, and destination flow.
- Add template management for future workbooks with changed sheet names or headers.

Later / optional:

- Streamlit styling/polish beyond the current quick-share version.
- Cloudflare custom domain and access policy.
- Production monitoring and logs.
- Scheduled import or batch import mode.

## Current Known Good Data

For the 202604 Liaoning workbook:

```text
franchise_count: 155
site_count: 293
region_contribution_flow_rows: 403
franchise_contribution_flow_rows: 4433
validation_passed: 9
validation_failed: 0
```

## Useful Commands

```powershell
cd frontend
npm run build
```

```powershell
cd backend-api
..\.venv\Scripts\python.exe -m compileall src
```

```powershell
cd import-service
..\.venv\Scripts\python.exe -m compileall src
```

```powershell
cd cloudflare/workers
npm run typecheck
```

Run the Streamlit quick-share version:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-streamlit.ps1
```

## Streamlit Deployment

The Streamlit version is a separate lightweight entry point:

```text
streamlit_app.py
requirements.txt
```

It does not replace the React/FastAPI/PostgreSQL version. It lets a user upload an Excel workbook and inspect KPI, validation, ranking, site samples, and province-weight heatmap directly in Streamlit.

Deploy on Streamlit Community Cloud:

```text
Repository: A3-77/LJdata
Branch: main
Main file path: streamlit_app.py
```

No PostgreSQL secret is required for the current Streamlit quick-share version because it parses the uploaded workbook in memory.

## Deployment Shape

```text
Cloudflare Pages: frontend
Cloudflare Worker: upload gateway, R2, Queue
Backend container: FastAPI + import-service
PostgreSQL: managed database or Docker for local development
```
