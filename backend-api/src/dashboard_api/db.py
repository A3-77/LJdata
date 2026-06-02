from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import HTTPException

from .config import settings
from .schemas import (
    ContributionHeatmapCell,
    ContributionHeatmapResponse,
    ImportErrorItem,
    ImportErrorResponse,
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
          inbound_signed_tickets,
          array_remove(array[
            case when total_contribution < 0 then '负贡献' end,
            case when inbound_contribution < 0 then '进港亏损' end,
            case when deduction_total >= 20000 then '扣款关注' end,
            case when outbound_tickets >= 5000 then '高票量' end,
            case when site_status is not null and site_status <> '' then site_status end
          ]::text[], null::text) as tags
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
            tags=list(row["tags"] or []),
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
