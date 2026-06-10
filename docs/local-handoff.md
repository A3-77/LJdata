# Local Handoff Guide

## Why A Packaged Copy May Not Open

This project has two local entry points, and they need different runtime pieces:

| Entry | Port | Needs | Use case |
|---|---:|---|---|
| Streamlit quick-share | 8501 | Python dependencies, uploaded Excel | Fast local review without database, supports one or more months |
| React dashboard | 5173 | Node.js frontend, FastAPI backend, SQLite file | Full engineering dashboard |
| FastAPI backend | 8000 | Python dependencies, SQLite by default | API for React dashboard |
| SQLite | file | Python standard library | Default persistent imported data |
| PostgreSQL | 5432 | Docker Desktop or local PostgreSQL | Optional compatibility/production database |

Common reasons another computer cannot open a local port:

- The server was not started. Opening `http://127.0.0.1:8501` only works after running the Streamlit command.
- Dependencies were not installed. A zip file does not include `.venv` or `node_modules`.
- The Excel data is not in the repository. `data/uploads/` is ignored by git, so the user must upload the workbook again.
- The full React version needs an imported SQLite database by default. If no workbook has been imported yet, the frontend may open but API data will be empty.
- The port is already occupied by another process. Use `-Port 8502`, `-FrontendPort 5174`, or another free port.
- Hidden files may be missed in a manual zip. Files like `.streamlit/config.toml` affect visual consistency.

## Recommended Way To Hand Off

Prefer GitHub over a manual zip:

```powershell
git clone https://github.com/A3-77/LJdata.git
cd LJdata
```

If a zip must be used, zip the repository root after pulling latest code, and include hidden files. Do not expect `.venv`, `node_modules`, database data, or uploaded Excel files to be inside the package.

## Fastest Local Start

For a non-technical reviewer, start with Streamlit:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-streamlit.ps1
```

Open:

```text
http://127.0.0.1:8501/
```

Then upload the Excel workbook in the left sidebar.

If port `8501` is busy:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-streamlit.ps1 -Port 8502
```

## Full Engineering Start

For the React/FastAPI/SQLite version:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open:

```text
Frontend: http://127.0.0.1:5173/
Backend:  http://127.0.0.1:8000/health
```

The default database file is:

```text
.runtime/dashboard.sqlite
```

Docker/PostgreSQL is now optional:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-postgres-docker.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -DatabaseUrl "postgresql://dashboard:dashboard@127.0.0.1:5432/dashboard"
```

## Why The Page May Look Different

Differences usually come from:

- Different Streamlit versions. `requirements.txt` is pinned to reduce this.
- Different theme settings. `.streamlit/config.toml` fixes the dashboard to a light theme.
- Different browser zoom, font rendering, or operating system.
- Different data. The uploaded workbook controls KPI, single-ticket contribution, concentration, flow risk, dispatch-fee proxy analysis, and validation results.
- Opening the wrong entry point. Streamlit and React are separate implementations.

Use Streamlit for quick sharing. Use React/FastAPI/SQLite for continued engineering work. Use PostgreSQL only when testing a live API deployment path.
