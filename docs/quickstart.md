# Quickstart

## 1. Database

Apply migrations to PostgreSQL:

```powershell
psql $env:DATABASE_URL -f database/migrations/001_init.sql
psql $env:DATABASE_URL -f database/seeds/001_seed_core.sql
```

## 2. Import Service

Inspect the current sample workbook:

```powershell
$env:PYTHONPATH = "import-service/src"
python -m import_service.cli inspect "C:\Users\A377\Desktop\辽宁区域_加盟商贡献表_202604（测试）.xlsx"
```

## 3. Backend API

Run FastAPI:

```powershell
cd backend-api
$env:PYTHONPATH = "src"
uvicorn dashboard_api.main:app --reload --port 8000
```

Health check:

```text
http://localhost:8000/health
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
- Python workbook inspection CLI.
- FastAPI endpoint skeleton with verified 202604 values.
- React dashboard shell with verified sample values.
- Cloudflare Worker API gateway and upload queue skeleton.

Next:

- Parse and persist `总表-加盟商`.
- Parse and persist `总表-网点`.
- Replace frontend static data with API calls.
- Add ECharts implementations.
- Add validation report persistence.

