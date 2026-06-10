from __future__ import annotations

import socket
import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from fastapi import HTTPException

from .config import settings
from .schemas import (
    ContributionHeatmapCell,
    ContributionHeatmapResponse,
    ImportErrorItem,
    ImportErrorResponse,
    ImportJobHistoryItem,
    ImportJobResponse,
    ImportValidationResponse,
    ImportValidationResult,
    OverviewResponse,
    RankItem,
    SiteRankItem,
)

RANK_METRICS = {
    "total_contribution": "total_contribution",
    "outbound_contribution": "outbound_contribution",
    "inbound_contribution": "inbound_contribution",
    "deduction_total": "deduction_total",
    "outbound_tickets": "outbound_tickets",
}

SITE_RANK_METRICS = {
    "total_contribution": "total_contribution",
    "outbound_contribution": "outbound_contribution",
    "inbound_contribution": "inbound_contribution",
    "deduction_total": "deduction_total",
    "outbound_tickets": "outbound_tickets",
    "inbound_signed_tickets": "inbound_signed_tickets",
}

FLOW_METRICS = {
    "contribution_total": "contribution_total",
    "ticket_count": "ticket_count",
    "weight_total": "weight_total",
}


def _require_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=503, detail="psycopg is not installed") from exc
    return psycopg, dict_row


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.lower().startswith("sqlite:")


def _sqlite_path(database_url: str) -> str:
    repo_root = Path(__file__).resolve().parents[3]
    parsed = urlparse(database_url)
    if parsed.path in {"", "/:memory:"}:
        return ":memory:"
    path = unquote(parsed.path)
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    elif path.startswith("/"):
        path = path[1:]
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = repo_root / resolved
    return str(resolved)


def _translate_sql(sql: str) -> str:
    return sql.replace("%s", "?").replace("now()", "CURRENT_TIMESTAMP")


class _SqliteConnection:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        self._connection.close()

    def execute(self, sql: str, params=()):
        return self._connection.execute(_translate_sql(sql), params)


def _sqlite_schema_sql() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    return (repo_root / "database" / "migrations" / "001_init_sqlite.sql").read_text(encoding="utf-8")


