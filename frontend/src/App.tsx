import { useEffect, useMemo, useRef, useState } from "react";
import type { DependencyList } from "react";
import * as echarts from "echarts/core";
import type { EChartsType } from "echarts/core";
import { BarChart, HeatmapChart } from "echarts/charts";
import { GridComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { API_BASE, DEMO_MODE, IMPORT_JOB_ID, METRIC_LABELS, NAV_ITEMS, PERIOD_MONTH, REGION_CODE, STATUS_LABELS, WEIGHT_BANDS } from "./constants";
import { countWan, moneyWan, percent, plainNumber, signedMoneyWan } from "./format";
import { sumHeatmapByProvince, sumHeatmapByWeightBand } from "./heatmapUtils";
import type {
  ContributionHeatmap,
  ContributionHeatmapCell,
  DashboardData,
  ImportJob,
  ImportValidationResponse,
  Overview,
  RankItem,
  SiteRankItem,
  ViewKey,
} from "./types";

echarts.use([BarChart, HeatmapChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer]);

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
  siteRank: [
    {
      name: "沈阳浑南一部",
      franchise_name: "沈阳加盟商一百三十一(项目)",
      site_status: "正常",
      total_contribution: 1432500.48,
      outbound_contribution: 1380200.18,
      inbound_contribution: 52300.3,
      deduction_total: 18500,
      outbound_tickets: 186420,
      inbound_signed_tickets: 328650,
      tags: ["高票量", "正贡献"],
    },
    {
      name: "沈阳铁西三部",
      franchise_name: "沈阳加盟商一百三十一(项目)",
      site_status: "正常",
      total_contribution: 1186030.22,
      outbound_contribution: 1112680.22,
      inbound_contribution: 73350,
      deduction_total: 22600,
      outbound_tickets: 153280,
      inbound_signed_tickets: 280440,
      tags: ["高票量", "扣款关注"],
    },
    {
      name: "盘锦兴隆台一部",
      franchise_name: "盘锦加盟商八(周东旭)",
      site_status: "正常",
      total_contribution: 965420.15,
      outbound_contribution: 882100.15,
      inbound_contribution: 83320,
      deduction_total: 41600,
      outbound_tickets: 121900,
      inbound_signed_tickets: 198300,
      tags: ["扣款关注"],
    },
    {
      name: "大连金州二部",
      franchise_name: "大连加盟商十五",
      site_status: "正常",
      total_contribution: 812430.8,
      outbound_contribution: 694210.8,
      inbound_contribution: 118220,
      deduction_total: 15800,
      outbound_tickets: 98400,
      inbound_signed_tickets: 201600,
      tags: ["正贡献"],
    },
    {
      name: "营口鲅鱼圈一部",
      franchise_name: "营口加盟商三十一",
      site_status: "正常",
      total_contribution: 622100.52,
      outbound_contribution: 568700.52,
      inbound_contribution: 53400,
      deduction_total: 52800,
      outbound_tickets: 76600,
      inbound_signed_tickets: 146900,
      tags: ["扣款关注"],
    },
    {
      name: "大连旅顺一部",
      franchise_name: "大连加盟商二十一(邵文东)",
      site_status: "复核",
      total_contribution: -88400.4,
      outbound_contribution: 31800.2,
      inbound_contribution: -120200.6,
      deduction_total: 24600,
      outbound_tickets: 15120,
      inbound_signed_tickets: 68200,
      tags: ["负贡献", "进港亏损"],
    },
    {
      name: "沈阳于洪五部",
      franchise_name: "沈阳加盟商七十六",
      site_status: "复核",
      total_contribution: -64220.18,
      outbound_contribution: 18420.82,
      inbound_contribution: -82641,
      deduction_total: 9800,
      outbound_tickets: 10880,
      inbound_signed_tickets: 54460,
      tags: ["负贡献", "进港亏损"],
    },
    {
      name: "抚顺望花一部",
      franchise_name: "抚顺加盟商九",
      site_status: "正常",
      total_contribution: 22100.12,
      outbound_contribution: 52900.12,
      inbound_contribution: -30800,
      deduction_total: 39200,
      outbound_tickets: 18440,
      inbound_signed_tickets: 72100,
      tags: ["进港亏损", "扣款关注"],
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
  const [overviewData, topRankData, bottomRankData, siteRank, heatmap] = await Promise.all([
    fetchJson<Overview>(`/api/dashboard/overview?${params}`),
    fetchJson<RankItem[]>(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=desc&limit=8`),
    fetchJson<RankItem[]>(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=asc&limit=8`),
    fetchJson<SiteRankItem[]>(`/api/dashboard/sites/rank?${params}&metric=total_contribution&direction=desc&limit=12`),
    fetchJson<ContributionHeatmap>(`/api/dashboard/contribution-flow/heatmap?${params}&scope_type=region&metric=contribution_total&province_limit=12`),
  ]);
  const [importJob, importValidation] = await Promise.all([
    fetchOptionalJson<ImportJob>(`/api/import/jobs/${IMPORT_JOB_ID}`),
    fetchOptionalJson<ImportValidationResponse>(`/api/import/jobs/${IMPORT_JOB_ID}/validation-results`),
  ]);
  return { overview: overviewData, topRank: topRankData, bottomRank: bottomRankData, siteRank, heatmap, importJob, importValidation };
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

function DeductionBar({ item, max }: { item: RankItem; max: number }) {
  const deduction = item.deduction_total ?? 0;
  const width = Math.max(4, percent(deduction, max));
  return (
    <div className="rank-row">
      <div className="rank-label">
        <strong title={item.name}>{item.name}</strong>
        <span>{item.tags.join(" / ") || "待复核"}</span>
      </div>
      <div className="rank-track" aria-hidden="true">
        <div className="rank-bar negative" style={{ width: `${width}%` }} />
      </div>
      <span className="amount negative-text">{moneyWan(deduction)}</span>
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

function FranchiseView({ data, maxContribution }: { data: DashboardData | null; maxContribution: number }) {
  const topItems = data?.topRank ?? [];
  const bottomItems = data?.bottomRank ?? [];
  const visibleItems = [...topItems, ...bottomItems];
  const negativeCount = visibleItems.filter((item) => item.total_contribution < 0).length;
  const inboundLossCount = visibleItems.filter((item) => (item.inbound_contribution ?? 0) < 0).length;
  const highDeductionCount = visibleItems.filter((item) => (item.deduction_total ?? 0) >= 50000).length;
  const topThreeTotal = topItems.slice(0, 3).reduce((sum, item) => sum + item.total_contribution, 0);
  const totalContribution = data?.overview.total_contribution ?? 0;
  const topThreeShare = totalContribution ? percent(topThreeTotal, totalContribution) : 0;

  return (
    <section className="franchise-view">
      <section className="kpi-grid">
        <KpiCard label="头部加盟商" value={topItems[0]?.name ?? "暂无"} />
        <KpiCard label="Top 3 贡献占比" value={`${topThreeShare.toFixed(1)}%`} tone="good" />
        <KpiCard label="负贡献样本数" value={`${negativeCount}`} tone={negativeCount ? "risk" : "neutral"} />
        <KpiCard label="高扣款样本数" value={`${highDeductionCount}`} tone={highDeductionCount ? "risk" : "neutral"} />
      </section>

      <section className="dashboard-grid">
        <article className="panel">
          <div className="panel-head">
            <h2>加盟商贡献 Top 8</h2>
            <span>总贡献 / 万元</span>
          </div>
          <RankChart items={topItems} />
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>低贡献与风险样本</h2>
            <span>Bottom 8</span>
          </div>
          <div className="rank-list">
            {bottomItems.length ? (
              bottomItems.map((item) => <RankBar key={item.name} item={item} max={maxContribution} />)
            ) : (
              <div className="empty-panel">暂无低贡献样本</div>
            )}
          </div>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>贡献拆解明细</h2>
            <span>粒度：月 / 区域 / 加盟商</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>加盟商</th>
                <th>总贡献</th>
                <th>出港贡献</th>
                <th>进港贡献</th>
                <th>扣款小计</th>
                <th>标签</th>
              </tr>
            </thead>
            <tbody>
              {visibleItems.length ? (
                visibleItems.map((item) => (
                  <tr key={`${item.name}-${item.total_contribution}`}>
                    <td>{item.name}</td>
                    <td className={item.total_contribution < 0 ? "negative-text" : ""}>{signedMoneyWan(item.total_contribution)}</td>
                    <td>{signedMoneyWan(item.outbound_contribution)}</td>
                    <td className={(item.inbound_contribution ?? 0) < 0 ? "negative-text" : ""}>
                      {signedMoneyWan(item.inbound_contribution)}
                    </td>
                    <td className={(item.deduction_total ?? 0) >= 50000 ? "negative-text" : ""}>{moneyWan(item.deduction_total)}</td>
                    <td>{item.tags.join(" / ") || "正常"}</td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={6} />
              )}
            </tbody>
          </table>
          <p className="panel-note">
            当前页先使用排名接口返回的 Top/Bottom 样本做加盟商分析。后续接入分页明细后，可扩展为全量搜索、排序和单个加盟商下钻。
          </p>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>运营关注点</h2>
            <span>自动识别</span>
          </div>
          <div className="insight-grid">
            <div>
              <strong>{inboundLossCount}</strong>
              <span>个样本存在进港亏损，需要复核签收量、进港成本和补贴口径。</span>
            </div>
            <div>
              <strong>{highDeductionCount}</strong>
              <span>个样本扣款超过 5 万元，建议进入扣款与补贴视图继续拆分。</span>
            </div>
            <div>
              <strong>{topThreeShare.toFixed(1)}%</strong>
              <span>来自 Top 3 加盟商的贡献占比，用于观察头部集中度。</span>
            </div>
          </div>
        </article>
      </section>
    </section>
  );
}

function SiteView({ data }: { data: DashboardData | null }) {
  const siteItems = data?.siteRank ?? [];
  const totalSites = data?.overview.site_count ?? 0;
  const negativeSites = siteItems.filter((item) => item.total_contribution < 0);
  const inboundLossSites = siteItems.filter((item) => (item.inbound_contribution ?? 0) < 0);
  const deductionRiskSites = siteItems.filter((item) => (item.deduction_total ?? 0) >= 20000);
  const topSite = siteItems[0];
  const maxSiteContribution = Math.max(1, ...siteItems.map((item) => Math.abs(item.total_contribution)));
  const sampleContribution = siteItems.reduce((sum, item) => sum + item.total_contribution, 0);
  const sampleTickets = siteItems.reduce((sum, item) => sum + (item.outbound_tickets ?? 0), 0);

  return (
    <section className="site-view">
      <section className="kpi-grid">
        <KpiCard label="网点总数" value={`${totalSites}`} />
        <KpiCard label="样本网点贡献" value={moneyWan(sampleContribution)} tone={sampleContribution < 0 ? "risk" : "good"} />
        <KpiCard label="负贡献网点" value={`${negativeSites.length}`} tone={negativeSites.length ? "risk" : "neutral"} />
        <KpiCard label="样本出港票量" value={countWan(sampleTickets)} />
      </section>

      <section className="dashboard-grid">
        <article className="panel">
          <div className="panel-head">
            <h2>网点贡献排行</h2>
            <span>Top 12 / 万元</span>
          </div>
          <div className="rank-list">
            {siteItems.length ? (
              siteItems.slice(0, 8).map((item) => (
                <RankBar
                  key={`${item.franchise_name}-${item.name}`}
                  item={item}
                  max={maxSiteContribution}
                />
              ))
            ) : (
              <div className="empty-panel">暂无网点排行数据</div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>网点风险样本</h2>
            <span>负贡献 / 进港亏损 / 扣款</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>网点</th>
                <th>加盟商</th>
                <th>标签</th>
              </tr>
            </thead>
            <tbody>
              {[...new Set([...negativeSites, ...inboundLossSites, ...deductionRiskSites])].length ? (
                [...new Set([...negativeSites, ...inboundLossSites, ...deductionRiskSites])].slice(0, 8).map((item) => (
                  <tr key={`${item.franchise_name}-${item.name}`}>
                    <td>{item.name}</td>
                    <td>{item.franchise_name}</td>
                    <td>{item.tags.join(" / ") || "待复核"}</td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={3} />
              )}
            </tbody>
          </table>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>网点贡献明细</h2>
            <span>粒度：月 / 区域 / 加盟商 / 网点</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>网点</th>
                <th>所属加盟商</th>
                <th>状态</th>
                <th>总贡献</th>
                <th>出港贡献</th>
                <th>进港贡献</th>
                <th>扣款</th>
                <th>出港票量</th>
              </tr>
            </thead>
            <tbody>
              {siteItems.length ? (
                siteItems.map((item) => (
                  <tr key={`${item.franchise_name}-${item.name}-${item.total_contribution}`}>
                    <td>{item.name}</td>
                    <td>{item.franchise_name}</td>
                    <td>{item.site_status || "正常"}</td>
                    <td className={item.total_contribution < 0 ? "negative-text" : ""}>{signedMoneyWan(item.total_contribution)}</td>
                    <td>{signedMoneyWan(item.outbound_contribution)}</td>
                    <td className={(item.inbound_contribution ?? 0) < 0 ? "negative-text" : ""}>
                      {signedMoneyWan(item.inbound_contribution)}
                    </td>
                    <td className={(item.deduction_total ?? 0) >= 20000 ? "negative-text" : ""}>{moneyWan(item.deduction_total)}</td>
                    <td>{countWan(item.outbound_tickets)}</td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={8} />
              )}
            </tbody>
          </table>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>网点关注点</h2>
            <span>自动识别</span>
          </div>
          <div className="insight-grid">
            <div>
              <strong>{topSite?.name ?? "-"}</strong>
              <span>当前样本贡献最高网点，所属加盟商为 {topSite?.franchise_name ?? "-"}。</span>
            </div>
            <div>
              <strong>{inboundLossSites.length}</strong>
              <span>个样本网点存在进港亏损，需要复核进港成本、签收量和派费口径。</span>
            </div>
            <div>
              <strong>{deductionRiskSites.length}</strong>
              <span>个样本网点扣款超过 2 万元，建议进入扣款视图继续拆分。</span>
            </div>
          </div>
        </article>
      </section>
    </section>
  );
}

function FlowView({ heatmap }: { heatmap: ContributionHeatmap | null | undefined }) {
  const provinceTotals = sumHeatmapByProvince(heatmap);
  const weightBandTotals = sumHeatmapByWeightBand(heatmap);
  const negativeCells = (heatmap?.cells ?? [])
    .filter((cell) => cell.value < 0)
    .sort((a, b) => a.value - b.value)
    .slice(0, 8);
  const strongestProvince = provinceTotals[0];
  const strongestWeightBand = [...weightBandTotals].sort((a, b) => Math.abs(b.value) - Math.abs(a.value))[0];
  const totalContribution = provinceTotals.reduce((sum, item) => sum + item.value, 0);

  return (
    <section className="flow-view">
      <section className="kpi-grid">
        <KpiCard label="覆盖目的省份" value={`${heatmap?.provinces.length ?? 0}`} />
        <KpiCard label="公斤段数量" value={`${heatmap?.weight_bands.length ?? 0}`} />
        <KpiCard label="热力图贡献合计" value={moneyWan(totalContribution)} tone={totalContribution < 0 ? "risk" : "good"} />
        <KpiCard label="负贡献单元格" value={`${negativeCells.length}`} tone={negativeCells.length ? "risk" : "neutral"} />
      </section>

      <section className="dashboard-grid">
        <article className="panel wide">
          <div className="panel-head">
            <h2>目的省份与公斤段热力图</h2>
            <span>贡献总额 / 万元</span>
          </div>
          <HeatmapChartView heatmap={heatmap} />
          <p className="panel-note">
            横轴按业务公斤段排序，纵轴按目的省份贡献绝对值排序。绿色表示正贡献，红色表示负贡献。
          </p>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>目的省份贡献排行</h2>
            <span>Top 12</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>目的省份</th>
                <th>贡献</th>
                <th>票量</th>
              </tr>
            </thead>
            <tbody>
              {provinceTotals.length ? (
                provinceTotals.map((item) => (
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td className={item.value < 0 ? "negative-text" : ""}>{signedMoneyWan(item.value)}</td>
                    <td>{countWan(item.tickets)}</td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={3} />
              )}
            </tbody>
          </table>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>公斤段贡献汇总</h2>
            <span>业务排序</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>公斤段</th>
                <th>贡献</th>
                <th>重量</th>
              </tr>
            </thead>
            <tbody>
              {weightBandTotals.length ? (
                weightBandTotals.map((item) => (
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td className={item.value < 0 ? "negative-text" : ""}>{signedMoneyWan(item.value)}</td>
                    <td>{countWan(item.weight)}</td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={3} />
              )}
            </tbody>
          </table>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>流向关注点</h2>
            <span>自动识别</span>
          </div>
          <div className="insight-grid">
            <div>
              <strong>{strongestProvince?.name ?? "-"}</strong>
              <span>当前贡献绝对值最高的目的省份，贡献为 {signedMoneyWan(strongestProvince?.value)}。</span>
            </div>
            <div>
              <strong>{strongestWeightBand?.name ?? "-"}</strong>
              <span>当前贡献绝对值最高的公斤段，贡献为 {signedMoneyWan(strongestWeightBand?.value)}。</span>
            </div>
            <div>
              <strong>{negativeCells.length}</strong>
              <span>个省份 x 公斤段组合为负贡献，建议优先复核价格、成本和补贴口径。</span>
            </div>
          </div>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>负贡献单元格</h2>
            <span>按亏损额排序</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>目的省份</th>
                <th>公斤段</th>
                <th>贡献</th>
                <th>票量</th>
                <th>重量</th>
              </tr>
            </thead>
            <tbody>
              {negativeCells.length ? (
                negativeCells.map((cell) => (
                  <tr key={`${cell.destination_province}-${cell.weight_band}`}>
                    <td>{cell.destination_province}</td>
                    <td>{cell.weight_band}</td>
                    <td className="negative-text">{signedMoneyWan(cell.value)}</td>
                    <td>{countWan(cell.ticket_count)}</td>
                    <td>{countWan(cell.weight_total)}</td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={5} />
              )}
            </tbody>
          </table>
        </article>
      </section>
    </section>
  );
}

function DeductionView({ data }: { data: DashboardData | null }) {
  const visibleItems = [...(data?.topRank ?? []), ...(data?.bottomRank ?? [])];
  const deductionItems = visibleItems
    .filter((item) => (item.deduction_total ?? 0) > 0)
    .sort((a, b) => (b.deduction_total ?? 0) - (a.deduction_total ?? 0));
  const highRiskItems = deductionItems.filter((item) => (item.deduction_total ?? 0) >= 50000);
  const maxDeduction = Math.max(1, ...deductionItems.map((item) => item.deduction_total ?? 0));
  const overviewDeduction = data?.overview.deduction_total ?? 0;
  const overviewContribution = data?.overview.total_contribution ?? 0;
  const deductionRatio = overviewContribution ? percent(overviewDeduction, overviewContribution) : 0;
  const sampleDeductionTotal = deductionItems.reduce((sum, item) => sum + (item.deduction_total ?? 0), 0);
  const strongestDeduction = deductionItems[0];

  return (
    <section className="deduction-view">
      <section className="kpi-grid">
        <KpiCard label="扣款小计" value={moneyWan(overviewDeduction)} tone="risk" />
        <KpiCard label="扣款 / 总贡献" value={`${deductionRatio.toFixed(1)}%`} tone={deductionRatio > 10 ? "risk" : "neutral"} />
        <KpiCard label="高扣款样本数" value={`${highRiskItems.length}`} tone={highRiskItems.length ? "risk" : "neutral"} />
        <KpiCard label="样本扣款合计" value={moneyWan(sampleDeductionTotal)} tone="risk" />
      </section>

      <section className="dashboard-grid">
        <article className="panel">
          <div className="panel-head">
            <h2>扣款排行</h2>
            <span>样本 / 万元</span>
          </div>
          <div className="rank-list">
            {deductionItems.length ? (
              deductionItems.slice(0, 8).map((item) => <DeductionBar key={item.name} item={item} max={maxDeduction} />)
            ) : (
              <div className="empty-panel">暂无扣款样本</div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>高扣款风险</h2>
            <span>扣款 ≥ 5 万元</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>加盟商</th>
                <th>扣款</th>
                <th>总贡献</th>
              </tr>
            </thead>
            <tbody>
              {highRiskItems.length ? (
                highRiskItems.map((item) => (
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td className="negative-text">{moneyWan(item.deduction_total)}</td>
                    <td className={item.total_contribution < 0 ? "negative-text" : ""}>{signedMoneyWan(item.total_contribution)}</td>
                  </tr>
                ))
              ) : (
                <EmptyRows colSpan={3} />
              )}
            </tbody>
          </table>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>扣款影响明细</h2>
            <span>粒度：月 / 区域 / 加盟商</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>加盟商</th>
                <th>扣款小计</th>
                <th>总贡献</th>
                <th>扣款 / 总贡献</th>
                <th>进港贡献</th>
                <th>标签</th>
              </tr>
            </thead>
            <tbody>
              {deductionItems.length ? (
                deductionItems.map((item) => {
                  const deduction = item.deduction_total ?? 0;
                  const itemRatio = item.total_contribution ? percent(deduction, Math.abs(item.total_contribution)) : 0;
                  return (
                    <tr key={`${item.name}-${deduction}`}>
                      <td>{item.name}</td>
                      <td className="negative-text">{moneyWan(deduction)}</td>
                      <td className={item.total_contribution < 0 ? "negative-text" : ""}>{signedMoneyWan(item.total_contribution)}</td>
                      <td className={itemRatio >= 10 ? "negative-text" : ""}>{itemRatio.toFixed(1)}%</td>
                      <td className={(item.inbound_contribution ?? 0) < 0 ? "negative-text" : ""}>
                        {signedMoneyWan(item.inbound_contribution)}
                      </td>
                      <td>{item.tags.join(" / ") || "正常"}</td>
                    </tr>
                  );
                })
              ) : (
                <EmptyRows colSpan={6} />
              )}
            </tbody>
          </table>
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>扣款与补贴关注点</h2>
            <span>当前口径</span>
          </div>
          <div className="insight-grid">
            <div>
              <strong>{strongestDeduction?.name ?? "-"}</strong>
              <span>当前样本中扣款最高，扣款为 {moneyWan(strongestDeduction?.deduction_total)}。</span>
            </div>
            <div>
              <strong>{deductionRatio.toFixed(1)}%</strong>
              <span>区域扣款小计占总贡献比例，用于判断贡献被扣款侵蚀程度。</span>
            </div>
            <div>
              <strong>待接入</strong>
              <span>补贴明细字段尚未进入当前 API，后续需要按费用类型、事件和来源 sheet 拆分。</span>
            </div>
          </div>
        </article>
      </section>
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

        {activeView === "franchise" ? <FranchiseView data={data} maxContribution={maxContribution} /> : null}

        {activeView === "site" ? <SiteView data={data} /> : null}

        {activeView === "flow" ? <FlowView heatmap={data?.heatmap} /> : null}

        {activeView === "deduction" ? <DeductionView data={data} /> : null}

        {activeView === "import" ? <ImportView data={data} /> : null}
      </section>
    </main>
  );
}
