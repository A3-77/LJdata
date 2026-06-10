# Quickstart

默认本地流程使用 SQLite，不需要 Docker。

## 1. 首次安装

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

## 2. 导入 Excel

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

默认数据库文件：

```text
.runtime/dashboard.sqlite
```

## 3. 启动本地看板

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

打开：

```text
Frontend: http://127.0.0.1:5173/
Backend:  http://127.0.0.1:8000/health
Ready:    http://127.0.0.1:8000/ready
```

如果端口被占用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -FrontendPort 5174 -BackendPort 8001
```

## 4. 常用检查

```powershell
python -m compileall backend-api/src import-service/src
```

```powershell
cd frontend
npm run build
cd ..
```

接口检查：

```text
http://127.0.0.1:8000/api/dashboard/overview?period_month=202604&region_code=LN
http://127.0.0.1:8000/api/dashboard/franchises/rank?period_month=202604&region_code=LN&metric=total_contribution&direction=desc&limit=10
http://127.0.0.1:8000/api/dashboard/sites/rank?period_month=202604&region_code=LN&metric=total_contribution&direction=desc&limit=12
http://127.0.0.1:8000/api/dashboard/contribution-flow/heatmap?period_month=202604&region_code=LN&scope_type=region&metric=contribution_total&province_limit=12
http://127.0.0.1:8000/api/import/jobs/latest?period_month=202604&region_code=LN
```

## 5. 本地上传导入

看板的“数据导入”页面会调用本地 FastAPI 上传接口。也可以直接调用：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/import/files?region_code=LN&region_name=辽宁区域&template_code=franchise_contribution_v1&replace_period=true" `
  -Method Post `
  -Form @{ file = Get-Item "C:\path\to\workbook.xlsx" }
```

上传的源文件保存在 `data/uploads/`，不会进入 Git。

## 6. 生成并上传 Cloudflare 快照

本地确认页面没问题后：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

只生成快照、不上传：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 -BuildOnly
```

更多说明见：

```text
docs/new-computer-setup.md
docs/snapshot-deploy.md
```

## 7. 当前已实现

- SQLite 本地数据库和导入脚本。
- Python Excel 检查、抽取、校验、入库 CLI。
- FastAPI 看板查询接口。
- React/Vite 本地看板。
- Cloudflare Pages Direct Upload 静态快照流程。
- Streamlit 快速分享版本。

高级备用路线见：

```text
docs/optional-postgres-docker.md
```
