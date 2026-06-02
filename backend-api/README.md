# Backend API

FastAPI service for dashboard queries and import status.

## Run locally

```powershell
$env:PYTHONPATH = "src"
uvicorn dashboard_api.main:app --reload --port 8000
```

## MVP endpoints

```text
GET /health
GET /api/dashboard/overview
GET /api/dashboard/franchises/rank
GET /api/import/jobs/{job_id}
```

Current responses use verified 202604 sample values. Replace with PostgreSQL queries after migrations are applied.
