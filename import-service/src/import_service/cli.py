from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .db import load_franchise_month_rows, load_site_month_rows
from .workbook import inspect_workbook, parse_franchise_month_rows, parse_site_month_rows


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="dashboard-import")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect workbook structure and overview checks")
    inspect_parser.add_argument("xlsx", type=Path)

    extract_parser = subparsers.add_parser("extract", help="Extract normalized rows from workbook")
    extract_subparsers = extract_parser.add_subparsers(dest="extract_command", required=True)

    franchise_parser = extract_subparsers.add_parser("franchise-summary", help="Extract 总表-加盟商 rows")
    franchise_parser.add_argument("xlsx", type=Path)
    franchise_parser.add_argument("--limit", type=int, default=5)
    franchise_parser.add_argument("--all", action="store_true", help="Print all rows")

    site_parser = extract_subparsers.add_parser("site-summary", help="Extract 总表-网点 rows")
    site_parser.add_argument("xlsx", type=Path)
    site_parser.add_argument("--limit", type=int, default=5)
    site_parser.add_argument("--all", action="store_true", help="Print all rows")

    load_parser = subparsers.add_parser("load-summary", help="Load franchise and site summaries into PostgreSQL")
    load_parser.add_argument("xlsx", type=Path)
    load_parser.add_argument("--database-url", required=True)
    load_parser.add_argument("--region-code", default="LN")
    load_parser.add_argument("--region-name", default="辽宁区域")
    load_parser.add_argument("--replace-period", action="store_true")

    args = parser.parse_args()

    if args.command == "inspect":
        result = inspect_workbook(args.xlsx)
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        return

    if args.command == "extract" and args.extract_command == "franchise-summary":
        rows = parse_franchise_month_rows(args.xlsx)
        selected = rows if args.all else rows[: args.limit]
        print(json.dumps({"count": len(rows), "rows": [row.as_dict() for row in selected]}, ensure_ascii=False, indent=2))
        return

    if args.command == "extract" and args.extract_command == "site-summary":
        rows = parse_site_month_rows(args.xlsx)
        selected = rows if args.all else rows[: args.limit]
        print(json.dumps({"count": len(rows), "rows": [row.as_dict() for row in selected]}, ensure_ascii=False, indent=2))
        return

    if args.command == "load-summary":
        franchise_rows = parse_franchise_month_rows(args.xlsx)
        site_rows = parse_site_month_rows(args.xlsx)
        franchise_count = load_franchise_month_rows(
            args.database_url,
            franchise_rows,
            region_code=args.region_code,
            region_name=args.region_name,
            replace_period=args.replace_period,
        )
        site_count = load_site_month_rows(
            args.database_url,
            site_rows,
            region_code=args.region_code,
            region_name=args.region_name,
            replace_period=args.replace_period,
        )
        print(json.dumps({"franchise_rows": franchise_count, "site_rows": site_count}, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
