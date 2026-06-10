# Backend API

FastAPI service for dashboard queries and import status.

## Run locally

Default local development uses SQLite and does not require Docker:

```powershell
$env:DATABASE_URL = "sqlite:///../.runtime/dashboard.sqlite"
$env:PYTHONPATH = "src"
uvicorn dashboard_api.main:app --reload --port 8000
```

Or use the root helper:

```powershell
powershell -ExecutionPolicy Bypass -File ..\scripts\start-local.ps1
```

PostgreSQL is still supported when explicitly configured:

```powershell
$env:DATABASE_URL = "postgresql://dashboard:dashboard@127.0.0.1:5432/dashboard"
$env:PYTHONPATH = "src"
uvicorn dashboard_api.main:app --reload --port 8000
```

## Build container

Build from the repository root so the backend image can include both `backend-api` and `import-service`:

```powershell
docker build -f backend-api/Dockerfile -t liaoning-dashboard-backend .
```

Run with a PostgreSQL URL:

```powershell
docker run --rm -p 8000:8000 `
  -e DATABASE_URL="postgresql://dashboard:dashboard@host.docker.internal:5432/dashboard" `
  -e DASHBOARD_IMPORT_API_TOKEN="change-me" `
  liaoning-dashboard-backend
```

For production, use a managed PostgreSQL URL, set `DASHBOARD_IMPORT_API_TOKEN`, and let Cloudflare Worker call this backend origin.

## MVP endpoints

```text
GET /health
GET /ready
GET /api/dashboard/overview
GET /api/dashboard/franchises/rank
GET /api/dashboard/sites/rank
GET /api/dashboard/contribution-flow/heatmap
GET /api/import/jobs
GET /api/import/jobs/latest
GET /api/import/jobs/{job_id}
GET /api/import/jobs/{job_id}/validation-results
GET /api/import/jobs/{job_id}/errors
```

Dashboard responses query SQLite or PostgreSQL tables populated by `import-service`.

Use `/health` for process liveness and `/ready` for deployment readiness. `/ready` checks the configured database connection.
