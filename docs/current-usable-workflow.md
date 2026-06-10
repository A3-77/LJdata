# 当前可用状态与操作手册

这套项目现在已经可以作为一个可用的本地审核 + 静态发布流程使用。

当前推荐链路是：

```text
Excel 表格 -> 本地 SQLite -> React 5173 预览 -> 生成静态快照 -> Cloudflare Pages Direct Upload
```

不需要 Docker，不需要本地 PostgreSQL，也不需要每次通过 GitHub 触发 Cloudflare 构建。

## 现在已经能做到

### 1. 新电脑环境检测

可以检测 Git、Node.js、npm、npx、Python、Python 虚拟环境、前端依赖、SQLite 数据文件、Cloudflare 登录状态。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

准备上传 Cloudflare 时：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1 -CheckCloudflare
```

### 2. 一键安装本地依赖

新电脑 clone 后运行一次：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1
```

这个脚本会安装 Python 后端/导入服务依赖、React 前端依赖、Cloudflare Worker 开发依赖。

### 3. 导入 Excel 到本地 SQLite

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

默认生成：

```text
.runtime/dashboard.sqlite
```

当前 202604 测试表已验证过：

```text
franchise_rows: 155
site_rows: 293
region_contribution_flow_rows: 403
franchise_contribution_flow_rows: 4433
validation_failed: 0
```

### 4. 在本地端口预览 React 看板

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

打开：

```text
http://127.0.0.1:5173/
```

默认端口：

| 端口 | 服务 | 说明 |
|---:|---|---|
| 5173 | React/Vite 前端 | 看板页面 |
| 8000 | FastAPI 后端 | API、上传、导入状态 |
| 8501 | Streamlit | 可选快速查看 |

这些端口都是当前电脑自己的本地端口。`127.0.0.1` 只表示正在运行命令的那台电脑，不是你的电脑，也不是服务器地址。

端口被占用时：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -FrontendPort 5174 -BackendPort 8001
```

启动脚本会自动把前端 API 代理指向新的后端端口。

### 5. 在页面里上传 Excel

本地看板的“数据导入”页面可以上传 Excel。上传会调用本地 FastAPI：

```text
POST /api/import/files
```

上传后的文件会保存在：

```text
data/uploads/
```

这个目录不会进入 GitHub。

如果不走页面，也可以用命令导入：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

### 6. 生成静态快照

本地看板确认没问题后，可以只生成快照、不上传：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 -BuildOnly
```

快照会生成到：

```text
snapshots/pages-<月份>-<时间戳>/
```

快照里已经嵌入当前本地 API 返回的数据。发布后不需要实时后端数据库。

### 7. 上传到 Cloudflare Pages

第一次在某台电脑上传前，需要登录 Cloudflare：

```powershell
npx --yes wrangler login
```

确认本地页面没问题后，一键生成并上传：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

当前默认 Cloudflare Pages 分支：

```text
test-4
```

如果要指定分支：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -Branch "test-4" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

发布后的页面是静态快照。它适合给别人看已经审核确认过的数据。

## 每周标准操作

### 第一次使用某台电脑

```powershell
git clone https://github.com/A3-77/LJdata.git
cd LJdata
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

如果这台电脑负责上传 Cloudflare：

```powershell
npx --yes wrangler login
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1 -CheckCloudflare
```

### 每周拿到新表格后

```powershell
git pull
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\new.xlsx"
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

打开本地看板检查：

```text
http://127.0.0.1:5173/
```

确认没问题后发布：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

如果新表格月份变了，把 `-PeriodMonth` 改成对应月份，例如：

```powershell
-PeriodMonth "202605"
```

## 现在暂时不能做到

- Cloudflare Pages 上的快照不是实时数据库页面，发布后是只读静态页面。
- Excel 不会自动从 Cloudflare 页面导入，仍然需要先在本地审核。
- Cloudflare 登录态和 API Token 不会跟随 GitHub，需要每台发布电脑单独登录或配置。
- 还没有自动定时发布。
- 还没有用户权限、多人审批、线上上传队列这类生产系统能力。
- 还没有把所有可能变化的 Excel 模板都做成可视化配置管理。

## 不需要关心的东西

正常每周流程不用 Docker。备用兼容说明已经单独放在：

```text
docs/optional-postgres-docker.md
```

正常使用时只看这几份文档即可：

```text
README.md
docs/current-usable-workflow.md
docs/new-computer-setup.md
docs/snapshot-deploy.md
```
