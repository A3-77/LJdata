# 设计优化指南

这份文档用于后续优化 React 看板，让页面更像真实经营分析工具，减少模板化和 AI 味。

已安装到本机 Codex 的补充设计 skill：

```text
C:\Users\A377\.codex\skills\redesign-existing-projects
C:\Users\A377\.codex\skills\minimalist-ui
```

重启 Codex 后可以直接调用。当前项目已有的 `impeccable` 和 `dashboard-dataviz` 仍然是主规则：

- `impeccable`：负责产品 UI 质感、布局、状态、可访问性、响应式。
- `dashboard-dataviz`：负责图表选择、指标口径、单位、颜色语义、数据可信度。
- `redesign-existing-projects`：用于审计 AI 味、默认字体、卡片堆叠、阴影、交互状态。
- `minimalist-ui`：用于约束成克制、清晰、低装饰的业务工具风格。

## 这个项目的设计方向

设计目标：

```text
克制、可信、清晰、可审计的经营分析工具
```

不要做成：

- 营销落地页。
- 炫光数据大屏。
- 深色科技风。
- 一堆白卡片加蓝色按钮的模板 dashboard。
- 过度圆角、过多阴影、过多渐变。

## 当前界面可以优化的点

### 1. 字体

当前 CSS 使用：

```css
font-family: Inter, "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
```

优化方向：

- 中文优先使用系统中文字体，保证清晰。
- 数字使用 tabular figures，提升 KPI 和表格对齐。
- 不强行引入花哨字体，避免财务/经营系统不稳重。

建议：

```css
font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", system-ui, sans-serif;
font-variant-numeric: tabular-nums;
```

### 2. 颜色

当前蓝色强调较强，深色左侧栏有典型模板感。

优化方向：

- 保持浅色工具界面。
- 用更中性的背景和线条。
- 正贡献、负贡献、扣款风险使用稳定语义色。
- 不使用大面积紫蓝渐变。
- 不用装饰性发光、玻璃拟态。

建议语义：

```text
背景：低饱和冷灰或纯浅灰
主文字：高对比深灰
边框：低对比灰线
强调：低饱和蓝或青蓝，只用于选中和关键动作
正贡献：绿色
风险/扣款：红色或红棕
中性体量：灰蓝
```

### 3. 卡片

当前看板大量使用白色卡片。卡片可以保留，但要更像业务系统：

- 卡片半径控制在 `6px` 到 `8px`。
- 少用大阴影，优先用边框、分割线和留白。
- 不要卡片套卡片。
- KPI 卡可以更紧凑，减少“模板组件”感。

### 4. 导航

左侧深色导航可用，但会有模板感。可选优化：

- 改成浅色侧栏，与内容区统一。
- 或保留深色，但降低对比和装饰感。
- 当前页状态要清楚，但不要像按钮墙。
- 移动端导航需要保持可横向滚动且文本不溢出。

### 5. 图表

图表优化必须服从数据可读性：

- 排行图用水平条形图。
- 热力图保留，但颜色要解释正负和风险。
- 每个图标题要有单位。
- tooltip 要带指标、单位、筛选上下文。
- 负值必须以 0 为基准，不要视觉误导。

### 6. 上传和错误状态

这是最像真实工具的部分，必须做扎实：

- 上传前说明当前支持的模板。
- 上传中有进度/处理中状态。
- 失败时显示是 sheet 缺失、校验失败、还是运行错误。
- 指向 `docs/excel-template-change-playbook.md`，提醒不能跳过校验。

## 后续 UI polish 建议顺序

1. 先做视觉审计截图，确认哪些地方最像模板。
2. 优化 CSS 变量、字体、数字对齐和色彩。
3. 优化导航和 topbar 的信息层级。
4. 调整 KPI 卡和面板样式，减少重复卡片感。
5. 优化导入页和错误状态。
6. 用 Playwright 截图检查 `5173` 页面。
7. 跑 `npm run build`。

## 给后续 AI 的设计提示词

可以直接发给接手电脑里的 AI：

```text
你正在优化 A3-77/LJdata 的 React 数据看板。先阅读 README.md、PRODUCT.md、AGENTS.md、docs/design-polish-guide.md、docs/current-usable-workflow.md。

目标不是做营销页，而是让经营分析看板更像真实业务工具：克制、可信、清晰、可审计。减少 AI 味，不要紫蓝渐变、玻璃拟态、过度圆角、过多阴影、卡片堆叠、深色科技大屏。

使用 impeccable、dashboard-dataviz、redesign-existing-projects、minimalist-ui 的规则。先审计现有 CSS 和页面截图，再做小步可回滚修改。保留图表口径和导入功能，不要为了好看破坏数据可信度。

修改后必须运行 npm run build，并用浏览器查看 127.0.0.1:5173。重点检查：KPI 数字、导航、上传页面、错误状态、图表单位、移动端文本不溢出。
```

## 验证命令

```powershell
cd frontend
npm run build
cd ..
```

本地查看：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

打开：

```text
http://127.0.0.1:5173/
```
