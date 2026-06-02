import { useEffect, useMemo, useRef, useState } from "react";
import type { DependencyList } from "react";
import * as echarts from "echarts/core";
import type { EChartsType } from "echarts/core";
import { BarChart, HeatmapChart } from "echarts/charts";
import { GridComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, HeatmapChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer]);

type Overview = {
  period_month: string;
  region_code: string;
  franchise_count: number;
  site_count: number;
  outbound_tickets: number;
  outbound_weight: number;
  inbound_signed_tickets: number;
  outbound_contribution: number;
  inbound_contribution: number;
  total_contribution: number;
  deduction_total: number;
};

type RankItem = {
  name: string;
  total_contribution: number;
  outbound_contribution: number | null;
  inbound_contribution: number | null;
  deduction_total: number | null;
  tags: string[];
};

type DashboardData = {
  overview: Overview;
  topRank: RankItem[];
  bottomRank: RankItem[];
  heatmap: ContributionHeatmap;
  importJob: ImportJob | null;
  importValidation: ImportValidationResponse | null;
};

type ContributionHeatmapCell = {
  destination_province: string;
  weight_band: string;
  value: number;
  ticket_count: number | null;
  weight_total: number | null;
};

type ContributionHeatmap = {
  period_month: string;
  region_code: string;
  scope_type: string;
  metric: string;
  provinces: string[];
  weight_bands: string[];
  cells: ContributionHeatmapCell[];
};

type ImportJob = {
  job_id: number;
  status: string;
  progress: number;
  message: string | null;
};

type ImportValidationResult = {
  rule_code: string;
  metric_code: string;
  expected_value: number | null;
  actual_value: number | null;
  diff_value: number | null;
  tolerance: number | null;
  passed: boolean;
  severity: string;
  message: string | null;
};

type ImportValidationResponse = {
  job_id: number;
  passed: number;
  failed: number;
  results: ImportValidationResult[];
};

type ViewKey = "overview" | "franchise" | "site" | "flow" | "deduction" | "import";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";
const PERIOD_MONTH = "202604";
const REGION_CODE = "LN";
const IMPORT_JOB_ID = Number(import.meta.env.VITE_IMPORT_JOB_ID ?? "1");
const WEIGHT_BANDS = ["0.3", "0.5", "1", "2", "3.2", "4", "5.2", "6", "7", "8", "9", "10.3", "＞10.3"];
const NAV_ITEMS: { key: ViewKey; label: string; enabled: boolean }[] = [
  { key: "overview", label: "经营总览", enabled: true },
  { key: "franchise", label: "加盟商贡献", enabled: false },
  { key: "site", label: "网点下钻", enabled: false },
  { key: "flow", label: "目的省份与公斤段", enabled: false },
  { key: "deduction", label: "扣款与补贴", enabled: false },
  { key: "import", label: "数据导入", enabled: true },
];
const METRIC_LABELS: Record<string, string> = {
  franchise_count: "加盟商数",
  site_count: "网点数",
  outbound_tickets: "出港票量",
  outbound_weight: "出港重量",
  inbound_signed_tickets: "进港签收量",
  outbound_contribution: "出港总贡献",
  inbound_contribution: "进港总贡献",
  total_contribution: "总贡献",
  deduction_total: "扣款小计",
};
const STATUS_LABELS: Record<string, string> = {
  pending: "待处理",
  running: "处理中",
  completed: "已完成",
  failed: "失败",
};

const DEMO_PROVINCES = ["广东", "浙江", "江苏", "山东", "河北", "吉林", "黑龙江", "北京", "上海", "内蒙古", "四川", "河南"];

const demoHeatmapCells: ContributionHeatmapCell[] = DEMO_PROVINCES.flatMap((province, provinceIndex) => (
  WEIGHT_BANDS.map((weightBand, bandIndex) => {
    const centerBoost = 1 - Math.abs(bandIndex - 5) * 0.065;
    const provinceScale = 1 - provinceIndex * 0.045;
    const negative = provinceIndex >= 9 && bandIndex >= 9;
    const valueWan = negative
      ? -12 - provinceIndex * 2.5 - bandIndex
      : Math.max(6, 92 * centerBoost * provinceScale - bandIndex * 1.8);

    return {
      destination_province: province,
      weight_band: weightBand,
      value: Math.round(valueWan * 10000),
      ticket_count: Math.round((24000 - provinceIndex * 760 + bandIndex * 310) * Math.max(0.55, centerBoost)),
      weight_total: Math.round((56000 - provinceIndex * 1200 + bandIndex * 880) * Math.max(0.55, centerBoost)),
    };
  })
));

