# 辽宁区域加盟商贡献数据看板工作树

此目录用于后续工程落地，不是正式交付文档目录。正式文档仍在 `outputs/`。

## 目录说明

| 目录 | 用途 |
|---|---|
| `docs/` | 工程设计、接口说明、数据口径草稿 |
| `frontend/` | React/Vite 前端看板 |
| `backend-api/` | API 服务，建议 FastAPI 或 Workers API 适配层 |
| `import-service/` | Python Excel 导入、清洗、校验、入库服务 |
| `database/migrations/` | SQLite/PostgreSQL 建表和变更脚本 |
| `database/seeds/` | 初始字典、指标、标签、模板配置 |
| `cloudflare/workers/` | Cloudflare Workers API 网关代码 |
| `cloudflare/r2/` | R2 bucket、文件路径、对象存储约定 |
| `cloudflare/queues/` | Queue / Workflow 导入任务约定 |
| `skills/` | 项目专用 skill 备份或后续扩展 |
| `data/samples/` | 示例输入文件说明，不放正式敏感数据 |
| `data/staging/` | 本地临时清洗数据 |
| `tests/` | 导入、指标、接口、前端测试 |
| `scripts/` | 项目辅助脚本 |

## 当前正式文档

正式文档位于：

```text
outputs/
```

已有：

```text
辽宁加盟商贡献数据看板提示词.md
可复用数据看板数据模型设计.md
辽宁区域加盟商贡献数据看板工程实施方案.md
```

## 推荐下一步

1. 新电脑先阅读 `docs/new-computer-setup.md`，运行 `scripts/check-local-env.ps1` 检测环境。
2. 用 `scripts/setup-sqlite-local.ps1` 导入每周 Excel，在 `http://127.0.0.1:5173/` 本地预览。
3. 预览确认后用 `scripts/publish-cloudflare-snapshot.ps1` 生成并上传 Cloudflare Pages 快照。
4. 增加行级导入异常明细。
5. 为前端补更多图表页面和下钻筛选。

## 当前状态

已创建 MVP 工程骨架：

- `database/`：SQLite/PostgreSQL 建表脚本和种子数据。
- `import-service/`：Python Excel 检查、抽取、source/import job 记录、校验报告、入库 CLI。
- `backend-api/`：FastAPI 查询接口，默认对接本地 SQLite，也保留 PostgreSQL 兼容。
- `frontend/`：React/Vite 看板，已从 API 拉取总览、Top/Bottom 排行，并渲染排行图和目的省份/公斤段热力图。
- `cloudflare/`：Workers、R2、Queues 入口骨架。

启动说明见：

```text
docs/quickstart.md
docs/new-computer-setup.md
```