def _as_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _connect():
    if _is_sqlite_url(settings.database_url):
        path = _sqlite_path(settings.database_url)
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma foreign_keys = on")
        exists = connection.execute(
            "select 1 from sqlite_master where type = 'table' and name = 'source_file'"
        ).fetchone()
        if not exists:
            connection.executescript(_sqlite_schema_sql())
            connection.commit()
        return _SqliteConnection(connection)

    psycopg, dict_row = _require_psycopg()
    try:
        parsed = urlparse(settings.database_url)
        if parsed.hostname:
            port = parsed.port or 5432
            with socket.create_connection(
                (parsed.hostname, port),
                timeout=settings.database_preflight_timeout,
            ):
                pass
        return psycopg.connect(
            settings.database_url,
            row_factory=dict_row,
            connect_timeout=settings.database_connect_timeout,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database is unavailable") from exc


def _franchise_tags(row: Any) -> list[str]:
    tags: list[str] = []
    if _as_float(row["total_contribution"]) < 0:
        tags.append("负贡献")
    if _as_float(row["inbound_contribution"]) < 0:
        tags.append("进港亏损")
    if _as_float(row["deduction_total"]) >= 50000:
        tags.append("扣款高风险")
    if _as_float(row["total_contribution"]) > 0:
        tags.append("正贡献")
    return tags


def _site_tags(row: Any) -> list[str]:
    tags: list[str] = []
    if _as_float(row["total_contribution"]) < 0:
        tags.append("负贡献")
    if _as_float(row["inbound_contribution"]) < 0:
        tags.append("进港亏损")
    if _as_float(row["deduction_total"]) >= 20000:
        tags.append("扣款关注")
    if _as_float(row["outbound_tickets"]) >= 5000:
        tags.append("高票量")
    if row["site_status"]:
        tags.append(str(row["site_status"]))
    return tags


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def check_database() -> dict[str, str]:
    with _connect() as conn:
        conn.execute("select 1").fetchone()
    return {"database": "ok"}


def get_overview(period_month: str, region_code: str) -> OverviewResponse:
    sql = """
        select
          f.period_month,
          f.region_code,
          count(distinct f.franchise_id) as franchise_count,
          coalesce(s.site_count, 0) as site_count,
          coalesce(sum(f.outbound_tickets), 0) as outbound_tickets,
          coalesce(sum(f.outbound_weight), 0) as outbound_weight,
          coalesce(sum(f.inbound_signed_tickets), 0) as inbound_signed_tickets,
          coalesce(sum(f.outbound_contribution), 0) as outbound_contribution,
          coalesce(sum(f.inbound_contribution), 0) as inbound_contribution,
          coalesce(sum(f.total_contribution), 0) as total_contribution,
          coalesce(sum(f.deduction_total), 0) as deduction_total
        from fact_franchise_month f
        left join (
          select period_month, region_code, count(distinct site_id) as site_count
          from fact_site_month
          where period_month = %s and region_code = %s
          group by period_month, region_code
        ) s on s.period_month = f.period_month and s.region_code = f.region_code
        where f.period_month = %s and f.region_code = %s
        group by f.period_month, f.region_code, s.site_count
    """
    with _connect() as conn:
        row = conn.execute(sql, (period_month, region_code, period_month, region_code)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="overview data not found")

    return OverviewResponse(
        period_month=str(row["period_month"]),
        region_code=str(row["region_code"]),
        franchise_count=int(row["franchise_count"] or 0),
        site_count=int(row["site_count"] or 0),
        outbound_tickets=_as_float(row["outbound_tickets"]),
        outbound_weight=_as_float(row["outbound_weight"]),
        inbound_signed_tickets=_as_float(row["inbound_signed_tickets"]),
        outbound_contribution=_as_float(row["outbound_contribution"]),
        inbound_contribution=_as_float(row["inbound_contribution"]),
        total_contribution=_as_float(row["total_contribution"]),
        deduction_total=_as_float(row["deduction_total"]),
    )


def get_franchise_rank(period_month: str, region_code: str, metric: str, direction: str, limit: int) -> list[RankItem]:
    order_column = RANK_METRICS.get(metric)
    if order_column is None:
        raise HTTPException(status_code=400, detail=f"unsupported metric: {metric}")
    if direction not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail=f"unsupported direction: {direction}")

    bounded_limit = max(1, min(limit, 100))
    sql = f"""
        select
          franchise_name as name,
          total_contribution,
          outbound_contribution,
          inbound_contribution,
          deduction_total,
          outbound_tickets,
          inbound_signed_tickets
        from fact_franchise_month
        where period_month = %s and region_code = %s
        order by {order_column} {direction} nulls last
        limit %s
    """
    with _connect() as conn:
        rows = conn.execute(sql, (period_month, region_code, bounded_limit)).fetchall()

    return [
        RankItem(
            name=str(row["name"]),
            total_contribution=_as_float(row["total_contribution"]),
            outbound_contribution=_as_float(row["outbound_contribution"]),
            inbound_contribution=_as_float(row["inbound_contribution"]),
            deduction_total=_as_float(row["deduction_total"]),
            outbound_tickets=_as_float(row["outbound_tickets"]),
            inbound_signed_tickets=_as_float(row["inbound_signed_tickets"]),
            tags=_franchise_tags(row),
        )
        for row in rows
    ]


def get_site_rank(period_month: str, region_code: str, metric: str, direction: str, limit: int) -> list[SiteRankItem]:
    order_column = SITE_RANK_METRICS.get(metric)
    if order_column is None:
        raise HTTPException(status_code=400, detail=f"unsupported metric: {metric}")
    if direction not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail=f"unsupported direction: {direction}")

    bounded_limit = max(1, min(limit, 100))
    sql = f"""
        select
          site_name as name,
          franchise_name,
          site_status,
          total_contribution,
          outbound_contribution,
          inbound_contribution,
          deduction_total,
          outbound_tickets,
          inbound_signed_tickets
        from fact_site_month
        where period_month = %s and region_code = %s
        order by {order_column} {direction} nulls last
        limit %s
    """
    with _connect() as conn:
        rows = conn.execute(sql, (period_month, region_code, bounded_limit)).fetchall()

    return [
        SiteRankItem(
            name=str(row["name"]),
            franchise_name=str(row["franchise_name"]),
            site_status=row["site_status"],
            total_contribution=_as_float(row["total_contribution"]),
            outbound_contribution=_as_float(row["outbound_contribution"]),
            inbound_contribution=_as_float(row["inbound_contribution"]),
            deduction_total=_as_float(row["deduction_total"]),
            outbound_tickets=_as_float(row["outbound_tickets"]),
            inbound_signed_tickets=_as_float(row["inbound_signed_tickets"]),
            tags=_site_tags(row),
        )
        for row in rows
    ]


