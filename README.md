# 辽宁区域加盟商贡献数据看板

这是一个已经可运行的本地审核 + 静态发布项目，用于把每周收到的加盟商贡献 Excel 表格导入本地 SQLite，先在 React 看板中预览确认，再生成静态快照并上传到 Cloudflare Pages。

当前推荐链路：

```text
Excel 表格 -> 本地 SQLite -> React 5173 预览 -> 生成静态快照 -> Cloudflare Pages Direct Upload
```

默认本地流程不需要 Docker，不需要本地 PostgreSQL，也不需要每次通过 GitHub 触发 Cloudflare 构建。

## 当前能做什么

- 检测新电脑运行环境。
- 一键安装 Python / React / Cloudflare 相关依赖。
- 导入 Excel 到本地 SQLite。
- 在 `http://127.0.0.1:5173/` 本地预览 React 看板。
- 在看板“数据导入”页面上传 Excel。
- 生成带数据的静态快照。
- 用 Cloudflare Pages Direct Upload 发布快照。
- 默认端口被占用时切换本地端口。

完整说明见：

```text
docs/current-usable-workflow.md
```

## 快速开始

新电脑第一次运行：

```powershell
git clone https://github.com/A3-77/LJdata.git
cd LJdata
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

导入 Excel 并启动本地看板：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

打开：

```text
http://127.0.0.1:5173/
```

确认后生成并上传 Cloudflare 快照：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

如果这台电脑还没有登录 Cloudflare：

```powershell
npx --yes wrangler login
```

## 本地端口说明

这些端口都是运行者自己电脑上的本地端口。`127.0.0.1` 只表示当前运行命令的那台电脑。

| 端口 | 服务 | 说明 |
|---:|---|---|
| 5173 | React/Vite 前端 | 看板页面 |
| 8000 | FastAPI 后端 | API、上传、导入状态 |
| 8501 | Streamlit | 可选快速查看 |

如果默认端口被占用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -FrontendPort 5174 -BackendPort 8001
```

## 主要目录

| 目录 | 用途 |
|---|---|
| `docs/` | 当前可用流程、交接说明、快照发布说明 |
| `frontend/` | React/Vite 前端看板 |
| `backend-api/` | FastAPI 后端接口 |
| `import-service/` | Python Excel 导入、清洗、校验、入库服务 |
| `database/migrations/` | SQLite 本地建表脚本和历史 SQL |
| `scripts/` | 本地检测、安装、导入、启动、快照发布脚本 |
| `cloudflare/` | Cloudflare Worker/Pages 相关代码和配置 |
| `data/` | 本地临时数据目录，不提交正式 Excel |
| `ops/` | 可选高级运维内容 |

## 重要文档

```text
docs/current-usable-workflow.md   当前能做什么、每周怎么操作
docs/new-computer-setup.md        新电脑安装和运行指南
docs/snapshot-deploy.md           Cloudflare 快照生成和上传说明
docs/quickstart.md                快速启动命令
docs/local-handoff.md             本地交接说明
docs/optional-postgres-docker.md  可选备用 Docker/PostgreSQL 路线
```

## 本地生成且不会提交的内容

```text
.venv/
frontend/node_modules/
cloudflare/workers/node_modules/
.runtime/
.wrangler/
snapshots/
data/uploads/
*.xlsx
.env
```

如果另一个人需要看同一份数据，请单独发送 Excel，让他在自己电脑上运行导入脚本。

## 目前边界

- Cloudflare 上发布的是只读静态快照，不是实时数据库页面。
- Excel 仍然需要先在本地导入并审核。
- Cloudflare 登录态不会跟随 GitHub，需要每台发布电脑单独登录或配置 token。
- 暂未实现自动定时发布、多人审批、线上上传队列等完整生产系统能力。
