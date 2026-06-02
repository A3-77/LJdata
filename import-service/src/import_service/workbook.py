from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from .models import ContributionFlowRow, FranchiseMonthRow, OverviewCheck, SheetProfile, SiteMonthRow, WorkbookInspection
from .templates import TemplateProfile, get_template_profile


DEFAULT_TEMPLATE_CODE = "franchise_contribution_v1"


def _num(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _flag_yes_no(value: object) -> bool | None:
    raw = _text(value)
    if raw in {"是", "Y", "Yes", "true", "True", "1"}:
        return True
    if raw in {"否", "N", "No", "false", "False", "0"}:
        return False
    return None


def _cell(row: list[object], index: int) -> object | None:
    return row[index] if index < len(row) else None


def _profile(template_code: str = DEFAULT_TEMPLATE_CODE) -> TemplateProfile:
    return get_template_profile(template_code)


def _sheet_name_for_code(workbook, profile: TemplateProfile, standard_sheet_code: str) -> str | None:
    return profile.sheet_name_for_code(list(workbook.sheetnames), standard_sheet_code)


def inspect_workbook(path: str | Path, *, template_code: str = DEFAULT_TEMPLATE_CODE) -> WorkbookInspection:
    source = Path(path)
    workbook = load_workbook(source, read_only=True, data_only=True)
    profile = _profile(template_code)

    sheets: list[SheetProfile] = []
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        rule = profile.rule_for_sheet(sheet_name)
        sheets.append(
            SheetProfile(
                name=sheet_name,
                max_row=ws.max_row or 0,
                max_col=ws.max_column or 0,
                standard_sheet_code=rule.standard_sheet_code if rule else None,
                header_start_row=rule.header_start_row if rule else None,
                header_end_row=rule.header_end_row if rule else None,
                data_start_row=rule.data_start_row if rule else None,
                total_row=rule.total_row if rule else None,
            )
        )

    overview = extract_overview_check(workbook, profile=profile)
    return WorkbookInspection(
        path=str(source),
        sheet_count=len(workbook.sheetnames),
        sheets=sheets,
        overview=overview,
    )


def infer_period_month(workbook, *, profile: TemplateProfile | None = None) -> str:
    profile = profile or _profile()
    sheet_name = _sheet_name_for_code(workbook, profile, "franchise_summary")
    rule = profile.rule_for_code("franchise_summary")
    if sheet_name and rule:
        ws = workbook[sheet_name]
        first_data_row = next(ws.iter_rows(min_row=rule.data_start_row, max_row=rule.data_start_row, values_only=True), None)
        if first_data_row:
            value = _text(_cell(list(first_data_row), 3))
            if value:
                return value
    return ""


def parse_franchise_month_rows(path: str | Path, *, template_code: str = DEFAULT_TEMPLATE_CODE) -> list[FranchiseMonthRow]:
    workbook = load_workbook(Path(path), read_only=True, data_only=True)
    profile = _profile(template_code)
    sheet_name = _sheet_name_for_code(workbook, profile, "franchise_summary")
    rule = profile.rule_for_code("franchise_summary")
    if not sheet_name or not rule:
        return []

    ws = workbook[sheet_name]
    rows: list[FranchiseMonthRow] = []

    for raw in ws.iter_rows(min_row=rule.data_start_row, values_only=True):
        row = list(raw)
        franchise_name = _text(_cell(row, 4))
        if not franchise_name:
            continue

        rows.append(
            FranchiseMonthRow(
                period_month=_text(_cell(row, 3)),
                franchise_name=franchise_name,
                daily_over_5000_flag=_flag_yes_no(_cell(row, 1)),
                outbound_tickets=_num(_cell(row, 6)),
                outbound_weight=_num(_cell(row, 7)),
                outbound_avg_weight=_num(_cell(row, 8)),
                waybill_fee=_num(_cell(row, 9)),
                transfer_fee=_num(_cell(row, 10)),
                warehouse_fee=_num(_cell(row, 11)),
                operation_fee=_num(_cell(row, 12)),
                dispatch_fee=_num(_cell(row, 14)),
                one_price_rebate=_num(_cell(row, 15)),
                outbound_contribution=_num(_cell(row, 35)),
                outbound_unit_contribution=_num(_cell(row, 36)),
                outbound_kg_contribution=_num(_cell(row, 37)),
                inbound_signed_tickets=_num(_cell(row, 38)),
                inbound_weight=_num(_cell(row, 39)),
                inbound_dispatch_income=_num(_cell(row, 41)),
                inbound_dispatch_cost=_num(_cell(row, 44)),
                deduction_total=_num(_cell(row, 66)),
                inbound_contribution=_num(_cell(row, 68)),
                total_contribution=_num(_cell(row, 69)),
                outbound_pass_contribution=_num(_cell(row, 70)),
                inbound_pass_contribution=_num(_cell(row, 71)),
            )
        )

    return rows


def parse_contribution_flow_rows(
    path: str | Path,
    *,
    scope_type: str,
    include_total_rows: bool = False,
    region_code: str = "LN",
    template_code: str = DEFAULT_TEMPLATE_CODE,
) -> list[ContributionFlowRow]:
    workbook = load_workbook(Path(path), read_only=True, data_only=True)
    profile = _profile(template_code)
    if scope_type == "region":
        standard_sheet_code = "contribution_region"
    elif scope_type == "franchise":
        standard_sheet_code = "contribution_franchise"
    else:
        raise ValueError("scope_type must be 'region' or 'franchise'")

    sheet_name = _sheet_name_for_code(workbook, profile, standard_sheet_code)
    rule = profile.rule_for_code(standard_sheet_code)
    if not sheet_name or not rule:
        return []

    period_month = infer_period_month(workbook, profile=profile)
    ws = workbook[sheet_name]
    rows: list[ContributionFlowRow] = []

    for raw in ws.iter_rows(min_row=rule.data_start_row, values_only=True):
        row = list(raw)
        destination = _text(_cell(row, 5))
        if not destination:
            continue
        if not include_total_rows and destination in {"小计", "合计", "总计"}:
            continue

        franchise_name = _text(_cell(row, 1)) if scope_type == "franchise" else None
        if scope_type == "franchise" and not franchise_name:
            continue

        row_region_code = region_code if scope_type == "region" else None

        for offset, weight_band in enumerate(profile.weight_bands):
            rows.append(
                ContributionFlowRow(
                    period_month=period_month,
                    scope_type=scope_type,
                    region_code=row_region_code,
                    franchise_name=franchise_name,
                    destination_province=destination,
                    weight_band=weight_band,
                    ticket_count=_num(_cell(row, profile.contribution_group_starts["ticket_count"] + offset)),
                    ticket_share=_num(_cell(row, profile.contribution_group_starts["ticket_share"] + offset)),
                    weight_total=_num(_cell(row, profile.contribution_group_starts["weight_total"] + offset)),
                    four_fee_total=_num(_cell(row, profile.contribution_group_starts["four_fee_total"] + offset)),
                    settlement_price=_num(_cell(row, profile.contribution_group_starts["settlement_price"] + offset)),
                    dispatch_fee=_num(_cell(row, profile.contribution_group_starts["dispatch_fee"] + offset)),
                    contribution_total=_num(_cell(row, profile.contribution_group_starts["contribution_total"] + offset)),
                    unit_four_fee=_num(_cell(row, profile.contribution_group_starts["unit_four_fee"] + offset)),
                    unit_settlement_price=_num(_cell(row, profile.contribution_group_starts["unit_settlement_price"] + offset)),
                    unit_dispatch_fee=_num(_cell(row, profile.contribution_group_starts["unit_dispatch_fee"] + offset)),
                    unit_contribution=_num(_cell(row, profile.contribution_group_starts["unit_contribution"] + offset)),
                    kg_contribution=_num(_cell(row, profile.contribution_group_starts["kg_contribution"] + offset)),
                )
            )

    return rows


def parse_site_month_rows(path: str | Path, *, template_code: str = DEFAULT_TEMPLATE_CODE) -> list[SiteMonthRow]:
    workbook = load_workbook(Path(path), read_only=True, data_only=True)
    profile = _profile(template_code)
    sheet_name = _sheet_name_for_code(workbook, profile, "site_summary")
    rule = profile.rule_for_code("site_summary")
    if not sheet_name or not rule:
        return []

    ws = workbook[sheet_name]
    rows: list[SiteMonthRow] = []

    for raw in ws.iter_rows(min_row=rule.data_start_row, values_only=True):
        row = list(raw)
        franchise_name = _text(_cell(row, 4))
        site_name = _text(_cell(row, 5))
        if not franchise_name or not site_name:
            continue

        rows.append(
            SiteMonthRow(
                period_month=_text(_cell(row, 3)),
                franchise_name=franchise_name,
                site_name=site_name,
                site_status=_text(_cell(row, 0)) or None,
                daily_over_5000_flag=_flag_yes_no(_cell(row, 1)),
                outbound_tickets=_num(_cell(row, 6)),
                outbound_weight=_num(_cell(row, 7)),
                outbound_contribution=_num(_cell(row, 35)),
                inbound_signed_tickets=_num(_cell(row, 38)),
                inbound_contribution=_num(_cell(row, 68)),
                deduction_total=_num(_cell(row, 66)),
                total_contribution=_num(_cell(row, 69)),
            )
        )

    return rows


def extract_overview_check(workbook, *, profile: TemplateProfile | None = None) -> OverviewCheck:
    profile = profile or _profile()
    franchise_total = None
    site_total = None

    franchise_sheet_name = _sheet_name_for_code(workbook, profile, "franchise_summary")
    franchise_rule = profile.rule_for_code("franchise_summary")
    if franchise_sheet_name and franchise_rule and franchise_rule.total_row:
        ws = workbook[franchise_sheet_name]
        franchise_total = next(ws.iter_rows(min_row=franchise_rule.total_row, max_row=franchise_rule.total_row, values_only=True), None)

    site_sheet_name = _sheet_name_for_code(workbook, profile, "site_summary")
    site_rule = profile.rule_for_code("site_summary")
    if site_sheet_name and site_rule and site_rule.total_row:
        ws = workbook[site_sheet_name]
        site_total = next(ws.iter_rows(min_row=site_rule.total_row, max_row=site_rule.total_row, values_only=True), None)

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
