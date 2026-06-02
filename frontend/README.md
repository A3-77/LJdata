# Frontend

React/Vite dashboard shell for the Liaoning franchise contribution project.

## Run locally

```powershell
npm install
npm run dev
```

The dashboard fetches data from the backend API through the Vite `/api` proxy. Start `backend-api` first, or set `VITE_API_BASE_URL` for a deployed API. Current charts use ECharts for franchise ranking and province-weight contribution heatmap.

The import validation view reads import job `1` by default. To inspect another job:

```powershell
$env:VITE_IMPORT_JOB_ID = "2"
npm run dev
```

For another workbook period or region, set these before starting Vite:

```powershell
$env:VITE_PERIOD_MONTH = "202605"
$env:VITE_REGION_CODE = "JL"
$env:VITE_REGION_LABEL = "吉林"
npm run dev
```

If PostgreSQL/backend is not available and you only need to inspect the page UI:

```powershell
$env:VITE_DEMO_MODE = "true"
npm run dev
```

Demo mode keeps the API path unchanged by default. It uses verified 202604 overview totals plus sample ranking and heatmap rows, and the page is explicitly marked as demo data.

## Cloudflare Pages

Use these settings for a Pages deployment:

```text
Root directory: frontend
Build command: npm run build
Build output directory: dist
```

Set `VITE_API_BASE_URL` to the Worker origin when Pages is not routing `/api/*` to the Worker. Leave it empty when `/api/*` is routed on the same host.

Use `frontend/.env.example` as the Pages environment variable template. `VITE_PERIOD_MONTH`, `VITE_REGION_CODE`, and `VITE_REGION_LABEL` control which imported period and region the dashboard requests.

`public/_redirects` keeps the React app working when a user refreshes a nested route.
