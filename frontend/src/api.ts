import { API_BASE, DEMO_MODE, IMPORT_JOB_ID, PERIOD_MONTH, REGION_CODE } from "./constants";
import { demoData } from "./demoData";
import type {
  ContributionHeatmap,
  DashboardData,
  ImportErrorResponse,
  ImportJob,
  ImportJobHistoryItem,
  ImportValidationResponse,
  Overview,
  RankItem,
  SiteRankItem,
} from "./types";

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

async function fetchImportJob(): Promise<ImportJob | null> {
  const params = `period_month=${PERIOD_MONTH}&region_code=${REGION_CODE}`;
  const latestJob = await fetchOptionalJson<ImportJob>(`/api/import/jobs/latest?${params}`);
  if (latestJob) {
    return latestJob;
  }
  return fetchOptionalJson<ImportJob>(`/api/import/jobs/${IMPORT_JOB_ID}`);
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
  const importJob = await fetchImportJob();
  const jobId = importJob?.job_id ?? IMPORT_JOB_ID;
  const [importJobs, importValidation, importErrors] = await Promise.all([
    fetchJson<ImportJobHistoryItem[]>(`/api/import/jobs?${params}&limit=8`),
    fetchOptionalJson<ImportValidationResponse>(`/api/import/jobs/${jobId}/validation-results`),
    fetchOptionalJson<ImportErrorResponse>(`/api/import/jobs/${jobId}/errors`),
  ]);
  return {
    overview: overviewData,
    topRank: topRankData,
    bottomRank: bottomRankData,
    siteRank,
    heatmap,
    importJob,
    importJobs,
    importValidation,
    importErrors,
  };
}
