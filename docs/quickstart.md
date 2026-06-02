# Quickstart

## 1. Database

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

Load the current workbook into PostgreSQL:

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
$env:DATABASE_URL = "postgresql://dashboard:dashboard@localhost:5432/dashboard"
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe -m uvicorn dashboard_api.main:app --reload --port 8000
```

Health check:

```text
http://localhost:8000/health
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
```

Open:

```text
http://localhost:5173
```

If Docker/PostgreSQL is not ready yet, run the frontend in explicit demo mode:

```powershell
cd frontend
$env:VITE_DEMO_MODE = "true"
npm run dev
```

Demo mode is only for UI inspection. It uses the validated 202604 overview totals and sample chart rows, while the normal mode still reads the real backend API.

## 5. Cloudflare Worker

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

Set Pages environment variables from `frontend/.env.example`. In production, keep `VITE_DEMO_MODE=false`. Set `VITE_API_BASE_URL` only when the frontend calls a separate Worker origin; leave it empty when `/api/*` is routed to the Worker on the same host.

## 6. Current MVP State

Implemented:

- PostgreSQL schema and core seed data.
- Python workbook inspection, extraction, source file tracking, import job tracking, validation reporting, and PostgreSQL loading CLI.
- FastAPI dashboard endpoints backed by PostgreSQL.
- React dashboard shell backed by API calls, with loading, error, empty states, ranking chart, and province-weight heatmap.
- Cloudflare Worker API gateway and upload queue skeleton.

Next:

- Add import error row-level persistence.
- Wire Cloudflare Worker upload tasks to `load-workbook`.
