# Backend API

FastAPI service for dashboard queries and import status.

## Run locally

```powershell
$env:DATABASE_URL = "postgresql://dashboard:dashboard@localhost:5432/dashboard"
$env:PYTHONPATH = "src"
uvicorn dashboard_api.main:app --reload --port 8000
```

## MVP endpoints

```text
GET /health
GET /api/dashboard/overview
GET /api/dashboard/franchises/rank
GET /api/dashboard/sites/rank
GET /api/dashboard/contribution-flow/heatmap
GET /api/import/jobs/{job_id}
GET /api/import/jobs/{job_id}/validation-results
GET /api/import/jobs/{job_id}/errors
```

Dashboard responses query PostgreSQL tables populated by `import-service`.
