from __future__ import annotations

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import (
    check_database,
    get_contribution_heatmap,
    get_franchise_rank,
    get_import_errors,
    get_import_job,
    get_import_validation_results,
    get_latest_import_job,
    get_overview,
    get_site_rank,
    list_import_jobs,
)
from .schemas import (
    ContributionHeatmapResponse,
    ImportErrorResponse,
    ImportJobHistoryItem,
    ImportJobResponse,
    ImportValidationResponse,
    OverviewResponse,
    RankItem,
    SiteRankItem,
    UploadImportResponse,
)
from .import_runner import run_workbook_import, save_upload

app = FastAPI(title="Liaoning Franchise Contribution Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", **check_database()}


def require_import_token(token: str | None) -> None:
    if settings.import_api_token and token != settings.import_api_token:
        raise HTTPException(status_code=401, detail="invalid import token")


@app.get("/api/dashboard/overview", response_model=OverviewResponse)
def overview(period_month: str = "202604", region_code: str = "LN") -> OverviewResponse:
    return get_overview(period_month=period_month, region_code=region_code)


@app.get("/api/dashboard/franchises/rank", response_model=list[RankItem])
def franchise_rank(
    period_month: str = "202604",
    region_code: str = "LN",
    metric: str = "total_contribution",
    direction: str = "desc",
    limit: int = 10,
) -> list[RankItem]:
    return get_franchise_rank(
        period_month=period_month,
        region_code=region_code,
        metric=metric,
        direction=direction,
        limit=limit,
    )


@app.get("/api/dashboard/sites/rank", response_model=list[SiteRankItem])
def site_rank(
    period_month: str = "202604",
    region_code: str = "LN",
    metric: str = "total_contribution",
    direction: str = "desc",
    limit: int = 10,
) -> list[SiteRankItem]:
    return get_site_rank(
        period_month=period_month,
        region_code=region_code,
        metric=metric,
        direction=direction,
        limit=limit,
    )


@app.get("/api/dashboard/contribution-flow/heatmap", response_model=ContributionHeatmapResponse)
def contribution_flow_heatmap(
    period_month: str = "202604",
    region_code: str = "LN",
    scope_type: str = "region",
    metric: str = "contribution_total",
    province_limit: int = 12,
) -> ContributionHeatmapResponse:
    return get_contribution_heatmap(
        period_month=period_month,
        region_code=region_code,
        scope_type=scope_type,
        metric=metric,
        province_limit=province_limit,
    )


@app.get("/api/import/jobs/latest", response_model=ImportJobResponse)
def latest_import_job(period_month: str | None = None, region_code: str | None = None) -> ImportJobResponse:
    return get_latest_import_job(period_month=period_month, region_code=region_code)


@app.get("/api/import/jobs", response_model=list[ImportJobHistoryItem])
def import_jobs(
    period_month: str | None = None,
    region_code: str | None = None,
    limit: int = 10,
) -> list[ImportJobHistoryItem]:
    return list_import_jobs(period_month=period_month, region_code=region_code, limit=limit)


@app.get("/api/import/jobs/{job_id}", response_model=ImportJobResponse)
def import_job(job_id: int) -> ImportJobResponse:
    return get_import_job(job_id)


@app.get("/api/import/jobs/{job_id}/validation-results", response_model=ImportValidationResponse)
def import_validation_results(job_id: int) -> ImportValidationResponse:
    return get_import_validation_results(job_id)


@app.get("/api/import/jobs/{job_id}/errors", response_model=ImportErrorResponse)
def import_errors(job_id: int) -> ImportErrorResponse:
    return get_import_errors(job_id)


@app.post("/api/import/files", response_model=UploadImportResponse)
async def upload_import_file(
    file: UploadFile = File(...),
    region_code: str = settings.default_region_code,
    region_name: str = settings.default_region_name,
    template_code: str = settings.default_template_code,
    replace_period: bool = True,
    x_import_token: str | None = Header(default=None, alias="X-Import-Token"),
) -> UploadImportResponse:
    require_import_token(x_import_token)
    workbook_path = await save_upload(file)
    return run_workbook_import(
        workbook_path,
        region_code=region_code,
        region_name=region_name,
        template_code=template_code,
        replace_period=replace_period,
    )