const demoData: DashboardData = {
  overview: {
    period_month: PERIOD_MONTH,
    region_code: REGION_CODE,
    franchise_count: 155,
    site_count: 293,
    outbound_tickets: 25342926,
    outbound_weight: 65988013.97,
    inbound_signed_tickets: 58097658,
    outbound_contribution: 33411654.7741,
    inbound_contribution: 6625333.59,
    total_contribution: 40036988.3641,
    deduction_total: 6448104.21,
  },
  topRank: [
    {
      name: "沈阳加盟商一百三十一(项目)",
      total_contribution: 8576417.9666,
      outbound_contribution: 8429270.7166,
      inbound_contribution: 147147.25,
      deduction_total: 57186.31,
      tags: ["头部贡献", "出港强"],
    },
    {
      name: "沈阳加盟商六十三(孙贺焱)",
      total_contribution: 2750968.4289,
      outbound_contribution: 2631607.4789,
      inbound_contribution: 119360.95,
      deduction_total: 28772.31,
      tags: ["稳定贡献"],
    },
    {
      name: "盘锦加盟商八(周东旭)",
      total_contribution: 2392608.15,
      outbound_contribution: 2262467.02,
      inbound_contribution: 130141.13,
      deduction_total: 124416.84,
      tags: ["高扣款"],
    },
    {
      name: "沈阳加盟商八十九",
      total_contribution: 1984500.62,
      outbound_contribution: 1845220.41,
      inbound_contribution: 139280.21,
      deduction_total: 38420.2,
      tags: ["出港强"],
    },
    {
      name: "大连加盟商十五",
      total_contribution: 1769230.18,
      outbound_contribution: 1510044.11,
      inbound_contribution: 259186.07,
      deduction_total: 42618.9,
      tags: ["均衡"],
    },
    {
      name: "鞍山加盟商十二",
      total_contribution: 1526408.73,
      outbound_contribution: 1382008.73,
      inbound_contribution: 144400,
      deduction_total: 31860.5,
      tags: ["稳定贡献"],
    },
    {
      name: "营口加盟商三十一",
      total_contribution: 1398320.46,
      outbound_contribution: 1230800.46,
      inbound_contribution: 167520,
      deduction_total: 55210.22,
      tags: ["需看扣款"],
    },
    {
      name: "锦州加盟商十九",
      total_contribution: 1217450.34,
      outbound_contribution: 1096265.34,
      inbound_contribution: 121185,
      deduction_total: 24776.6,
      tags: ["稳定贡献"],
    },
  ],
  bottomRank: [
    {
      name: "大连加盟商二十一(邵文东)",
      total_contribution: -246344.4746,
      outbound_contribution: 25530.3554,
      inbound_contribution: -271874.83,
      deduction_total: 56737.44,
      tags: ["负贡献", "进港亏损"],
    },
    {
      name: "沈阳加盟商七十六",
      total_contribution: -118460.12,
      outbound_contribution: 42180.32,
      inbound_contribution: -160640.44,
      deduction_total: 18220.1,
      tags: ["负贡献", "进港亏损"],
    },
    {
      name: "抚顺加盟商九",
      total_contribution: 38420.55,
      outbound_contribution: 102330.81,
      inbound_contribution: -63910.26,
      deduction_total: 76210.4,
      tags: ["进港亏损", "高扣款"],
    },
    {
      name: "辽阳加盟商二十三",
      total_contribution: 72810.44,
      outbound_contribution: 83810.44,
      inbound_contribution: -11000,
      deduction_total: 52100,
      tags: ["高扣款"],
    },
    {
      name: "铁岭加盟商十一",
      total_contribution: 94888.27,
      outbound_contribution: 108230.27,
      inbound_contribution: -13342,
      deduction_total: 44620,
      tags: ["进港亏损"],
    },
  ],
  heatmap: {
    period_month: PERIOD_MONTH,
    region_code: REGION_CODE,
    scope_type: "region",
    metric: "contribution_total",
    provinces: DEMO_PROVINCES,
    weight_bands: WEIGHT_BANDS,
    cells: demoHeatmapCells,
  },
  importJob: {
    job_id: 1,
    status: "completed",
    progress: 100,
    message: "辽宁区域_加盟商贡献表_202604（测试）.xlsx 已完成校验，演示模式未写入数据库。",
  },
  importValidation: {
    job_id: 1,
    passed: 9,
    failed: 0,
    results: [
      ["franchise_count", 155, 155],
      ["site_count", 293, 293],
      ["outbound_tickets", 25342926, 25342926],
      ["outbound_weight", 65988013.97, 65988013.97],
      ["inbound_signed_tickets", 58097658, 58097658],
      ["outbound_contribution", 33411654.7741, 33411654.7741],
      ["inbound_contribution", 6625333.59, 6625333.59],
      ["total_contribution", 40036988.3641, 40036988.3641],
      ["deduction_total", 6448104.21, 6448104.21],
    ].map(([metricCode, expectedValue, actualValue]) => ({
      rule_code: "summary_total_reconcile",
      metric_code: String(metricCode),
      expected_value: Number(expectedValue),
      actual_value: Number(actualValue),
      diff_value: 0,
      tolerance: 0.01,
      passed: true,
      severity: "info",
      message: "源表汇总值与抽取结果一致",
    })),
  },
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

async function fetchOptionalJson<T>(path: string): Promise<T | null> {
  try {
    return await fetchJson<T>(path);
  } catch {
    return null;
  }
}

async function fetchDashboardData(): Promise<DashboardData> {
  if (DEMO_MODE) {
    return demoData;
  }

  const params = `period_month=${PERIOD_MONTH}&region_code=${REGION_CODE}`;
  const [overviewData, topRankData, bottomRankData, heatmap] = await Promise.all([
    fetchJson<Overview>(`/api/dashboard/overview?${params}`),
    fetchJson<RankItem[]>(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=desc&limit=8`),
    fetchJson<RankItem[]>(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=asc&limit=8`),
    fetchJson<ContributionHeatmap>(`/api/dashboard/contribution-flow/heatmap?${params}&scope_type=region&metric=contribution_total&province_limit=12`),
  ]);
  const [importJob, importValidation] = await Promise.all([
    fetchOptionalJson<ImportJob>(`/api/import/jobs/${IMPORT_JOB_ID}`),
    fetchOptionalJson<ImportValidationResponse>(`/api/import/jobs/${IMPORT_JOB_ID}/validation-results`),
  ]);
  return { overview: overviewData, topRank: topRankData, bottomRank: bottomRankData, heatmap, importJob, importValidation };
}

function moneyWan(value: number | null | undefined) {
  const raw = value ?? 0;
  return `${(raw / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
}

function countWan(value: number | null | undefined) {
  const raw = value ?? 0;
  return `${(raw / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
}

function plainNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return value.toLocaleString("zh-CN", { maximumFractionDigits: 4 });
}

function percent(part: number, total: number) {
  if (!Number.isFinite(part) || !Number.isFinite(total) || total === 0) {
    return 0;
  }
  return part / total * 100;
}

function KpiCard(props: { label: string; value: string; tone?: "good" | "risk" | "neutral"; loading?: boolean }) {
  return (
    <section className={`kpi ${props.tone ?? "neutral"} ${props.loading ? "loading" : ""}`}>
      <span>{props.label}</span>
      <strong>{props.loading ? "" : props.value}</strong>
    </section>
  );
}

function StatusPill({ status }: { status: string | undefined }) {
  const normalized = status ?? "pending";
  return <span className={`status-pill ${normalized}`}>{STATUS_LABELS[normalized] ?? normalized}</span>;
}

function RankBar({ item, max }: { item: RankItem; max: number }) {
  const width = Math.max(4, percent(Math.abs(item.total_contribution), max));
  const negative = item.total_contribution < 0;
  return (
    <div className="rank-row">
      <div className="rank-label">
        <strong title={item.name}>{item.name}</strong>
        <span>{item.tags.join(" / ") || "正常"}</span>
      </div>
      <div className="rank-track" aria-hidden="true">
        <div className={negative ? "rank-bar negative" : "rank-bar"} style={{ width: `${width}%` }} />
      </div>
      <span className={negative ? "amount negative-text" : "amount"}>{moneyWan(item.total_contribution)}</span>
    </div>
  );
}

function EmptyRows({ colSpan }: { colSpan: number }) {
  return (
    <tr>
      <td className="empty-cell" colSpan={colSpan}>暂无数据</td>
    </tr>
  );
}

function useChart(
  optionFactory: () => Record<string, unknown>,
  deps: DependencyList,
) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) {
      return;
    }
    const chart: EChartsType = echarts.init(ref.current);
    chart.setOption(optionFactory());

    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, deps);

  return ref;
}

