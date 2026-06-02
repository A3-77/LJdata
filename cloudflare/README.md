# Cloudflare

Cloudflare is used as the application edge layer, not the heavy import runtime.

## Responsibilities

```text
Pages: frontend hosting
Workers: API gateway and upload entry
R2: source Excel files and validation reports
Queues: import job dispatch
Workflows: optional long-running state orchestration
```

Excel parsing stays in the Python Import Service.

## Pages

Cloudflare Pages hosts the Vite frontend:

```text
Root directory: frontend
Build command: npm run build
Build output directory: dist
```

For production API access, either:

- route `/api/*` from Pages to the Worker on the same host and leave `VITE_API_BASE_URL` empty; or
- set `VITE_API_BASE_URL` to the Worker origin.

The frontend includes `public/_redirects` so SPA refreshes fall back to `index.html`.

## Worker

```powershell
cd cloudflare/workers
npm install
npm run dev
```

Bindings are declared in `wrangler.toml`.

The Worker keeps Excel upload handling at the edge:

- `POST /api/import/files` stores the source workbook in R2 and sends an import job message to Queue.
- `GET /api/*` proxies dashboard and import-status reads to `BACKEND_API_BASE_URL`.

Set `BACKEND_API_BASE_URL` to the FastAPI service origin in production. Cloudflare Pages can either call the Worker as `VITE_API_BASE_URL`, or route `/api/*` to the Worker through Cloudflare routing.
