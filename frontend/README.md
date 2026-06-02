# Frontend

React/Vite dashboard shell for the Liaoning franchise contribution project.

## Run locally

```powershell
npm install
npm run dev
```

The dashboard fetches data from the backend API through the Vite `/api` proxy. Start `backend-api` first, or set `VITE_API_BASE_URL` for a deployed API. Current charts use ECharts for franchise ranking and province-weight contribution heatmap.

If PostgreSQL/backend is not available and you only need to inspect the page UI:

```powershell
$env:VITE_DEMO_MODE = "true"
npm run dev
```

Demo mode keeps the API path unchanged by default. It uses verified 202604 overview totals plus sample ranking and heatmap rows, and the page is explicitly marked as demo data.