function RankChart({ items }: { items: RankItem[] }) {
  const ref = useChart(
    () => ({
      grid: { top: 8, right: 88, bottom: 24, left: 138 },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: any) => {
          const item = params?.[0];
          return `${item.name}<br/>总贡献：${moneyWan(Number(item.value) * 10000)}`;
        },
      },
      xAxis: {
        type: "value",
        axisLabel: { formatter: (value: number) => `${value.toFixed(0)}万` },
        splitLine: { lineStyle: { color: "#eef2f7" } },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: items.map((item) => item.name),
        axisLabel: {
          width: 120,
          overflow: "truncate",
          color: "#334155",
        },
      },
      series: [
        {
          type: "bar",
          data: items.map((item) => Number((item.total_contribution / 10000).toFixed(2))),
          barWidth: 14,
          itemStyle: { color: "#2454d6", borderRadius: [0, 4, 4, 0] },
          label: {
            show: true,
            position: "right",
            color: "#17202f",
            formatter: (params: any) => `${Number(params.value).toLocaleString("zh-CN", { maximumFractionDigits: 1 })}万`,
          },
        },
      ],
    }),
    [items],
  );

  if (!items.length) {
    return <div className="empty-panel">暂无排行图数据</div>;
  }

  return <div ref={ref} className="chart chart-rank" role="img" aria-label="加盟商总贡献排行图" />;
}

