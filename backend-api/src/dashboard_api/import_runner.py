from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from .config import settings
from .schemas import UploadImportResponse

SAFE_FILENAME_RE = re.compile(r"[^0-9A-Za-z._\-\u4e00-\u9fff]+")


def _safe_filename(filename: str) -> str:
    cleaned = SAFE_FILENAME_RE.sub("_", Path(filename).name).strip("._")
    return cleaned or "workbook.xlsx"


def _require_excel(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".xlsx", ".xlsm"}:
        raise HTTPException(status_code=400, detail="only .xlsx or .xlsm workbooks are supported")


async def save_upload(upload: UploadFile) -> Path:
    if not upload.filename:
        raise HTTPException(status_code=400, detail="missing upload filename")
    _require_excel(upload.filename)

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    target = settings.upload_dir / f"{int(time.time())}_{_safe_filename(upload.filename)}"
    with target.open("wb") as handle:
        while chunk := await upload.read(1024 * 1024):
            handle.write(chunk)
    return target


def run_workbook_import(
    workbook_path: Path,
    *,
    region_code: str,
    region_name: str,
    template_code: str,
    replace_period: bool,
) -> UploadImportResponse:
    if not settings.import_service_src.exists():
        raise HTTPException(status_code=503, detail="import service source path is unavailable")

    command = [
        settings.import_python,
        "-m",
        "import_service.cli",
        "load-workbook",
        str(workbook_path),
        "--database-url",
        settings.database_url,
        "--region-code",
        region_code,
        "--region-name",
        region_name,
        "--template-code",
        template_code,
    ]
    if replace_period:
        command.append("--replace-period")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(settings.import_service_src)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"failed to start import service: {exc}") from exc

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    parsed: dict[str, Any] = {}
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = {"stdout": stdout}

    if completed.returncode != 0:
        detail = stderr or stdout or "import service failed"
        raise HTTPException(status_code=500, detail=detail)

    job_id = parsed.get("job_id")
    status = str(parsed.get("status") or "completed")
    return UploadImportResponse(
        job_id=int(job_id) if job_id is not None else None,
        status=status,
        file_name=workbook_path.name,
        message=_build_message(parsed),
        summary=parsed,
    )


def _build_message(summary: dict[str, Any]) -> str:
    if "error_count" in summary and summary.get("status") == "failed":
        return f"Import failed with {summary.get('error_count')} errors"
    parts = []
    for key, label in [
        ("franchise_rows", "franchise rows"),
        ("site_rows", "site rows"),
        ("region_contribution_flow_rows", "region flow rows"),
        ("franchise_contribution_flow_rows", "franchise flow rows"),
    ]:
        if key in summary:
            parts.append(f"{summary[key]} {label}")
    return "Loaded " + ", ".join(parts) if parts else "Import completed"
