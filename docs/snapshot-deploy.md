# Weekly Snapshot Deployment

Use this workflow for weekly Excel updates:

```text
Local debug: React on 5173
Snapshot build: static React bundle with embedded data
Production publish: Cloudflare Pages Direct Upload
```

## 1. Local Debug

Start the local React/FastAPI environment:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open:

```text
http://127.0.0.1:5173/
```

When PostgreSQL/Docker is available, import the new workbook and review the dashboard locally.

## 2. Build A Snapshot

Recommended one-command workflow after local review:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "<cloudflare-pages-project-name>" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

This checks `http://127.0.0.1:8000/ready`, builds a timestamped snapshot, and uploads it to Cloudflare Pages Direct Upload.

You can also save the Cloudflare project name once for the current PowerShell window:

```powershell
$env:CLOUDFLARE_PAGES_PROJECT = "<cloudflare-pages-project-name>"
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1
```

To only generate the snapshot without uploading:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 -BuildOnly
```

Manual two-step workflow:

After the local page looks correct, generate a static snapshot from the local API:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-cloudflare-snapshot.ps1 `
  -ApiBase "http://127.0.0.1:8000" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

The script:

- fetches dashboard API data from the local backend,
- temporarily writes `frontend/src/snapshotData.ts`,
- builds the React app with `VITE_SNAPSHOT_MODE=true`,
- copies `frontend/dist` into a timestamped `snapshots/` folder.

After the build, the source `frontend/src/snapshotData.ts` is restored, so the reviewed data is embedded in the generated `dist` snapshot without forcing a GitHub commit.

## 3. Deploy Directly To Cloudflare Pages

Login once if needed:

```powershell
npx --yes wrangler login
```

Deploy the generated snapshot:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy-cloudflare-snapshot.ps1 `
  -SnapshotDir "snapshots/pages-202604-YYYYMMDD-HHMMSS" `
  -ProjectName "<cloudflare-pages-project-name>"
```

This publishes the static snapshot directly to Cloudflare Pages. It does not require Streamlit and does not require a GitHub-triggered Pages build.

## Notes

- Snapshot pages are read-only. Upload/import buttons are disabled by behavior because `VITE_SNAPSHOT_MODE=true`.
- If the local API is not ready, fix the local dashboard first; do not publish a stale snapshot.
- Keep GitHub for source history. Use Cloudflare Direct Upload for the weekly reviewed release.