function HeatmapChartView({ heatmap }: { heatmap: ContributionHeatmap | null | undefined }) {
  const values = heatmap?.cells.map((cell) => cell.value / 10000) ?? [];
  const min = Math.min(0, ...values);
  const max = Math.max(0, ...values);
  const ref = useChart(
    () => {
      const provinces = heatmap?.provinces ?? [];
      const weightBands = heatmap?.weight_bands ?? [];
      const cellMap = new Map(
        (heatmap?.cells ?? []).map((cell) => [`${cell.destination_province}::${cell.weight_band}`, cell]),
      );

      return {
        grid: { top: 12, right: 18, bottom: 64, left: 74 },
        tooltip: {
          position: "top",
          formatter: (params: any) => {
            const [x, y] = params.value as [number, number, number];
            const province = provinces[y];
            const weightBand = weightBands[x];
            const cell = cellMap.get(`${province}::${weightBand}`);
            return [
              `${PERIOD_MONTH} / 区域贡献`,
              `目的省份：${province}`,
              `公斤段：${weightBand}`,
              `贡献总额：${moneyWan(cell?.value)}`,
              `票量：${countWan(cell?.ticket_count)}`,
            ].join("<br/>");
          },
        },
        xAxis: {
          type: "category",
          data: weightBands,
          axisLabel: { color: "#334155", interval: 0 },
          splitArea: { show: true },
        },
        yAxis: {
          type: "category",
          inverse: true,
          data: provinces,
          axisLabel: { color: "#334155" },
          splitArea: { show: true },
        },
        visualMap: {
          min,
          max,
          calculable: true,
          orient: "horizontal",
          left: "center",
          bottom: 8,
          text: ["高", "低"],
          inRange: { color: ["#b33a2e", "#f8fafc", "#147a46"] },
        },
        series: [
          {
            type: "heatmap",
            data: provinces.flatMap((province, y) => (
              weightBands.map((weightBand, x) => {
                const cell = cellMap.get(`${province}::${weightBand}`);
                return [x, y, Number(((cell?.value ?? 0) / 10000).toFixed(2))];
              })
            )),
            emphasis: {
              itemStyle: {
                borderColor: "#17202f",
                borderWidth: 1,
              },
            },
          },
        ],
      };
    },
    [heatmap, min, max],
  );

  if (!heatmap?.provinces.length || !heatmap.weight_bands.length) {
    return <div className="empty-panel">暂无热力图数据</div>;
  }

  return <div ref={ref} className="chart chart-heatmap" role="img" aria-label="目的省份与公斤段贡献热力图" />;
}

