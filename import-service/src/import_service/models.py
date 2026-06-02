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

