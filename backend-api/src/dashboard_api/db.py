from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import HTTPException

from .config import settings
from .schemas import ImportJobResponse, OverviewResponse, RankItem

RANK_METRICS = {
    "total_contribution": "total_contribution",
    "outbound_contribution": "outbound_contribution",
    "inbound_contribution": "inbound_contribution",
    "deduction_total": "deduction_total",
    "outbound_tickets": "outbound_tickets",
}


def _require_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=503, detail="psycopg is not installed") from exc
    return psycopg, dict_row


def _as_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _connect():
    psycopg, dict_row = _require_psycopg()
    try:
        return psycopg.connect(settings.database_url, row_factory=dict_row)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database is unavailable") from exc


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
          array_remove(array[
            case when total_contribution < 0 then '负贡献' end,
            case when inbound_contribution < 0 then '进港亏损' end,
            case when deduction_total >= 50000 then '扣款高风险' end,
            case when total_contribution > 0 then '正贡献' end
          ]::text[], null::text) as tags
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
            tags=list(row["tags"] or []),
        )
        for row in rows
    ]


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
