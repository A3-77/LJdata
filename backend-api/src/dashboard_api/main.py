from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import ImportJobResponse, OverviewResponse, RankItem

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
    # TODO: Replace with PostgreSQL query against v_dashboard_overview.
    return OverviewResponse(
        period_month=period_month,
        region_code=region_code,
        franchise_count=155,
        site_count=293,
        outbound_tickets=25342926,
        outbound_weight=65988013.97,
        inbound_signed_tickets=58097658,
        outbound_contribution=33411654.7741,
        inbound_contribution=6625333.59,
        total_contribution=40036988.3641,
        deduction_total=6448104.21,
    )


@app.get("/api/dashboard/franchises/rank", response_model=list[RankItem])
def franchise_rank(period_month: str = "202604", metric: str = "total_contribution", limit: int = 10) -> list[RankItem]:
    # TODO: Replace with PostgreSQL query against v_franchise_rank.
    items = [
        RankItem(
            name="沈阳加盟商一百三十一(项目)",
            total_contribution=8576417.9666,
            outbound_contribution=8429270.7166,
            inbound_contribution=147147.25,
            deduction_total=57186.31,
            tags=["高贡献"],
        ),
        RankItem(
            name="沈阳加盟商六十三(孙贺焱)",
            total_contribution=2750968.4289,
            outbound_contribution=2631607.4789,
            inbound_contribution=119360.95,
            deduction_total=28772.31,
            tags=["高贡献"],
        ),
        RankItem(
            name="大连加盟商二十一(邵文东)",
            total_contribution=-246344.4746,
            outbound_contribution=25530.3554,
            inbound_contribution=-271874.83,
            deduction_total=56737.44,
            tags=["负贡献", "进港亏损"],
        ),
    ]
    return items[:limit]


@app.get("/api/import/jobs/{job_id}", response_model=ImportJobResponse)
def import_job(job_id: int) -> ImportJobResponse:
    # TODO: Replace with import_job table lookup.
    return ImportJobResponse(job_id=job_id, status="pending", progress=0, message="Import worker not connected yet")