function OverviewView({
  data,
  loading,
  overview,
  outboundShare,
  inboundShare,
  riskItems,
  maxContribution,
}: {
  data: DashboardData | null;
  loading: boolean;
  overview: Overview | undefined;
  outboundShare: number;
  inboundShare: number;
  riskItems: RankItem[];
  maxContribution: number;
}) {
  return (
    <>
      <section className="kpi-grid" aria-busy={loading}>
        <KpiCard label="加盟商数" value={`${overview?.franchise_count ?? 0}`} loading={loading} />
        <KpiCard label="网点数" value={`${overview?.site_count ?? 0}`} loading={loading} />
        <KpiCard label="出港票量" value={countWan(overview?.outbound_tickets)} loading={loading} />
        <KpiCard label="进港签收量" value={countWan(overview?.inbound_signed_tickets)} loading={loading} />
        <KpiCard label="出港总贡献" value={moneyWan(overview?.outbound_contribution)} tone="good" loading={loading} />
        <KpiCard label="进港总贡献" value={moneyWan(overview?.inbound_contribution)} tone="good" loading={loading} />
        <KpiCard label="总贡献" value={moneyWan(overview?.total_contribution)} tone="good" loading={loading} />
        <KpiCard label="扣款小计" value={moneyWan(overview?.deduction_total)} tone="risk" loading={loading} />
      </section>

      <section className="dashboard-grid">
        <article className="panel wide">
          <div className="panel-head">
            <h2>总贡献拆解</h2>
            <span>单位：万元</span>
          </div>
          <div className="split-bar">
            <div className="outbound" style={{ width: `${outboundShare}%` }}>
              出港 {moneyWan(overview?.outbound_contribution)}
            </div>
            <div className="inbound" style={{ width: `${inboundShare}%` }}>
              进港 {moneyWan(overview?.inbound_contribution)}
            </div>
          </div>
          <p className="panel-note">
            总贡献 = 出港总贡献 + 进港总贡献。当前数据
            {DEMO_MODE ? "用于前端演示，真实上线后来自 PostgreSQL 聚合接口。" : "来自 PostgreSQL 聚合接口。"}
          </p>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>加盟商贡献排行</h2>
            <span>Top 8</span>
          </div>
          <RankChart items={data?.topRank ?? []} />
          <div className="rank-list compact-list">
            {data?.topRank.slice(0, 4).map((item) => <RankBar key={item.name} item={item} max={maxContribution} />)}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>目的省份与公斤段</h2>
            <span>贡献总额 / 万元</span>
          </div>
          <HeatmapChartView heatmap={data?.heatmap} />
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>风险跟进</h2>
            <span>Bottom 8</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>加盟商</th>
                <th>标签</th>
                <th>进港贡献</th>
              </tr>
            </thead>
            <tbody>
              {riskItems.length ? (
                riskItems.map((item) => (
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td>{item.tags.join(" / ") || "待复核"}</td>
                    <td className={(item.inbound_contribution ?? 0) < 0 ? "negative-text" : ""}>
                      {moneyWan(item.inbound_contribution)}
                    </td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={3} />
              )}
            </tbody>
          </table>
        </article>
      </section>
    </>
  );
}

function ImportView({ data }: { data: DashboardData | null }) {
  const job = data?.importJob;
  const validation = data?.importValidation;
  const totalRules = (validation?.passed ?? 0) + (validation?.failed ?? 0);
  const passRate = totalRules ? percent(validation?.passed ?? 0, totalRules) : 0;

  return (
    <section className="import-view">
      <section className="import-summary">
        <article className="panel">
          <div className="panel-head">
            <h2>最近导入任务</h2>
            <StatusPill status={job?.status} />
          </div>
          {job ? (
            <>
              <div className="job-meta">
                <span>任务 ID</span>
                <strong>#{job.job_id}</strong>
              </div>
              <div className="progress-track" aria-label={`导入进度 ${job.progress}%`}>
                <div className="progress-bar" style={{ width: `${Math.max(0, Math.min(100, job.progress))}%` }} />
              </div>
              <p className="panel-note">{job.message ?? "暂无任务说明"}</p>
            </>
          ) : (
            <div className="empty-panel">暂无导入任务。完成 Excel 导入后，这里会显示任务状态和校验结果。</div>
          )}
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>校验概览</h2>
            <span>规则数 {totalRules}</span>
          </div>
          <div className="validation-score">
            <strong>{passRate.toFixed(0)}%</strong>
            <span>通过率</span>
          </div>
          <div className="validation-counts">
            <span className="pass">通过 {validation?.passed ?? 0}</span>
            <span className={validation?.failed ? "fail" : ""}>失败 {validation?.failed ?? 0}</span>
          </div>
        </article>
      </section>

      <article className="panel wide">
        <div className="panel-head">
          <h2>校验明细</h2>
          <span>源表汇总 vs 抽取结果</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>状态</th>
              <th>指标</th>
              <th>源表值</th>
              <th>抽取值</th>
              <th>差异</th>
              <th>规则</th>
            </tr>
          </thead>
          <tbody>
            {validation?.results.length ? (
              validation.results.map((result) => (
                <tr key={`${result.rule_code}-${result.metric_code}`}>
                  <td>
                    <span className={result.passed ? "result-pass" : "result-fail"}>
                      {result.passed ? "通过" : "失败"}
                    </span>
                  </td>
                  <td>{METRIC_LABELS[result.metric_code] ?? result.metric_code}</td>
                  <td>{plainNumber(result.expected_value)}</td>
                  <td>{plainNumber(result.actual_value)}</td>
                  <td className={(result.diff_value ?? 0) === 0 ? "" : "negative-text"}>{plainNumber(result.diff_value)}</td>
                  <td>{result.message ?? result.rule_code}</td>
                </tr>
              ))
            ) : (
              <EmptyRows colSpan={6} />
            )}
          </tbody>
        </table>
      </article>
    </section>
  );
}

export function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ViewKey>("overview");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchDashboardData());
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const maxContribution = useMemo(() => {
    const values = data?.topRank.map((item) => Math.abs(item.total_contribution)) ?? [];
    return Math.max(1, ...values);
  }, [data]);

  const riskItems = useMemo(() => {
    return data?.bottomRank.filter((item) => (
      item.total_contribution < 0 ||
      (item.inbound_contribution ?? 0) < 0 ||
      (item.deduction_total ?? 0) > 50000
    )) ?? [];
  }, [data]);

  const overview = data?.overview;
  const outboundShare = overview ? percent(overview.outbound_contribution, overview.total_contribution) : 0;
  const inboundShare = overview ? percent(overview.inbound_contribution, overview.total_contribution) : 0;
  const activeNav = NAV_ITEMS.find((item) => item.key === activeView);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span>LN</span>
          <strong>贡献看板</strong>
        </div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={item.key === activeView ? "active" : ""}
              disabled={!item.enabled}
              onClick={() => setActiveView(item.key)}
            >
              <span>{item.label}</span>
              {!item.enabled ? <small>待开发</small> : null}
            </button>
          ))}
        </nav>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p>{PERIOD_MONTH} / 辽宁区域</p>
            <h1>{activeNav?.label ?? "辽宁区域加盟商贡献数据看板"}</h1>
          </div>
          <div className="filters">
            {DEMO_MODE ? <span className="mode-badge">演示数据</span> : null}
            <button type="button">月份 {PERIOD_MONTH}</button>
            <button type="button">区域 辽宁</button>
            <button type="button">全部加盟商</button>
            <button type="button" onClick={load} disabled={loading}>刷新</button>
          </div>
        </header>

        {error ? (
          <section className="notice error">
            <strong>数据加载失败</strong>
            <span>{error}</span>
          </section>
        ) : null}

        {DEMO_MODE ? (
          <section className="notice info">
            <strong>前端演示模式</strong>
            <span>总览 KPI 使用已校验的 202604 汇总值，排行和热力图含部分样例数据；接入 PostgreSQL 后会切回真实 API。</span>
          </section>
        ) : null}

        {activeView === "overview" ? (
          <OverviewView
            data={data}
            loading={loading}
            overview={overview}
            outboundShare={outboundShare}
            inboundShare={inboundShare}
            riskItems={riskItems}
            maxContribution={maxContribution}
          />
        ) : null}

        {activeView === "import" ? <ImportView data={data} /> : null}
      </section>
    </main>
  );
}