def get_contribution_heatmap(
    period_month: str,
    region_code: str,
    scope_type: str,
    metric: str,
    province_limit: int,
) -> ContributionHeatmapResponse:
    metric_column = FLOW_METRICS.get(metric)
    if metric_column is None:
        raise HTTPException(status_code=400, detail=f"unsupported metric: {metric}")
    if scope_type not in {"region", "franchise"}:
        raise HTTPException(status_code=400, detail=f"unsupported scope_type: {scope_type}")

    bounded_limit = max(1, min(province_limit, 50))
    sql = f"""
        with province_rank as (
          select destination_province, sum(abs(coalesce({metric_column}, 0))) as metric_abs_total
          from fact_contribution_flow
          where period_month = %s
            and region_code = %s
            and scope_type = %s
            and destination_province is not null
          group by destination_province
          order by metric_abs_total desc
          limit %s
        ),
        flow_agg as (
          select
            destination_province,
            weight_band,
            coalesce(sum({metric_column}), 0) as value,
            coalesce(sum(ticket_count), 0) as ticket_count,
            coalesce(sum(weight_total), 0) as weight_total
          from fact_contribution_flow
          where period_month = %s
            and region_code = %s
            and scope_type = %s
          group by destination_province, weight_band
        )
        select
          pr.destination_province,
          wb.weight_band,
          coalesce(f.value, 0) as value,
          coalesce(f.ticket_count, 0) as ticket_count,
          coalesce(f.weight_total, 0) as weight_total,
          wb.sort_order
        from province_rank pr
        cross join dim_weight_band wb
        left join flow_agg f
          on f.destination_province = pr.destination_province
         and f.weight_band = wb.weight_band
        order by pr.metric_abs_total desc, wb.sort_order, wb.weight_band
    """
    with _connect() as conn:
        rows = conn.execute(
            sql,
            (
                period_month,
                region_code,
                scope_type,
                bounded_limit,
                period_month,
                region_code,
                scope_type,
            ),
        ).fetchall()

    provinces: list[str] = []
    weight_bands: list[str] = []
    cells: list[ContributionHeatmapCell] = []

    for row in rows:
        province = str(row["destination_province"])
        weight_band = str(row["weight_band"])
        if province not in provinces:
            provinces.append(province)
        if weight_band not in weight_bands:
            weight_bands.append(weight_band)
        cells.append(
            ContributionHeatmapCell(
                destination_province=province,
                weight_band=weight_band,
                value=_as_float(row["value"]),
                ticket_count=_as_float(row["ticket_count"]),
                weight_total=_as_float(row["weight_total"]),
            )
        )

    return ContributionHeatmapResponse(
        period_month=period_month,
        region_code=region_code,
        scope_type=scope_type,
        metric=metric,
        provinces=provinces,
        weight_bands=weight_bands,
        cells=cells,
    )


