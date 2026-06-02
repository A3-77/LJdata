import { useEffect, useMemo, useState } from "react";
import { fetchDashboardData } from "./api";
import { DeductionView, FlowView, FranchiseView, ImportView, OverviewView, SiteView } from "./views";
import { DEMO_MODE, NAV_ITEMS, PERIOD_MONTH, REGION_CODE, REGION_LABEL } from "./constants";
import { percent } from "./format";
import type { DashboardData, ViewKey } from "./types";

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
          <span>{REGION_CODE}</span>
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
            <p>{PERIOD_MONTH} / {REGION_LABEL}区域</p>
            <h1>{activeNav?.label ?? `${REGION_LABEL}区域加盟商贡献数据看板`}</h1>
          </div>
          <div className="filters">
            {DEMO_MODE ? <span className="mode-badge">演示数据</span> : null}
            <button type="button">月份 {PERIOD_MONTH}</button>
            <button type="button">区域 {REGION_LABEL}</button>
            <button type="button">全部加盟商</button>
            <button type="button" onClick={load} disabled={loading}>刷新</button>
          </div>
        </header>

        <nav className="mobile-nav" aria-label="看板导航">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={item.key === activeView ? "active" : ""}
              disabled={!item.enabled}
              onClick={() => setActiveView(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {error ? (
          <section className="notice error">
            <strong>数据加载失败</strong>
            <span>{error}</span>
          </section>
        ) : null}

        {DEMO_MODE ? (
          <section className="notice info">
            <strong>前端演示模式</strong>
            <span>总览 KPI 使用已校验的 {PERIOD_MONTH} 汇总值，排行和热力图含部分样例数据；接入 PostgreSQL 后会切回真实 API。</span>
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
