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

Load the current workbook into PostgreSQL:

```powershell
.\.venv\Scripts\python.exe -m import_service.cli load-summary "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx" --database-url $env:DATABASE_URL --replace-period
.\.venv\Scripts\python.exe -m import_service.cli load-contribution-flow "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx" --database-url $env:DATABASE_URL --scope region --replace-period
.\.venv\Scripts\python.exe -m import_service.cli load-contribution-flow "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx" --database-url $env:DATABASE_URL --scope franchise --replace-period
```

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
http://localhost:8000/api/dashboard/franchises/rank?period_month=202604&region_code=LN&metric=total_contribution&limit=10
```

## 4. Frontend

Run the dashboard:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## 5. Cloudflare Worker

Run the Worker gateway:

```powershell
cd cloudflare/workers
npm install
npm run dev
```

## 6. Current MVP State

Implemented:

- PostgreSQL schema and core seed data.
- Python workbook inspection, extraction, and PostgreSQL loading CLI.
- FastAPI dashboard endpoints backed by PostgreSQL.
- React dashboard shell with verified sample values.
- Cloudflare Worker API gateway and upload queue skeleton.

Next:

- Replace frontend static data with API calls.
- Add ECharts implementations.
- Persist source_file and import_job records.
- Add validation report persistence.
