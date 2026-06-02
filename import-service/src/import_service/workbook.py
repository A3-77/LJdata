from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from .models import OverviewCheck, SheetProfile, WorkbookInspection


SHEET_RULES: dict[str, dict[str, int | None]] = {
    "总表-加盟商": {"header_start_row": 1, "header_end_row": 3, "data_start_row": 5, "total_row": 4},
    "总表-网点": {"header_start_row": 1, "header_end_row": 3, "data_start_row": 5, "total_row": 4},
    "总表-一口价": {"header_start_row": 2, "header_end_row": 2, "data_start_row": 3, "total_row": 1},
    "辽宁区域贡献": {"header_start_row": 1, "header_end_row": 2, "data_start_row": 3, "total_row": None},
    "加盟商贡献": {"header_start_row": 1, "header_end_row": 2, "data_start_row": 3, "total_row": None},
    "出港考核、派费补贴": {"header_start_row": 1, "header_end_row": 1, "data_start_row": 2, "total_row": None},
    "包仓费明细": {"header_start_row": 1, "header_end_row": 1, "data_start_row": 2, "total_row": None},
    "运营管理类汇总表": {"header_start_row": 1, "header_end_row": 1, "data_start_row": 2, "total_row": None},
}


def _num(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def inspect_workbook(path: str | Path) -> WorkbookInspection:
    source = Path(path)
    workbook = load_workbook(source, read_only=True, data_only=True)

    sheets: list[SheetProfile] = []
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        rule = SHEET_RULES.get(sheet_name, {})
        sheets.append(
            SheetProfile(
                name=sheet_name,
                max_row=ws.max_row or 0,
                max_col=ws.max_column or 0,
                header_start_row=rule.get("header_start_row"),
                header_end_row=rule.get("header_end_row"),
                data_start_row=rule.get("data_start_row"),
                total_row=rule.get("total_row"),
            )
        )

    overview = extract_overview_check(workbook)
    return WorkbookInspection(
        path=str(source),
        sheet_count=len(workbook.sheetnames),
        sheets=sheets,
        overview=overview,
    )


def extract_overview_check(workbook) -> OverviewCheck:
    franchise_total = None
    site_total = None

    if "总表-加盟商" in workbook.sheetnames:
        ws = workbook["总表-加盟商"]
        franchise_total = next(ws.iter_rows(min_row=4, max_row=4, values_only=True), None)

    if "总表-网点" in workbook.sheetnames:
        ws = workbook["总表-网点"]
        site_total = next(ws.iter_rows(min_row=4, max_row=4, values_only=True), None)

    return OverviewCheck(
        franchise_count=_num(franchise_total[4]) if franchise_total else None,
        site_count=_num(site_total[5]) if site_total else None,
        outbound_tickets=_num(franchise_total[6]) if franchise_total else None,
        outbound_weight=_num(franchise_total[7]) if franchise_total else None,
        inbound_signed_tickets=_num(franchise_total[38]) if franchise_total else None,
        outbound_contribution=_num(franchise_total[35]) if franchise_total else None,
        inbound_contribution=_num(franchise_total[68]) if franchise_total else None,
        total_contribution=_num(franchise_total[69]) if franchise_total else None,
        deduction_total=_num(franchise_total[66]) if franchise_total else None,
    )

