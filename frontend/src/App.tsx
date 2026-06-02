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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const PERIOD_MONTH = "202604";
const REGION_CODE = "LN";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

async function fetchDashboardData(): Promise<DashboardData> {
  const params = `period_month=${PERIOD_MONTH}&region_code=${REGION_CODE}`;
  const [overviewData, topRankData, bottomRankData, heatmap] = await Promise.all([
    fetchJson<Overview>(`/api/dashboard/overview?${params}`),
    fetchJson<RankItem[]>(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=desc&limit=8`),
    fetchJson<RankItem[]>(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=asc&limit=8`),
    fetchJson<ContributionHeatmap>(`/api/dashboard/contribution-flow/heatmap?${params}&scope_type=region&metric=contribution_total&province_limit=12`),
  ]);
  return { overview: overviewData, topRank: topRankData, bottomRank: bottomRankData, heatmap };
}

function moneyWan(value: number | null | undefined) {
  const raw = value ?? 0;
  return `${(raw / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
}

function countWan(value: number | null | undefined) {
  const raw = value ?? 0;
  return `${(raw / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
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

export function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span>LN</span>
          <strong>贡献看板</strong>
        </div>
        <nav>
          <a className="active">经营总览</a>
          <a>加盟商贡献</a>
          <a>网点下钻</a>
          <a>目的省份与公斤段</a>
          <a>扣款与补贴</a>
          <a>数据导入</a>
        </nav>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p>{PERIOD_MONTH} / 辽宁区域</p>
            <h1>辽宁区域加盟商贡献数据看板</h1>
          </div>
          <div className="filters">
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
            <p className="panel-note">总贡献 = 出港总贡献 + 进港总贡献。当前数据来自 PostgreSQL 聚合接口。</p>
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
      </section>
    </main>
  );
}
