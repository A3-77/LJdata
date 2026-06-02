from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import (
    get_contribution_heatmap,
    get_franchise_rank,
    get_import_errors,
    get_import_job,
    get_import_validation_results,
    get_overview,
    get_site_rank,
)
from .schemas import (
    ContributionHeatmapResponse,
    ImportErrorResponse,
    ImportJobResponse,
    ImportValidationResponse,
    OverviewResponse,
    RankItem,
    SiteRankItem,
)

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


@app.get("/api/import/jobs/{job_id}", response_model=ImportJobResponse)
def import_job(job_id: int) -> ImportJobResponse:
    return get_import_job(job_id)


@app.get("/api/import/jobs/{job_id}/validation-results", response_model=ImportValidationResponse)
def import_validation_results(job_id: int) -> ImportValidationResponse:
    return get_import_validation_results(job_id)


@app.get("/api/import/jobs/{job_id}/errors", response_model=ImportErrorResponse)
def import_errors(job_id: int) -> ImportErrorResponse:
    return get_import_errors(job_id)
