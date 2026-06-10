# Quickstart

## 0. Recommended Scripts

The default local workflow now uses SQLite. Docker is not required.

Import the current Excel workbook into the local SQLite database:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

Start the local frontend and backend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

This starts:

```text
Frontend: http://127.0.0.1:5173/
Backend:  http://127.0.0.1:8000/health
Database: .runtime/dashboard.sqlite
```

PostgreSQL remains available as an optional compatibility path. Use it only when you specifically need to test the container/managed database setup:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-postgres-docker.ps1
```

If you only want to initialize PostgreSQL without importing Excel:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-postgres-docker.ps1 -SkipImport
```

## 1. Database

### Default: SQLite, no Docker

The scripts create and use:

```text
.runtime/dashboard.sqlite
```

To initialize SQLite without importing a workbook:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -SkipImport
```

To use another SQLite file:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -DatabaseUrl "sqlite:///.runtime/my-dashboard.sqlite" -Workbook "C:\path\to\workbook.xlsx"
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -DatabaseUrl "sqlite:///.runtime/my-dashboard.sqlite"
```

### Optional: PostgreSQL/Docker

Start local PostgreSQL:

```powershell
docker compose up -d postgres
```

Set the database URL and apply schema:

```powershell
$env:DATABASE_URL = "postgresql://dashboard:dashboard@localhost:5432/dashboard"
Get-Content database/migrations/001_init.sql -Encoding utf8 | docker compose exec -T postgres psql -U dashboard -d dashboard
Get-Content database/seeds/001_seed_core.sql -Encoding utf8 | docker compose exec -T postgres psql -U dashboard -d dashboard
```

Install Python dependencies once:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e import-service
.\.venv\Scripts\python.exe -m pip install -e backend-api
```

## 2. Import Service

Inspect the current sample workbook:

```powershell
$env:PYTHONPATH = "import-service/src"
.\.venv\Scripts\python.exe -m import_service.cli inspect "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx"
```

Validate workbook totals before loading:

```powershell
.\.venv\Scripts\python.exe -m import_service.cli validate "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx"
```

Load the current workbook into the configured database:

```powershell
.\.venv\Scripts\python.exe -m import_service.cli load-workbook "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx" --database-url $env:DATABASE_URL --replace-period
```

`load-workbook` creates or updates `source_file`, records one `import_job`, refreshes `source_sheet`, stores validation results in `import_validation_result`, and loads all currently supported fact tables.

Expected row counts for the 202604 test file:

```text
franchise_rows: 155
site_rows: 293
region contribution_flow_rows: 403
franchise contribution_flow_rows: 4433
```

## 3. Backend API

Run FastAPI:

```powershell
cd backend-api
$env:DATABASE_URL = "sqlite:///../.runtime/dashboard.sqlite"
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe -m uvicorn dashboard_api.main:app --reload --port 8000
```

Health check:

```text
http://localhost:8000/health
http://localhost:8000/ready
```

Dashboard checks:

```text
http://localhost:8000/api/dashboard/overview?period_month=202604&region_code=LN
http://localhost:8000/api/dashboard/franchises/rank?period_month=202604&region_code=LN&metric=total_contribution&direction=desc&limit=10
http://localhost:8000/api/dashboard/franchises/rank?period_month=202604&region_code=LN&metric=total_contribution&direction=asc&limit=10
http://localhost:8000/api/dashboard/sites/rank?period_month=202604&region_code=LN&metric=total_contribution&direction=desc&limit=12
http://localhost:8000/api/dashboard/contribution-flow/heatmap?period_month=202604&region_code=LN&scope_type=region&metric=contribution_total&province_limit=12
http://localhost:8000/api/import/jobs?period_month=202604&region_code=LN&limit=8
http://localhost:8000/api/import/jobs/latest?period_month=202604&region_code=LN
http://localhost:8000/api/import/jobs/1/validation-results
http://localhost:8000/api/import/jobs/1/errors
```

Upload and import from the API:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8000/api/import/files?region_code=LN&region_name=辽宁区域&template_code=franchise_contribution_v1&replace_period=true" `
  -Method Post `
  -Form @{ file = Get-Item "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx" }
```

The upload endpoint stores the workbook under `data/uploads/`, calls the existing `import-service` `load-workbook` command, records the import job, and refreshes the dashboard data. Configure the runner through:

```text
DASHBOARD_UPLOAD_DIR
DASHBOARD_IMPORT_PYTHON
DASHBOARD_IMPORT_SERVICE_SRC
DASHBOARD_DEFAULT_REGION_CODE
DASHBOARD_DEFAULT_REGION_NAME
DASHBOARD_DEFAULT_TEMPLATE_CODE
```