def get_import_job(job_id: int) -> ImportJobResponse:
    sql = """
        select id as job_id, status, progress, message
        from import_job
        where id = %s
    """
    with _connect() as conn:
        row = conn.execute(sql, (job_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="import job not found")

    return ImportJobResponse(
        job_id=int(row["job_id"]),
        status=str(row["status"]),
        progress=int(row["progress"]),
        message=row["message"],
    )


def get_latest_import_job(period_month: str | None, region_code: str | None) -> ImportJobResponse:
    filters = []
    params: list[str] = []
    if period_month:
        filters.append("sf.period_month = %s")
        params.append(period_month)
    if region_code:
        filters.append("sf.region_code = %s")
        params.append(region_code)

    where_clause = f"where {' and '.join(filters)}" if filters else ""
    sql = f"""
        select ij.id as job_id, ij.status, ij.progress, ij.message
        from import_job ij
        join source_file sf on sf.id = ij.file_id
        {where_clause}
        order by coalesce(ij.started_at, ij.created_at) desc, ij.id desc
        limit 1
    """
    with _connect() as conn:
        row = conn.execute(sql, tuple(params)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="import job not found")

    return ImportJobResponse(
        job_id=int(row["job_id"]),
        status=str(row["status"]),
        progress=int(row["progress"]),
        message=row["message"],
    )


def list_import_jobs(period_month: str | None, region_code: str | None, limit: int) -> list[ImportJobHistoryItem]:
    filters = []
    params: list[Any] = []
    if period_month:
        filters.append("sf.period_month = %s")
        params.append(period_month)
    if region_code:
        filters.append("sf.region_code = %s")
        params.append(region_code)

    bounded_limit = max(1, min(limit, 100))
    params.append(bounded_limit)
    where_clause = f"where {' and '.join(filters)}" if filters else ""
    sql = f"""
        select
          ij.id as job_id,
          sf.file_name,
          sf.period_month,
          sf.region_code,
          sf.template_code,
          ij.status,
          ij.progress,
          ij.created_at,
          ij.started_at,
          ij.finished_at,
          ij.message
        from import_job ij
        join source_file sf on sf.id = ij.file_id
        {where_clause}
        order by coalesce(ij.started_at, ij.created_at) desc, ij.id desc
        limit %s
    """
    with _connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()

    return [
        ImportJobHistoryItem(
            job_id=int(row["job_id"]),
            file_name=str(row["file_name"]),
            period_month=str(row["period_month"]),
            region_code=str(row["region_code"]),
            template_code=row["template_code"],
            status=str(row["status"]),
            progress=int(row["progress"]),
            created_at=_isoformat(row["created_at"]) or "",
            started_at=_isoformat(row["started_at"]),
            finished_at=_isoformat(row["finished_at"]),
            message=row["message"],
        )
        for row in rows
    ]


def get_import_validation_results(job_id: int) -> ImportValidationResponse:
    with _connect() as conn:
        job_exists = conn.execute("select 1 from import_job where id = %s", (job_id,)).fetchone()
        if not job_exists:
            raise HTTPException(status_code=404, detail="import job not found")

        rows = conn.execute(
            """
            select
              rule_code, metric_code, expected_value, actual_value, diff_value,
              tolerance, passed, severity, message
            from import_validation_result
            where job_id = %s
            order by passed asc, severity desc, metric_code
            """,
            (job_id,),
        ).fetchall()

    results = [
        ImportValidationResult(
            rule_code=str(row["rule_code"]),
            metric_code=str(row["metric_code"]),
            expected_value=None if row["expected_value"] is None else _as_float(row["expected_value"]),
            actual_value=None if row["actual_value"] is None else _as_float(row["actual_value"]),
            diff_value=None if row["diff_value"] is None else _as_float(row["diff_value"]),
            tolerance=None if row["tolerance"] is None else _as_float(row["tolerance"]),
            passed=bool(row["passed"]),
            severity=str(row["severity"]),
            message=row["message"],
        )
        for row in rows
    ]
    passed = sum(1 for result in results if result.passed)
    return ImportValidationResponse(
        job_id=job_id,
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def get_import_errors(job_id: int) -> ImportErrorResponse:
    with _connect() as conn:
        job_exists = conn.execute("select 1 from import_job where id = %s", (job_id,)).fetchone()
        if not job_exists:
            raise HTTPException(status_code=404, detail="import job not found")

        rows = conn.execute(
            """
            select severity, sheet_name, row_number, column_name, error_code, error_message
            from import_error
            where job_id = %s
            order by
              case severity
                when 'error' then 1
                when 'warning' then 2
                else 3
              end,
              sheet_name nulls last,
              row_number nulls last,
              error_code
            """,
            (job_id,),
        ).fetchall()

    errors = [
        ImportErrorItem(
            severity=str(row["severity"]),
            sheet_name=row["sheet_name"],
            row_number=row["row_number"],
            column_name=row["column_name"],
            error_code=str(row["error_code"]),
            error_message=str(row["error_message"]),
        )
        for row in rows
    ]
    return ImportErrorResponse(job_id=job_id, error_count=len(errors), errors=errors)
