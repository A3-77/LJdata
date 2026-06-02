# 辽宁区域加盟商贡献数据看板工作树

此目录用于后续工程落地，不是正式交付文档目录。正式文档仍在 `outputs/`。

## 目录说明

| 目录 | 用途 |
|---|---|
| `docs/` | 工程设计、接口说明、数据口径草稿 |
| `frontend/` | React/Vite 前端看板 |
| `backend-api/` | API 服务，建议 FastAPI 或 Workers API 适配层 |
| `import-service/` | Python Excel 导入、清洗、校验、入库服务 |
| `database/migrations/` | PostgreSQL 建表和变更脚本 |
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

1. 生成数据库建表 SQL。
2. 生成 Excel 导入服务骨架。
3. 生成 Cloudflare Workers API 骨架。
4. 生成 React 看板前端骨架。
5. 用当前 202604 Excel 做导入回归测试。
