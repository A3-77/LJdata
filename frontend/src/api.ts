import { API_BASE, DEMO_MODE, IMPORT_JOB_ID, PERIOD_MONTH, REGION_CODE } from "./constants";
import { demoData } from "./demoData";
import type { ContributionHeatmap, DashboardData, ImportJob, ImportValidationResponse, Overview, RankItem, SiteRankItem } from "./types";

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

export async function fetchDashboardData(): Promise<DashboardData> {
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
