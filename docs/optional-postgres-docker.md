# Optional PostgreSQL / Docker Path

The normal weekly workflow does not use Docker:

```text
Excel -> SQLite -> React local preview -> Cloudflare Pages static snapshot
```

Keep this page only for compatibility testing or for a future live API deployment that needs PostgreSQL.

## Start PostgreSQL With Docker

```powershell
powershell -ExecutionPolicy Bypass -File scripts/optional/setup-postgres-docker.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

Initialize PostgreSQL without importing Excel:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/optional/setup-postgres-docker.ps1 -SkipImport
```

The compose file is intentionally outside the repository root:

```text
ops/docker/docker-compose.postgres.yml
```

The optional backend build ignore file is also isolated there:

```text
ops/docker/dockerignore.backend
```

Manual commands:

```powershell
docker compose -f ops/docker/docker-compose.postgres.yml up -d postgres
docker compose -f ops/docker/docker-compose.postgres.yml logs postgres
```

Use PostgreSQL with the local API only when explicitly testing this path:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 `
  -DatabaseUrl "postgresql://dashboard:dashboard@127.0.0.1:5432/dashboard"
```

## Optional Backend Container

Cloudflare Pages static snapshots do not need a backend container. Build this only when testing a live FastAPI deployment:

```powershell
docker build -f backend-api/Dockerfile -t liaoning-dashboard-backend .
```

Run it against PostgreSQL:

```powershell
docker run --rm -p 8000:8000 `
  -e DATABASE_URL="postgresql://dashboard:dashboard@host.docker.internal:5432/dashboard" `
  -e DASHBOARD_IMPORT_API_TOKEN="change-me" `
  liaoning-dashboard-backend
```

For the current handoff workflow, ignore this page.
