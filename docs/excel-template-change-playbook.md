# Excel 模板变化处理手册

这份文档给后续维护者和电脑里的 AI 使用。目标是：以后新 Excel 的 sheet 页、表头、行列位置变化时，先安全诊断，再决定是否扩展模板，避免把错误数据发布到 Cloudflare。

## 先记住

当前导入器不是“随便什么 Excel 都能识别”的通用 AI 解析器。它是一个带模板配置的可审计导入器。

当前模板入口：

```text
import-service/src/import_service/templates.py
```

当前解析逻辑：

```text
import-service/src/import_service/workbook.py
```

当前校验逻辑：

```text
import-service/src/import_service/validation.py
```

默认模板：

```text
franchise_contribution_v1
```

## 遇到导入失败时不要做什么

- 不要跳过校验后直接发布快照。
- 不要只因为页面能打开就认为数据正确。
- 不要把未知列硬塞进现有字段。
- 不要改坏 `franchise_contribution_v1`，导致旧表不能导入。
- 不要把 Excel 文件、`.runtime` 数据库、Cloudflare token 提交到 GitHub。

## 第一步：结构诊断

在仓库根目录运行：

```powershell
$env:PYTHONPATH = "import-service/src"
.\.venv\Scripts\python.exe -m import_service.cli inspect "C:\path\to\workbook.xlsx"
```

重点看：

- `sheet_count`
- 每个 sheet 的 `name`
- 是否识别出 `standard_sheet_code`
- `header_start_row`
- `header_end_row`
- `data_start_row`
- `total_row`
- `overview` 汇总值是否为空或异常

如果某个必要 sheet 的 `standard_sheet_code` 是 `null`，通常是 sheet 名变化。

## 第二步：校验汇总口径

```powershell
.\.venv\Scripts\python.exe -m import_service.cli validate "C:\path\to\workbook.xlsx"
```

重点看：

- `failed` 是否为 0
- 加盟商数、网点数是否合理
- 出港票量、进港签收量、出港总贡献、进港总贡献、总贡献、扣款小计是否能和源表总计对上

只要 `failed` 不是 0，就不能发布正式快照。

## 第三步：抽样查看解析结果

```powershell
.\.venv\Scripts\python.exe -m import_service.cli extract franchise-summary "C:\path\to\workbook.xlsx" --limit 5
.\.venv\Scripts\python.exe -m import_service.cli extract site-summary "C:\path\to\workbook.xlsx" --limit 5
.\.venv\Scripts\python.exe -m import_service.cli extract contribution-flow "C:\path\to\workbook.xlsx" --scope region --limit 5
.\.venv\Scripts\python.exe -m import_service.cli extract contribution-flow "C:\path\to\workbook.xlsx" --scope franchise --limit 5
```

检查：

- `count` 是否明显异常。
- 加盟商名称、网点名称是否错位。
- 月份 `period_month` 是否正确。
- 票量、重量、贡献、扣款字段是否像数字。
- 目的省份、公斤段是否错位。

## 常见变化和处理方式

### 1. 只是 sheet 名变了

例子：

```text
总表-加盟商 -> 加盟商总表
辽宁区域贡献 -> 省区贡献
```

处理：

修改 `import-service/src/import_service/templates.py` 里的 `sheet_name_patterns`，加别名或通配符。

示例：

```python
SheetRule("franchise_summary", ("总表-加盟商", "加盟商总表", "*加盟商*总表*"), 1, 3, 5, 4, True)
```

然后重新运行：

```powershell
.\.venv\Scripts\python.exe -m import_service.cli inspect "C:\path\to\workbook.xlsx"
.\.venv\Scripts\python.exe -m import_service.cli validate "C:\path\to\workbook.xlsx"
```

### 2. 表头行或数据起始行变了

例子：

```text
原来第 5 行开始数据，现在第 6 行开始数据
```

处理：

修改对应 `SheetRule`：

```python
SheetRule("franchise_summary", ("总表-加盟商",), header_start_row, header_end_row, data_start_row, total_row, True)
```

注意：

- `header_start_row`、`header_end_row` 只影响识别和记录。
- `data_start_row` 影响实际读取数据。
- `total_row` 影响汇总校验。

### 3. 关键字段列位置变了

例子：

