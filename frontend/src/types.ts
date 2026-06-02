export type Overview = {
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

export type RankItem = {
  name: string;
  total_contribution: number;
  outbound_contribution: number | null;
  inbound_contribution: number | null;
  deduction_total: number | null;
  tags: string[];
};

export type SiteRankItem = RankItem & {
  franchise_name: string;
  site_status: string | null;
  outbound_tickets: number | null;
  inbound_signed_tickets: number | null;
};

export type DashboardData = {
  overview: Overview;
  topRank: RankItem[];
  bottomRank: RankItem[];
  siteRank: SiteRankItem[];
  heatmap: ContributionHeatmap;
  importJob: ImportJob | null;
  importValidation: ImportValidationResponse | null;
};

export type ContributionHeatmapCell = {
  destination_province: string;
  weight_band: string;
  value: number;
  ticket_count: number | null;
  weight_total: number | null;
};

export type ContributionHeatmap = {
  period_month: string;
  region_code: string;
  scope_type: string;
  metric: string;
  provinces: string[];
  weight_bands: string[];
  cells: ContributionHeatmapCell[];
};

export type ImportJob = {
  job_id: number;
  status: string;
  progress: number;
  message: string | null;
};

export type ImportValidationResult = {
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

export type ImportValidationResponse = {
  job_id: number;
  passed: number;
  failed: number;
  results: ImportValidationResult[];
};

export type ViewKey = "overview" | "franchise" | "site" | "flow" | "deduction" | "import";
