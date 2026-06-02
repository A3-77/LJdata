import { HeatmapChartView, RankChart } from "./charts";
import { DeductionBar, EmptyRows, KpiCard, RankBar, StatusPill } from "./components";
import { DEMO_MODE, METRIC_LABELS } from "./constants";
import { countWan, moneyWan, percent, plainNumber, signedMoneyWan } from "./format";
import { sumHeatmapByProvince, sumHeatmapByWeightBand } from "./heatmapUtils";
import type { ContributionHeatmap, DashboardData, Overview, RankItem } from "./types";
export function OverviewView({
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

export function ImportView({ data }: { data: DashboardData | null }) {
  const job = data?.importJob;
  const validation = data?.importValidation;
  const errors = data?.importErrors;
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
            <span className={errors?.error_count ? "fail" : ""}>错误 {errors?.error_count ?? 0}</span>
          </div>
        </article>
      </section>

      <article className="panel wide">
        <div className="panel-head">
          <h2>导入错误</h2>
          <span>结构、字段、校验与运行错误</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>级别</th>
              <th>Sheet</th>
              <th>行</th>
              <th>列/指标</th>
              <th>错误码</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            {errors?.errors.length ? (
              errors.errors.map((error, index) => (
                <tr key={`${error.error_code}-${error.sheet_name ?? "job"}-${error.row_number ?? index}`}>
                  <td>
                    <span className={error.severity === "error" ? "result-fail" : "result-pass"}>
                      {error.severity}
                    </span>
                  </td>
                  <td>{error.sheet_name ?? "-"}</td>
                  <td>{error.row_number ?? "-"}</td>
                  <td>{error.column_name ?? "-"}</td>
                  <td>{error.error_code}</td>
                  <td>{error.error_message}</td>
                </tr>
              ))
            ) : (
              <EmptyRows colSpan={6} />
            )}
          </tbody>
        </table>
      </article>

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

export function FranchiseView({ data, maxContribution }: { data: DashboardData | null; maxContribution: number }) {
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

export function SiteView({ data }: { data: DashboardData | null }) {
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

export function FlowView({ heatmap }: { heatmap: ContributionHeatmap | null | undefined }) {
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

export function DeductionView({ data }: { data: DashboardData | null }) {
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
