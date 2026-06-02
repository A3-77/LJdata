from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .workbook import inspect_workbook


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="dashboard-import")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect workbook structure and overview checks")
    inspect_parser.add_argument("xlsx", type=Path)

    args = parser.parse_args()

    if args.command == "inspect":
        result = inspect_workbook(args.xlsx)
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
