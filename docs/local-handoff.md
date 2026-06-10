# Local Handoff Guide

## 为什么 clone 或压缩包不能直接打开

GitHub 只保存源码，不保存每台电脑本地生成的运行环境：

```text
.venv/
node_modules/
.runtime/dashboard.sqlite
.wrangler/
data/uploads/
*.xlsx
```

所以新电脑需要先安装依赖，再导入 Excel。

## 推荐交接方式

推荐用 GitHub：

```powershell
git clone https://github.com/A3-77/LJdata.git
cd LJdata
```

压缩包只适合临时离线备份。即使使用压缩包，也不要指望里面带有 Python 虚拟环境、Node 依赖、本地数据库、Excel 源文件或 Cloudflare 登录状态。

## 新电脑第一步

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
powershell -ExecutionPolicy Bypass -File scripts/bootstrap-local.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-local-env.ps1
```

## React/FastAPI/SQLite 完整本地启动

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

打开：

```text
http://127.0.0.1:5173/
```

`127.0.0.1` 是每台电脑自己的本地地址。端口 `5173`、`8000`、`8501` 是默认值，不是绑定在某一台电脑上的固定资源。

默认数据库文件：

```text
.runtime/dashboard.sqlite
```

如果默认端口被占用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -FrontendPort 5174 -BackendPort 8001
```

## Streamlit 快速查看

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-streamlit.ps1
```

打开：

```text
http://127.0.0.1:8501/
```

然后在页面里上传 Excel。

## 页面看起来不一样的常见原因

- 没有导入同一份 Excel。
- 依赖没安装完整。
- 打开了错误入口，Streamlit 和 React 是两套界面。
- 浏览器缩放、系统字体或屏幕尺寸不同。
- 本地端口被其他程序占用。

更多完整流程见：

```text
docs/new-computer-setup.md
```
