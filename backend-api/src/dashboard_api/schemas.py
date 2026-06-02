from __future__ import annotations

from pydantic import BaseModel, Field


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
    tags: list[str] = Field(default_factory=list)


class SiteRankItem(BaseModel):
    name: str
    franchise_name: str
    site_status: str | None = None
    total_contribution: float
    outbound_contribution: float | None = None
    inbound_contribution: float | None = None
    deduction_total: float | None = None
    outbound_tickets: float | None = None
    inbound_signed_tickets: float | None = None
    tags: list[str] = Field(default_factory=list)


class ImportJobResponse(BaseModel):
    job_id: int
    status: str
    progress: int
    message: str | None = None


class ImportValidationResult(BaseModel):
    rule_code: str
    metric_code: str
    expected_value: float | None = None
    actual_value: float | None = None
    diff_value: float | None = None
    tolerance: float | None = None
    passed: bool
    severity: str
    message: str | None = None


class ImportValidationResponse(BaseModel):
    job_id: int
    passed: int
    failed: int
    results: list[ImportValidationResult]


class ImportErrorItem(BaseModel):
    severity: str
    sheet_name: str | None = None
    row_number: int | None = None
    column_name: str | None = None
    error_code: str
    error_message: str


class ImportErrorResponse(BaseModel):
    job_id: int
    error_count: int
    errors: list[ImportErrorItem]


class ContributionHeatmapCell(BaseModel):
    destination_province: str
    weight_band: str
    value: float
    ticket_count: float | None = None
    weight_total: float | None = None


class ContributionHeatmapResponse(BaseModel):
    period_month: str
    region_code: str
    scope_type: str
    metric: str
    provinces: list[str]
    weight_bands: list[str]
    cells: list[ContributionHeatmapCell]
