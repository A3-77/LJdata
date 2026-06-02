export function moneyWan(value: number | null | undefined) {
  const raw = value ?? 0;
  return `${(raw / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
}

export function countWan(value: number | null | undefined) {
  const raw = value ?? 0;
  return `${(raw / 10000).toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} 万`;
}

export function plainNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return value.toLocaleString("zh-CN", { maximumFractionDigits: 4 });
}

export function signedMoneyWan(value: number | null | undefined) {
  const raw = value ?? 0;
  const sign = raw > 0 ? "+" : "";
  return `${sign}${moneyWan(raw)}`;
}

export function percent(part: number, total: number) {
  if (!Number.isFinite(part) || !Number.isFinite(total) || total === 0) {
    return 0;
  }
  return part / total * 100;
}
