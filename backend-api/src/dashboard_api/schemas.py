from __future__ import annotations

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    period_month: str
    region_code: str
    franchise_count: int
    site_count: int
    outbound_tickets: float
    outbound_weight: float
    inbound_signed_tickets: float
    outbound_contribution: float
    inbound_contribution: float
    total_contribution: float
    deduction_total: float


class RankItem(BaseModel):
    name: str
    total_contribution: float
    outbound_contribution: float | None = None
    inbound_contribution: float | None = None
    deduction_total: float | None = None
    tags: list[str] = []


class ImportJobResponse(BaseModel):
    job_id: int
    status: str
    progress: int
    message: str | None = None

