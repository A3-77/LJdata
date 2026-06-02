from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from .db import (
    create_import_job,
    finish_import_job,
    load_contribution_flow_rows,
    load_franchise_month_rows,
    load_site_month_rows,
    save_import_errors,
    save_validation_results,
)
from .models import ImportErrorRow
from .validation import (
    validate_required_sheets,
    validate_summary_totals,
    validate_workbook,
    validation_results_to_import_errors,
)
from .workbook import inspect_workbook, parse_contribution_flow_rows, parse_franchise_month_rows, parse_site_month_rows


def _exception_error(exc: Exception) -> ImportErrorRow:
    return ImportErrorRow(
        severity="error",
        sheet_name=None,
        row_number=None,
        column_name=None,
        error_code="import_runtime_error",
        error_message=str(exc),
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    warnings.filterwarnings("ignore", message=".*extension is not supported.*")
    warnings.filterwarnings("ignore", message=".*Conditional Formatting extension is not supported.*")

    parser = argparse.ArgumentParser(prog="dashboard-import")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect workbook structure and overview checks")
    inspect_parser.add_argument("xlsx", type=Path)
    inspect_parser.add_argument("--template-code", default="franchise_contribution_v1")

    validate_parser = subparsers.add_parser("validate", help="Validate workbook totals and supported reconciliation rules")
    validate_parser.add_argument("xlsx", type=Path)
    validate_parser.add_argument("--tolerance", type=float, default=0.01)
    validate_parser.add_argument("--template-code", default="franchise_contribution_v1")

    extract_parser = subparsers.add_parser("extract", help="Extract normalized rows from workbook")
    extract_subparsers = extract_parser.add_subparsers(dest="extract_command", required=True)

    franchise_parser = extract_subparsers.add_parser("franchise-summary", help="Extract 总表-加盟商 rows")
    franchise_parser.add_argument("xlsx", type=Path)
    franchise_parser.add_argument("--limit", type=int, default=5)
    franchise_parser.add_argument("--all", action="store_true", help="Print all rows")
    franchise_parser.add_argument("--template-code", default="franchise_contribution_v1")

    site_parser = extract_subparsers.add_parser("site-summary", help="Extract 总表-网点 rows")
    site_parser.add_argument("xlsx", type=Path)
    site_parser.add_argument("--limit", type=int, default=5)
    site_parser.add_argument("--all", action="store_true", help="Print all rows")
    site_parser.add_argument("--template-code", default="franchise_contribution_v1")

    flow_parser = extract_subparsers.add_parser("contribution-flow", help="Unpivot 辽宁区域贡献 or 加盟商贡献 rows")
    flow_parser.add_argument("xlsx", type=Path)
    flow_parser.add_argument("--scope", choices=["region", "franchise"], required=True)
    flow_parser.add_argument("--limit", type=int, default=5)
    flow_parser.add_argument("--all", action="store_true", help="Print all rows")
    flow_parser.add_argument("--include-total-rows", action="store_true")
    flow_parser.add_argument("--template-code", default="franchise_contribution_v1")

    load_parser = subparsers.add_parser("load-summary", help="Load franchise and site summaries into PostgreSQL")
    load_parser.add_argument("xlsx", type=Path)
    load_parser.add_argument("--database-url", required=True)
    load_parser.add_argument("--region-code", default="LN")
    load_parser.add_argument("--region-name", default="辽宁区域")
    load_parser.add_argument("--template-code", default="franchise_contribution_v1")
    load_parser.add_argument("--replace-period", action="store_true")

    load_workbook_parser = subparsers.add_parser("load-workbook", help="Load all currently supported workbook sheets into PostgreSQL")
    load_workbook_parser.add_argument("xlsx", type=Path)
    load_workbook_parser.add_argument("--database-url", required=True)
    load_workbook_parser.add_argument("--region-code", default="LN")
    load_workbook_parser.add_argument("--region-name", default="辽宁区域")
    load_workbook_parser.add_argument("--template-code", default="franchise_contribution_v1")
    load_workbook_parser.add_argument("--replace-period", action="store_true")

    load_flow_parser = subparsers.add_parser("load-contribution-flow", help="Load unpivoted contribution flow into PostgreSQL")
    load_flow_parser.add_argument("xlsx", type=Path)
    load_flow_parser.add_argument("--database-url", required=True)
    load_flow_parser.add_argument("--scope", choices=["region", "franchise"], required=True)
    load_flow_parser.add_argument("--region-code", default="LN")
    load_flow_parser.add_argument("--template-code", default="franchise_contribution_v1")
    load_flow_parser.add_argument("--replace-period", action="store_true")

    args = parser.parse_args()

    if args.command == "inspect":
        result = inspect_workbook(args.xlsx, template_code=args.template_code)
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        return

    if args.command == "validate":
        results = validate_workbook(args.xlsx, tolerance=args.tolerance, template_code=args.template_code)
        passed = sum(1 for result in results if result.passed)
        print(
            json.dumps(
                {
                    "passed": passed,
                    "failed": len(results) - passed,
                    "results": [result.as_dict() for result in results],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "extract" and args.extract_command == "franchise-summary":
        rows = parse_franchise_month_rows(args.xlsx, template_code=args.template_code)
        selected = rows if args.all else rows[: args.limit]
        print(json.dumps({"count": len(rows), "rows": [row.as_dict() for row in selected]}, ensure_ascii=False, indent=2))
        return

    if args.command == "extract" and args.extract_command == "site-summary":
        rows = parse_site_month_rows(args.xlsx, template_code=args.template_code)
        selected = rows if args.all else rows[: args.limit]
        print(json.dumps({"count": len(rows), "rows": [row.as_dict() for row in selected]}, ensure_ascii=False, indent=2))
        return

    if args.command == "extract" and args.extract_command == "contribution-flow":
        rows = parse_contribution_flow_rows(
            args.xlsx,
            scope_type=args.scope,
            include_total_rows=args.include_total_rows,
            template_code=args.template_code,
        )
        selected = rows if args.all else rows[: args.limit]
        print(json.dumps({"count": len(rows), "rows": [row.as_dict() for row in selected]}, ensure_ascii=False, indent=2))
        return

    if args.command == "load-summary":
        franchise_rows = parse_franchise_month_rows(args.xlsx, template_code=args.template_code)
        site_rows = parse_site_month_rows(args.xlsx, template_code=args.template_code)
        period_month = franchise_rows[0].period_month if franchise_rows else ""
        inspection = inspect_workbook(args.xlsx, template_code=args.template_code)
        structure_errors = validate_required_sheets(args.xlsx, template_code=args.template_code)
        validation_results = validate_summary_totals(inspection.overview, franchise_rows, site_rows)
        validation_errors = validation_results_to_import_errors(validation_results)
        import_errors = structure_errors + validation_errors
        file_id, job_id = create_import_job(
            args.database_url,
            workbook_path=args.xlsx,
            inspection=inspection,
            period_month=period_month,
            region_code=args.region_code,
            template_code=args.template_code,
        )
        save_validation_results(args.database_url, job_id=job_id, results=validation_results)
        save_import_errors(args.database_url, job_id=job_id, errors=import_errors)
        if import_errors:
            finish_import_job(
                args.database_url,
                file_id=file_id,
                job_id=job_id,
                status="failed",
                progress=100,
                message=f"Import blocked by {len(import_errors)} validation or structure errors",
            )
            print(
                json.dumps(
                    {
                        "file_id": file_id,
                        "job_id": job_id,
                        "status": "failed",
                        "error_count": len(import_errors),
                        "errors": [error.as_dict() for error in import_errors],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        try:
            franchise_count = load_franchise_month_rows(
                args.database_url,
                franchise_rows,
                region_code=args.region_code,
                region_name=args.region_name,
                replace_period=args.replace_period,
                file_id=file_id,
                template_code=args.template_code,
            )
            site_count = load_site_month_rows(
                args.database_url,
                site_rows,
                region_code=args.region_code,
                region_name=args.region_name,
                replace_period=args.replace_period,
                file_id=file_id,
                template_code=args.template_code,
            )
        except Exception as exc:
            save_import_errors(args.database_url, job_id=job_id, errors=[*import_errors, _exception_error(exc)])
            finish_import_job(
                args.database_url,
                file_id=file_id,
                job_id=job_id,
                status="failed",
                progress=100,
                message=str(exc),
            )
            raise
        finish_import_job(
            args.database_url,
            file_id=file_id,
            job_id=job_id,
            status="completed",
            progress=100,
            message=f"Loaded {len(franchise_rows)} franchise rows and {len(site_rows)} site rows",
        )
        passed = sum(1 for result in validation_results if result.passed)
        print(
            json.dumps(
                {
                    "file_id": file_id,
                    "job_id": job_id,
                    "franchise_rows": franchise_count,
                    "site_rows": site_count,
                    "validation_passed": passed,
                    "validation_failed": len(validation_results) - passed,
                    "error_count": len(import_errors),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "load-workbook":
        franchise_rows = parse_franchise_month_rows(args.xlsx, template_code=args.template_code)
        site_rows = parse_site_month_rows(args.xlsx, template_code=args.template_code)
        region_flow_rows = parse_contribution_flow_rows(
            args.xlsx,
            scope_type="region",
            region_code=args.region_code,
            template_code=args.template_code,
        )
        franchise_flow_rows = parse_contribution_flow_rows(
            args.xlsx,
            scope_type="franchise",
            region_code=args.region_code,
            template_code=args.template_code,
        )
        period_month = franchise_rows[0].period_month if franchise_rows else ""
        inspection = inspect_workbook(args.xlsx, template_code=args.template_code)
        structure_errors = validate_required_sheets(args.xlsx, template_code=args.template_code)
        validation_results = validate_summary_totals(inspection.overview, franchise_rows, site_rows)
        validation_errors = validation_results_to_import_errors(validation_results)
        import_errors = structure_errors + validation_errors
        file_id, job_id = create_import_job(
            args.database_url,
            workbook_path=args.xlsx,
            inspection=inspection,
            period_month=period_month,
            region_code=args.region_code,
            template_code=args.template_code,
        )
        save_validation_results(args.database_url, job_id=job_id, results=validation_results)
        save_import_errors(args.database_url, job_id=job_id, errors=import_errors)
        if import_errors:
            finish_import_job(
                args.database_url,
                file_id=file_id,
                job_id=job_id,
                status="failed",
                progress=100,
                message=f"Import blocked by {len(import_errors)} validation or structure errors",
            )
            print(
                json.dumps(
                    {
                        "file_id": file_id,
                        "job_id": job_id,
                        "status": "failed",
                        "error_count": len(import_errors),
                        "errors": [error.as_dict() for error in import_errors],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        try:
            franchise_count = load_franchise_month_rows(
                args.database_url,
                franchise_rows,
                region_code=args.region_code,
                region_name=args.region_name,
                replace_period=args.replace_period,
                file_id=file_id,
                template_code=args.template_code,
            )
            site_count = load_site_month_rows(
                args.database_url,
                site_rows,
                region_code=args.region_code,
                region_name=args.region_name,
                replace_period=args.replace_period,
                file_id=file_id,
                template_code=args.template_code,
            )
            region_flow_count = load_contribution_flow_rows(
                args.database_url,
                region_flow_rows,
                region_code=args.region_code,
                region_name=args.region_name,
                replace_period=args.replace_period,
                file_id=file_id,
                template_code=args.template_code,
            )
            franchise_flow_count = load_contribution_flow_rows(
                args.database_url,
                franchise_flow_rows,
                region_code=args.region_code,
                region_name=args.region_name,
                replace_period=args.replace_period,
                file_id=file_id,
                template_code=args.template_code,
            )
        except Exception as exc:
            save_import_errors(args.database_url, job_id=job_id, errors=[*import_errors, _exception_error(exc)])
            finish_import_job(
                args.database_url,
                file_id=file_id,
                job_id=job_id,
                status="failed",
                progress=100,
                message=str(exc),
            )
            raise
        finish_import_job(
            args.database_url,
            file_id=file_id,
            job_id=job_id,
            status="completed",
            progress=100,
            message=(
                f"Loaded {franchise_count} franchise rows, {site_count} site rows, "
                f"{region_flow_count} region flow rows, and {franchise_flow_count} franchise flow rows"
            ),
        )
        passed = sum(1 for result in validation_results if result.passed)
        print(
            json.dumps(
                {
                    "file_id": file_id,
                    "job_id": job_id,
                    "franchise_rows": franchise_count,
                    "site_rows": site_count,
                    "region_contribution_flow_rows": region_flow_count,
                    "franchise_contribution_flow_rows": franchise_flow_count,
                    "validation_passed": passed,
                    "validation_failed": len(validation_results) - passed,
                    "error_count": len(import_errors),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "load-contribution-flow":
        rows = parse_contribution_flow_rows(
            args.xlsx,
            scope_type=args.scope,
            region_code=args.region_code,
            template_code=args.template_code,
        )
        period_month = rows[0].period_month if rows else ""
        inspection = inspect_workbook(args.xlsx, template_code=args.template_code)
        file_id, job_id = create_import_job(
            args.database_url,
            workbook_path=args.xlsx,
            inspection=inspection,
            period_month=period_month,
            region_code=args.region_code,
            template_code=args.template_code,
        )
        try:
            count = load_contribution_flow_rows(
                args.database_url,
                rows,
                region_code=args.region_code,
                replace_period=args.replace_period,
                file_id=file_id,
                template_code=args.template_code,
            )
        except Exception as exc:
            save_import_errors(args.database_url, job_id=job_id, errors=[_exception_error(exc)])
            finish_import_job(
                args.database_url,
                file_id=file_id,
                job_id=job_id,
                status="failed",
                progress=100,
                message=str(exc),
            )
            raise
        finish_import_job(
            args.database_url,
            file_id=file_id,
            job_id=job_id,
            status="completed",
            progress=100,
            message=f"Loaded {count} contribution flow rows for {args.scope}",
        )
        print(
            json.dumps(
                {"file_id": file_id, "job_id": job_id, "contribution_flow_rows": count, "scope": args.scope},
                ensure_ascii=False,
                indent=2,
            )
        )
        return


if __name__ == "__main__":
    main()
