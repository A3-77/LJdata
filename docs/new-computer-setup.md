# 新电脑运行与发布指南

这份文档给第一次拿到项目代码的人使用，目标是让另一台 Windows 电脑可以完成整套流程：

- 从 GitHub 克隆源码；
- 安装本地运行环境；
- 上传/导入每周 Excel 表格到 SQLite；
- 在 `http://127.0.0.1:5173/` 本地预览 React 看板；
- 生成确认后的静态快照；
- 通过 Cloudflare Pages Direct Upload 上传发布。

## 1. 推荐用 GitHub，不推荐压缩包

推荐方式：

```powershell
git clone https://github.com/A3-77/LJdata.git
cd LJdata
```

压缩包只适合作为离线备份。它不会包含 `.venv`、`node_modules`、`.runtime/dashboard.sqlite`、`.wrangler`、本地 Excel 文件、Cloudflare 登录状态。

## 2. 新电脑先安装这些软件

先安装：

```text
Git for Windows
Node.js 20 LTS 或更新版本
Python 3.11 或更新版本
```

正常本地流程不需要 Docker。默认数据库是 SQLite 文件：

```text
.runtime/dashboard.sqlite
```

## 3. 先检测环境

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

如果这台电脑还要负责上传 Cloudflare，再运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1 -CheckCloudflare
```

检测脚本不会安装东西，也不会改文件，只会告诉你缺什么。

## 4. 首次安装项目依赖

克隆后运行一次：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1
```

然后重新检测：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

## 5. 导入 Excel 到 SQLite

Excel 文件不放进 GitHub。把每周收到的表格放在新电脑任意位置，然后运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

当前 202604 测试表的正常结果大致是：

```text
franchise_rows: 155
site_rows: 293
region_contribution_flow_rows: 403
franchise_contribution_flow_rows: 4433
validation_failed: 0
```

## 6. 启动本地预览

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

这里的端口都是“当前这台电脑自己的本地端口”，不是写死到你的电脑，也不是公网地址。`127.0.0.1` 只表示正在运行命令的那台电脑自己。

打开：

```text
http://127.0.0.1:5173/
```

健康检查：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/ready
```

如果 `5173` 或 `8000` 被占用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -FrontendPort 5174 -BackendPort 8001
```

换端口后打开新的前端地址，例如：

```text
http://127.0.0.1:5174/
```

启动脚本会同步设置前端 API 代理，让前端请求新的后端端口。

## 7. 确认后上传 Cloudflare 快照

Cloudflare 登录状态不会保存在 GitHub。新电脑必须先登录：

```powershell
npx --yes wrangler login
```

也可以使用单独提供的 `CLOUDFLARE_API_TOKEN`，但不要把 token 写进仓库。

本地页面确认没问题后：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

当前默认 Pages 分支是 `test-4`。如果要手动指定：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -Branch "test-4" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```

只生成快照、不上传：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 -BuildOnly
```

## 8. 哪些东西不会跟着 GitHub 走

这些都是每台电脑本地生成的，已经被 Git 忽略：

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

如果另一个人需要看同一份数据，把 Excel 单独发给他，让他自己运行 `setup-sqlite-local.ps1` 导入。

## 9. 每周正常使用流程

```powershell
git pull
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\new.xlsx"
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

本地预览：

```text
http://127.0.0.1:5173/
```

确认后发布：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-cloudflare-snapshot.ps1 `
  -ProjectName "06-10-test-3" `
  -PeriodMonth "202604" `
  -RegionCode "LN"
```
