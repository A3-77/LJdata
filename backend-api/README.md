# Backend API

FastAPI service for dashboard queries, import status, and local workbook upload.

## Run Locally

Default local development uses SQLite:

```powershell
$env:DATABASE_URL = "sqlite:///../.runtime/dashboard.sqlite"
$env:PYTHONPATH = "src"
uvicorn dashboard_api.main:app --reload --port 8000
```

Or use the root helper:

```powershell
powershell -ExecutionPolicy Bypass -File ..\scripts\start-local.ps1
```

## Endpoints

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
POST /api/import/files
```

Dashboard responses query tables populated by `import-service`.

Use `/health` for process liveness and `/ready` for database readiness.

Optional advanced deployment notes are in:

```text
../docs/optional-postgres-docker.md
```
