import { API_BASE, DEMO_MODE, IMPORT_JOB_ID, PERIOD_MONTH, REGION_CODE, REGION_LABEL, TEMPLATE_CODE } from "./constants";
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
  UploadImportResponse,
} from "./types";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await responseError(response));
  }
  return response.json() as Promise<T>;
}

async function responseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item: unknown) => {
          if (item && typeof item === "object" && "msg" in item) {
            return String(item.msg);
          }
          return JSON.stringify(item);
        })
        .join("; ");
    }
  } catch {
    // Fall through to the HTTP status text.
  }
  return `${response.status} ${response.statusText}`;
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

export async function fetchImportDiagnostics(jobId: number): Promise<{
  importErrors: ImportErrorResponse | null;
  importValidation: ImportValidationResponse | null;
}> {
  if (DEMO_MODE) {
    return {
      importErrors: demoData.importErrors,
      importValidation: demoData.importValidation,
    };
  }

  const [importValidation, importErrors] = await Promise.all([
    fetchOptionalJson<ImportValidationResponse>(`/api/import/jobs/${jobId}/validation-results`),
    fetchOptionalJson<ImportErrorResponse>(`/api/import/jobs/${jobId}/errors`),
  ]);
  return { importErrors, importValidation };
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
  const [importJobs, diagnostics] = await Promise.all([
    fetchJson<ImportJobHistoryItem[]>(`/api/import/jobs?${params}&limit=8`),
    fetchImportDiagnostics(jobId),
  ]);
  return {
    overview: overviewData,
    topRank: topRankData,
    bottomRank: bottomRankData,
    siteRank,
    heatmap,
    importJob,
    importJobs,
    importValidation: diagnostics.importValidation,
    importErrors: diagnostics.importErrors,
  };
}

export async function uploadImportFile(file: File): Promise<UploadImportResponse> {
  if (DEMO_MODE) {
    throw new Error("演示模式不能上传文件，请连接真实 API 后再导入。");
  }

  const formData = new FormData();
  formData.append("file", file);
  const params = new URLSearchParams({
    period_month: PERIOD_MONTH,
    region_code: REGION_CODE,
    region_name: `${REGION_LABEL}区域`,
    template_code: TEMPLATE_CODE,
    replace_period: "true",
  });
  const response = await fetch(`${API_BASE}/api/import/files?${params.toString()}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await responseError(response));
  }
  return response.json() as Promise<UploadImportResponse>;
}
