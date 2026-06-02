from __future__ import annotations

from collections.abc import Iterable

from .models import FranchiseMonthRow, ImportErrorRow, OverviewCheck, SiteMonthRow, ValidationResult
from .templates import get_template_profile
from .workbook import inspect_workbook, parse_franchise_month_rows, parse_site_month_rows

SUMMARY_METRICS = {
    "franchise_count": "加盟商数",
    "site_count": "网点数",
    "outbound_tickets": "出港票量",
    "outbound_weight": "出港重量",
    "inbound_signed_tickets": "进港签收量",
    "outbound_contribution": "出港总贡献",
    "inbound_contribution": "进港总贡献",
    "total_contribution": "总贡献",
    "deduction_total": "扣款小计",
}


def _sum(values: Iterable[float | None]) -> float:
    return sum(value or 0 for value in values)


def _result(rule_code: str, metric_code: str, expected: float | None, actual: float | None, tolerance: float) -> ValidationResult:
    if expected is None or actual is None:
        diff = None
        passed = False
    else:
        diff = actual - expected
        passed = abs(diff) <= tolerance
    metric_name = SUMMARY_METRICS.get(metric_code, metric_code)
    return ValidationResult(
        rule_code=rule_code,
        metric_code=metric_code,
        expected_value=expected,
        actual_value=actual,
        diff_value=diff,
        tolerance=tolerance,
        passed=passed,
        severity="error" if not passed else "info",
        message=f"{metric_name}: expected {expected}, actual {actual}, diff {diff}",
    )


def validate_summary_totals(
    overview: OverviewCheck,
    franchise_rows: list[FranchiseMonthRow],
    site_rows: list[SiteMonthRow],
    *,
    tolerance: float = 0.01,
) -> list[ValidationResult]:
    franchise_count = float(len(franchise_rows))
    site_count = float(len(site_rows))
    actuals = {
        "franchise_count": franchise_count,
        "site_count": site_count,
        "outbound_tickets": _sum(row.outbound_tickets for row in franchise_rows),
        "outbound_weight": _sum(row.outbound_weight for row in franchise_rows),
        "inbound_signed_tickets": _sum(row.inbound_signed_tickets for row in franchise_rows),
        "outbound_contribution": _sum(row.outbound_contribution for row in franchise_rows),
        "inbound_contribution": _sum(row.inbound_contribution for row in franchise_rows),
        "total_contribution": _sum(row.total_contribution for row in franchise_rows),
        "deduction_total": _sum(row.deduction_total for row in franchise_rows),
    }
    expected = overview.as_dict()
    return [
        _result("summary_total_reconciliation", metric_code, expected.get(metric_code), actual, tolerance)
        for metric_code, actual in actuals.items()
    ]


def validate_required_sheets(path: str, *, template_code: str = "franchise_contribution_v1") -> list[ImportErrorRow]:
    inspection = inspect_workbook(path, template_code=template_code)
    present_codes = {sheet.standard_sheet_code for sheet in inspection.sheets if sheet.standard_sheet_code}
    profile = get_template_profile(template_code)

    errors: list[ImportErrorRow] = []
    for rule in profile.sheet_rules:
        if rule.required and rule.standard_sheet_code not in present_codes:
            errors.append(
                ImportErrorRow(
                    severity="error",
                    sheet_name=rule.sheet_name_pattern,
                    row_number=None,
                    column_name=None,
                    error_code="required_sheet_missing",
                    error_message=(
                        f"Required sheet is missing for {rule.standard_sheet_code}: "
                        f"expected pattern {rule.sheet_name_pattern}"
                    ),
                )
            )
    return errors


def validation_results_to_import_errors(results: Iterable[ValidationResult]) -> list[ImportErrorRow]:
    errors: list[ImportErrorRow] = []
    for result in results:
        if result.passed:
            continue
        errors.append(
            ImportErrorRow(
                severity=result.severity,
                sheet_name=None,
                row_number=None,
                column_name=result.metric_code,
                error_code=result.rule_code,
                error_message=result.message,
            )
        )
    return errors


def validate_workbook(
    path: str,
    *,
    tolerance: float = 0.01,
    template_code: str = "franchise_contribution_v1",
) -> list[ValidationResult]:
    inspection = inspect_workbook(path, template_code=template_code)
    franchise_rows = parse_franchise_month_rows(path, template_code=template_code)
    site_rows = parse_site_month_rows(path, template_code=template_code)
    return validate_summary_totals(inspection.overview, franchise_rows, site_rows, tolerance=tolerance)
