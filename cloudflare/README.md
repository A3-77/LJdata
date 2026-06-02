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

## Worker

```powershell
cd cloudflare/workers
npm install
npm run dev
```

Bindings are declared in `wrangler.toml`.
