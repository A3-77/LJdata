import { STATUS_LABELS } from "./constants";
import { moneyWan, percent } from "./format";
import type { RankItem } from "./types";

export function KpiCard(props: { label: string; value: string; tone?: "good" | "risk" | "neutral"; loading?: boolean }) {
  return (
    <section className={`kpi ${props.tone ?? "neutral"} ${props.loading ? "loading" : ""}`}>
      <span>{props.label}</span>
      <strong>{props.loading ? "" : props.value}</strong>
    </section>
  );
}

export function StatusPill({ status }: { status: string | undefined }) {
  const normalized = status ?? "pending";
  return <span className={`status-pill ${normalized}`}>{STATUS_LABELS[normalized] ?? normalized}</span>;
}

export function RankBar({ item, max }: { item: RankItem; max: number }) {
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

export function DeductionBar({ item, max }: { item: RankItem; max: number }) {
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

export function EmptyRows({ colSpan }: { colSpan: number }) {
  return (
    <tr>
      <td className="empty-cell" colSpan={colSpan}>暂无数据</td>
    </tr>
  );
}
