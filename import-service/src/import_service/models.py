from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SheetProfile:
    name: str
    max_row: int
    max_col: int
    header_start_row: int | None = None
    header_end_row: int | None = None
    data_start_row: int | None = None
    total_row: int | None = None


@dataclass(frozen=True)
class OverviewCheck:
    franchise_count: float | None
    site_count: float | None
    outbound_tickets: float | None
    outbound_weight: float | None
    inbound_signed_tickets: float | None
    outbound_contribution: float | None
    inbound_contribution: float | None
    total_contribution: float | None
    deduction_total: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "franchise_count": self.franchise_count,
            "site_count": self.site_count,
            "outbound_tickets": self.outbound_tickets,
            "outbound_weight": self.outbound_weight,
            "inbound_signed_tickets": self.inbound_signed_tickets,
            "outbound_contribution": self.outbound_contribution,
            "inbound_contribution": self.inbound_contribution,
            "total_contribution": self.total_contribution,
            "deduction_total": self.deduction_total,
        }


@dataclass(frozen=True)
class WorkbookInspection:
    path: str
    sheet_count: int
    sheets: list[SheetProfile]
    overview: OverviewCheck

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sheet_count": self.sheet_count,
            "sheets": [sheet.__dict__ for sheet in self.sheets],
            "overview": self.overview.as_dict(),
        }


@dataclass(frozen=True)
class FranchiseMonthRow:
    period_month: str
    franchise_name: str
    daily_over_5000_flag: bool | None
    outbound_tickets: float | None
    outbound_weight: float | None
    outbound_avg_weight: float | None
    waybill_fee: float | None
    transfer_fee: float | None
    warehouse_fee: float | None
    operation_fee: float | None
    dispatch_fee: float | None
    one_price_rebate: float | None
    outbound_contribution: float | None
    outbound_unit_contribution: float | None
    outbound_kg_contribution: float | None
    inbound_signed_tickets: float | None
    inbound_weight: float | None
    inbound_dispatch_income: float | None
    inbound_dispatch_cost: float | None
    deduction_total: float | None
    inbound_contribution: float | None
    total_contribution: float | None
    outbound_pass_contribution: float | None
    inbound_pass_contribution: float | None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__


@dataclass(frozen=True)
class SiteMonthRow:
    period_month: str
    franchise_name: str
    site_name: str
    site_status: str | None
    daily_over_5000_flag: bool | None
    outbound_tickets: float | None
    outbound_weight: float | None
    outbound_contribution: float | None
    inbound_signed_tickets: float | None
    inbound_contribution: float | None
    deduction_total: float | None
    total_contribution: float | None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__


@dataclass(frozen=True)
class ContributionFlowRow:
    period_month: str
    scope_type: str
    region_code: str | None
    franchise_name: str | None
    destination_province: str
    weight_band: str
    ticket_count: float | None
    ticket_share: float | None
    weight_total: float | None
    four_fee_total: float | None
    settlement_price: float | None
    dispatch_fee: float | None
    contribution_total: float | None
    unit_four_fee: float | None
    unit_settlement_price: float | None
    unit_dispatch_fee: float | None
    unit_contribution: float | None
    kg_contribution: float | None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__