```text
总贡献列从原来的第 70 列附近移动了
扣款小计列移动了
```

处理：

修改 `import-service/src/import_service/workbook.py` 中的字段映射，例如：

```python
total_contribution=_num(_cell(row, 69))
deduction_total=_num(_cell(row, 66))
```

这里的索引是 0-based，也就是 Excel 的第 1 列对应索引 0。

这类变化风险较高，建议新增模板版本，不要直接覆盖旧模板。

### 4. 贡献流宽表列组变了

贡献流 sheet 使用公斤段宽表，列组起点在：

```text
DEFAULT_CONTRIBUTION_GROUP_STARTS
DEFAULT_WEIGHT_BANDS
```

如果公斤段变化或每组指标列起点变化，需要修改这些配置，或者新增模板版本。

### 5. 表含义变了

如果源表新增、删除、合并了业务口径，例如“总贡献”的含义变了，不要只改列号。

处理顺序：

1. 让业务人员确认新口径。
2. 修改字段映射和校验规则。
3. 更新文档说明。
4. 用旧表和新表分别回归。
5. 再发布快照。

## 推荐新增模板版本的情况

出现以下情况时，优先新增模板，而不是直接修改 `franchise_contribution_v1`：

- 表头结构明显变化。
- 关键指标列位置大面积变化。
- 公斤段宽表结构变化。
- 老 Excel 仍然需要继续可导入。
- 需要同时支持多个区域或多个供应方模板。

新增模板示意：

```python
FRANCHISE_CONTRIBUTION_V2 = TemplateProfile(
    template_code="franchise_contribution_v2",
    template_name="加盟商贡献表",
    version="2.0.0",
    sheet_rules=(...),
    weight_bands=...,
    contribution_group_starts=...,
)

TEMPLATE_PROFILES = {
    FRANCHISE_CONTRIBUTION_V1.template_code: FRANCHISE_CONTRIBUTION_V1,
    FRANCHISE_CONTRIBUTION_V2.template_code: FRANCHISE_CONTRIBUTION_V2,
}
```

使用新模板导入：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 `
  -Workbook "C:\path\to\workbook.xlsx" `
  -TemplateCode "franchise_contribution_v2"
```

## 修改后必须验证

至少运行：

```powershell
python -m compileall backend-api/src import-service/src
cd frontend
npm run build
cd ..
```

然后重新导入：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-sqlite-local.ps1 -Workbook "C:\path\to\workbook.xlsx"
```

检查导入结果：

```text
validation_failed 必须为 0
franchise_rows 不能明显异常
site_rows 不能明显异常
region_contribution_flow_rows 不能明显异常
franchise_contribution_flow_rows 不能明显异常
```

启动本地看板：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

打开：

```text
http://127.0.0.1:5173/
```

人工核对：

- 加盟商数。
- 网点数。
- 出港票量。
- 进港签收量。
- 出港总贡献。
- 进港总贡献。
- 总贡献。
- 扣款小计。
- Top/Bottom 排行是否像业务真实情况。
- 热力图是否有明显错位。

确认后才能生成并上传 Cloudflare 快照。

## 给后续 AI 的标准处理提示词

可以把下面这段直接发给接手电脑里的 AI：

```text
你正在维护 A3-77/LJdata 项目。先阅读 README.md、AGENTS.md、docs/current-usable-workflow.md、docs/excel-template-change-playbook.md。

现在有一份新的 Excel 导入失败或看板数据异常。请不要跳过校验，不要发布 Cloudflare 快照。先运行 import-service inspect、validate、extract 命令，判断是 sheet 名变化、表头行变化、字段列位置变化、贡献流宽表变化，还是业务口径变化。

如果只是 sheet 名变化，优先在 import-service/src/import_service/templates.py 的 sheet_name_patterns 增加别名。如果结构明显变化，新增 template profile，例如 franchise_contribution_v2，不要破坏 franchise_contribution_v1。

修改后必须运行 python -m compileall backend-api/src import-service/src、frontend npm run build、setup-sqlite-local.ps1 导入、start-local.ps1 本地预览。只有 validation_failed 为 0 且本地看板核对通过，才能运行 publish-cloudflare-snapshot.ps1。
```

## 最后原则

宁可让导入失败，也不要把错位数据做成漂亮看板发布出去。
