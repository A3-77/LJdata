type Overview = {
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
  outbound_contribution: number;
  inbound_contribution: number;
  deduction_total: number;
  tags: string[];
};

const overview: Overview = {
  franchise_count: 155,
  site_count: 293,
  outbound_tickets: 25342926,
  outbound_weight: 65988013.97,
  inbound_signed_tickets: 58097658,
  outbound_contribution: 33411654.7741,
  inbound_contribution: 6625333.59,
  total_contribution: 40036988.3641,
  deduction_total: 6448104.21,
};

const rankItems: RankItem[] = [
  {
    name: "沈阳加盟商一百三十一(项目)",
    total_contribution: 8576417.9666,
    outbound_contribution: 8429270.7166,
    inbound_contribution: 147147.25,
    deduction_total: 57186.31,
    tags: ["高贡献"],
  },
  {
    name: "沈阳加盟商六十三(孙贺焱)",
    total_contribution: 2750968.4289,
    outbound_contribution: 2631607.4789,
    inbound_contribution: 119360.95,
    deduction_total: 28772.31,
    tags: ["高贡献"],
  },
  {
    name: "盘锦加盟商八(周东旭)",
    total_contribution: 2392608.15,
    outbound_contribution: 2262467.02,
    inbound_contribution: 130141.13,
    deduction_total: 124416.84,
    tags: ["高贡献"],
  },
  {
    name: "大连加盟商二十一(邵文东)",
    total_contribution: -246344.4746,
    outbound_contribution: 25530.3554,
    inbound_contribution: -271874.83,
    deduction_total: 56737.44,
    tags: ["负贡献", "进港亏损"],
  },
];

function moneyWan(value: number) {
  return `${(value / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
}

function countWan(value: number) {
  return `${(value / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
}

function KpiCard(props: { label: string; value: string; tone?: "good" | "risk" | "neutral" }) {
  return (
    <section className={`kpi ${props.tone ?? "neutral"}`}>
      <span>{props.label}</span>
      <strong>{props.value}</strong>
    </section>
  );
}

function RankBar({ item, max }: { item: RankItem; max: number }) {
  const width = Math.max(4, Math.abs(item.total_contribution) / max * 100);
  const negative = item.total_contribution < 0;
  return (
    <div className="rank-row">
      <div className="rank-label">
        <strong>{item.name}</strong>
        <span>{item.tags.join(" / ") || "正常"}</span>
      </div>
      <div className="rank-track">
        <div className={negative ? "rank-bar negative" : "rank-bar"} style={{ width: `${width}%` }} />
      </div>
      <span className={negative ? "amount negative-text" : "amount"}>{moneyWan(item.total_contribution)}</span>
    </div>
  );
}

export function App() {
  const maxContribution = Math.max(...rankItems.map((item) => Math.abs(item.total_contribution)));
  const outboundShare = overview.outbound_contribution / overview.total_contribution * 100;
  const inboundShare = overview.inbound_contribution / overview.total_contribution * 100;

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
            <p>202604 / 辽宁区域</p>
            <h1>辽宁区域加盟商贡献数据看板</h1>
          </div>
          <div className="filters">
            <button>月份 202604</button>
            <button>区域 辽宁</button>
            <button>全部加盟商</button>
          </div>
        </header>

        <section className="kpi-grid">
          <KpiCard label="加盟商数" value={`${overview.franchise_count}`} />
          <KpiCard label="网点数" value={`${overview.site_count}`} />
          <KpiCard label="出港票量" value={countWan(overview.outbound_tickets)} />
          <KpiCard label="进港签收量" value={countWan(overview.inbound_signed_tickets)} />
          <KpiCard label="出港总贡献" value={moneyWan(overview.outbound_contribution)} tone="good" />
          <KpiCard label="进港总贡献" value={moneyWan(overview.inbound_contribution)} tone="good" />
          <KpiCard label="总贡献" value={moneyWan(overview.total_contribution)} tone="good" />
          <KpiCard label="扣款小计" value={moneyWan(overview.deduction_total)} tone="risk" />
        </section>

        <section className="dashboard-grid">
          <article className="panel wide">
            <div className="panel-head">
              <h2>总贡献拆解</h2>
              <span>单位：万元</span>
            </div>
            <div className="split-bar">
              <div className="outbound" style={{ width: `${outboundShare}%` }}>
                出港 {moneyWan(overview.outbound_contribution)}
              </div>
              <div className="inbound" style={{ width: `${inboundShare}%` }}>
                进港 {moneyWan(overview.inbound_contribution)}
              </div>
            </div>
            <p className="panel-note">总贡献 = 出港总贡献 + 进港总贡献。当前出港贡献占主导。</p>
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>加盟商贡献排行</h2>
              <span>Top / Bottom</span>
            </div>
            <div className="rank-list">
              {rankItems.map((item) => (
                <RankBar key={item.name} item={item} max={maxContribution} />
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <h2>风险跟进</h2>
              <span>按标签识别</span>
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
                {rankItems.filter((item) => item.total_contribution < 0).map((item) => (
                  <tr key={item.name}>
                    <td>{item.name}</td>
                    <td>{item.tags.join(" / ")}</td>
                    <td className="negative-text">{moneyWan(item.inbound_contribution)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </article>
        </section>
      </section>
    </main>
  );
}