When PostgreSQL is selected but not running, dashboard endpoints return `503 database is unavailable` quickly instead of hanging. SQLite is the default for normal local development.

## 4. Frontend

Run the dashboard:

```powershell
cd frontend
npm install
npm run dev
```

The frontend uses Vite's `/api` proxy in local development. Start `backend-api` first. For a deployed API, set `VITE_API_BASE_URL`.

The default dashboard context is configured through Vite variables:

```powershell
$env:VITE_PERIOD_MONTH = "202604"
$env:VITE_REGION_CODE = "LN"
$env:VITE_REGION_LABEL = "辽宁"
$env:VITE_IMPORT_JOB_ID = "1"
$env:VITE_TEMPLATE_CODE = "franchise_contribution_v1"
```

Open:

```text
http://localhost:5173
```

If the API is not ready yet, run the frontend in explicit demo mode:

```powershell
cd frontend
$env:VITE_DEMO_MODE = "true"
npm run dev
```

Demo mode is only for UI inspection. It uses the validated 202604 overview totals and sample chart rows, while the normal mode reads the real backend API backed by SQLite or PostgreSQL.

## 5. Streamlit Quick Share

The Streamlit entry point is for quick sharing and review. It does not require PostgreSQL. Users upload one or more Excel workbooks in the browser, and the app parses KPI, validation, single-ticket contribution, Top 20/30 contribution concentration, franchise cards, combined tables, flow risk, and dispatch-fee proxy analysis in memory.

Run locally from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-streamlit.ps1
```

Open:

```text
http://localhost:8501
```

Deploy on Streamlit Community Cloud:

```text
Repository: A3-77/LJdata
Branch: main
Main file path: streamlit_app.py
```

No PostgreSQL secret is required for the current Streamlit quick-share version.

For handoff troubleshooting, see:

```text
docs/local-handoff.md
```

## 6. Cloudflare Worker

For the reviewed weekly snapshot flow, use Cloudflare Pages Direct Upload instead of a GitHub-triggered build:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-cloudflare-snapshot.ps1 -PeriodMonth "202604" -RegionCode "LN"
powershell -ExecutionPolicy Bypass -File scripts/deploy-cloudflare-snapshot.ps1 -SnapshotDir "snapshots/<snapshot-folder>" -ProjectName "<cloudflare-pages-project>"
```

Details are in:

```text
docs/snapshot-deploy.md
```

Run the Worker gateway:

```powershell
cd cloudflare/workers
npm install
npm run dev
```

Cloudflare Pages frontend deployment:

```text
Root directory: frontend
Build command: npm run build
Build output directory: dist
```

Set Pages environment variables from `frontend/.env.example`. In production, keep `VITE_DEMO_MODE=false`. Set `VITE_API_BASE_URL` only when the frontend calls a separate Worker origin; leave it empty when `/api/*` is routed to the Worker on the same host. For static snapshot uploads, the generated snapshot does not need a live database.

## 7. Backend Container

The Python backend is not deployed to Cloudflare Pages. Build it as a container from the repository root:

```powershell
docker build -f backend-api/Dockerfile -t liaoning-dashboard-backend .
```

Run it against local PostgreSQL:

```powershell
docker run --rm -p 8000:8000 `
  -e DATABASE_URL="postgresql://dashboard:dashboard@host.docker.internal:5432/dashboard" `
  liaoning-dashboard-backend
```

For production API hosting, deploy this container to a Python/container host and set:

```text
DATABASE_URL
API_CORS_ORIGINS
DASHBOARD_IMPORT_API_TOKEN
DASHBOARD_UPLOAD_DIR
DASHBOARD_IMPORT_SERVICE_SRC
```

## 8. Current MVP State

Implemented:

- PostgreSQL schema and core seed data.
- SQLite no-Docker local schema and workbook import script.
- Python workbook inspection, extraction, source file tracking, import job tracking, validation reporting, and SQLite/PostgreSQL loading CLI.
- FastAPI dashboard endpoints backed by SQLite locally or PostgreSQL when configured.
- React dashboard shell backed by API calls, with loading, error, empty states, ranking chart, province-weight heatmap, import diagnostics, import history selection, and workbook upload.
- Cloudflare Worker API gateway, R2 upload path, Queue producer, and Queue consumer handoff to the backend import runner.
- Local backend workbook upload endpoint that reuses the Python import CLI.
- Streamlit quick-share entry point with multi-workbook upload, single-ticket contribution review, franchise cards, combined table, flow risk, and dispatch-fee proxy analysis.

Next:

- Add asynchronous job execution for large workbooks so upload requests do not wait for the whole import.
- Choose the production backend container host and managed PostgreSQL provider if a live API is needed beyond static snapshots.
- Configure real Cloudflare account resources: Pages, Worker routes, R2 bucket, Queue, and secrets.
