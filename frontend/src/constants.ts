import type { ViewKey } from "./types";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";
export const SNAPSHOT_MODE = import.meta.env.VITE_SNAPSHOT_MODE === "true";
export const PERIOD_MONTH = import.meta.env.VITE_PERIOD_MONTH ?? "202604";
export const REGION_CODE = import.meta.env.VITE_REGION_CODE ?? "LN";
export const REGION_LABEL = import.meta.env.VITE_REGION_LABEL ?? "辽宁";
export const IMPORT_JOB_ID = Number(import.meta.env.VITE_IMPORT_JOB_ID ?? "1");
export const TEMPLATE_CODE = import.meta.env.VITE_TEMPLATE_CODE ?? "franchise_contribution_v1";

export const WEIGHT_BANDS = ["0.3", "0.5", "1", "2", "3.2", "4", "5.2", "6", "7", "8", "9", "10.3", "＞10.3"];

export const NAV_ITEMS: { key: ViewKey; label: string; enabled: boolean }[] = [
  { key: "overview", label: "经营总览", enabled: true },
  { key: "analysis", label: "分析重点", enabled: true },
  { key: "franchise", label: "加盟商贡献", enabled: true },
  { key: "site", label: "网点下钻", enabled: true },
  { key: "flow", label: "目的省份与公斤段", enabled: true },
  { key: "deduction", label: "扣款与补贴", enabled: true },
  { key: "import", label: "数据导入", enabled: true },
];

export const METRIC_LABELS: Record<string, string> = {
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

export const STATUS_LABELS: Record<string, string> = {
  pending: "待处理",
  running: "处理中",
  completed: "已完成",
  failed: "失败",
};
