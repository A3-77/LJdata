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

## Deployment Shape

```text
Cloudflare Pages: frontend
Cloudflare Worker: upload gateway, R2, Queue
Backend container: FastAPI + import-service
PostgreSQL: managed database or Docker for local development
```
