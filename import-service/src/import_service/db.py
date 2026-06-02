from __future__ import annotations

from collections.abc import Iterable

from .models import FranchiseMonthRow, SiteMonthRow


def _require_psycopg():
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for database loading. Install import-service dependencies first.") from exc
    return psycopg


def _period_parts(period_month: str) -> tuple[int, int]:
    return int(period_month[:4]), int(period_month[4:6])


def ensure_month(cursor, period_month: str) -> None:
    year, month = _period_parts(period_month)
    cursor.execute(
        """
        insert into dim_month(period_month, year, month)
        values (%s, %s, %s)
        on conflict (period_month) do nothing
        """,
        (period_month, year, month),
    )


def ensure_region(cursor, region_code: str, region_name: str) -> None:
    cursor.execute(
        """
        insert into dim_region(region_code, region_name)
        values (%s, %s)
        on conflict (region_code) do update set region_name = excluded.region_name
        """,
        (region_code, region_name),
    )


def upsert_franchise(cursor, franchise_name: str, region_code: str) -> int:
    cursor.execute(
        """
        insert into dim_franchise(franchise_name, region_code)
        values (%s, %s)
        on conflict (region_code, franchise_name) do update
        set updated_at = now()
        returning id
        """,
        (franchise_name, region_code),
    )
    return int(cursor.fetchone()[0])


def upsert_site(cursor, site_name: str, franchise_id: int, status: str | None) -> int:
    cursor.execute(
        """
        insert into dim_site(site_name, franchise_id, status)
        values (%s, %s, %s)
        on conflict (site_name, franchise_id) do update
        set status = excluded.status,
            updated_at = now()
        returning id
        """,
        (site_name, franchise_id, status),
    )
    return int(cursor.fetchone()[0])


def load_franchise_month_rows(
    database_url: str,
    rows: Iterable[FranchiseMonthRow],
    *,
    region_code: str = "LN",
    region_name: str = "辽宁区域",
    replace_period: bool = False,
) -> int:
    psycopg = _require_psycopg()
    rows = list(rows)
    if not rows:
        return 0

    period_month = rows[0].period_month
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            ensure_region(cursor, region_code, region_name)
            ensure_month(cursor, period_month)

            if replace_period:
                cursor.execute(
                    "delete from fact_franchise_month where period_month = %s and region_code = %s",
                    (period_month, region_code),
                )

            for row in rows:
                franchise_id = upsert_franchise(cursor, row.franchise_name, region_code)
                cursor.execute(
                    """
                    insert into fact_franchise_month (
                      period_month, region_code, franchise_id, franchise_name,
                      daily_over_5000_flag, outbound_tickets, outbound_weight, outbound_avg_weight,
                      waybill_fee, transfer_fee, warehouse_fee, operation_fee, dispatch_fee,
                      one_price_rebate, outbound_contribution, outbound_unit_contribution,
                      outbound_kg_contribution, inbound_signed_tickets, inbound_weight,
                      inbound_dispatch_income, inbound_dispatch_cost, deduction_total,
                      inbound_contribution, total_contribution, outbound_pass_contribution,
                      inbound_pass_contribution
                    )
                    values (
                      %s, %s, %s, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s
                    )
                    """,
                    (
                        row.period_month,
                        region_code,
                        franchise_id,
                        row.franchise_name,
                        row.daily_over_5000_flag,
                        row.outbound_tickets,
                        row.outbound_weight,
                        row.outbound_avg_weight,
                        row.waybill_fee,
                        row.transfer_fee,
                        row.warehouse_fee,
                        row.operation_fee,
                        row.dispatch_fee,
                        row.one_price_rebate,
                        row.outbound_contribution,
                        row.outbound_unit_contribution,
                        row.outbound_kg_contribution,
                        row.inbound_signed_tickets,
                        row.inbound_weight,
                        row.inbound_dispatch_income,
                        row.inbound_dispatch_cost,
                        row.deduction_total,
                        row.inbound_contribution,
                        row.total_contribution,
                        row.outbound_pass_contribution,
                        row.inbound_pass_contribution,
                    ),
                )
        conn.commit()
    return len(rows)


def load_site_month_rows(
    database_url: str,
    rows: Iterable[SiteMonthRow],
    *,
    region_code: str = "LN",
    region_name: str = "辽宁区域",
    replace_period: bool = False,
) -> int:
    psycopg = _require_psycopg()
    rows = list(rows)
    if not rows:
        return 0

    period_month = rows[0].period_month
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            ensure_region(cursor, region_code, region_name)
            ensure_month(cursor, period_month)

            if replace_period:
                cursor.execute(
                    "delete from fact_site_month where period_month = %s and region_code = %s",
                    (period_month, region_code),
                )

            for row in rows:
                franchise_id = upsert_franchise(cursor, row.franchise_name, region_code)
                site_id = upsert_site(cursor, row.site_name, franchise_id, row.site_status)
                cursor.execute(
                    """
                    insert into fact_site_month (
                      period_month, region_code, franchise_id, franchise_name,
                      site_id, site_name, site_status, daily_over_5000_flag,
                      outbound_tickets, outbound_weight, outbound_contribution,
                      inbound_signed_tickets, inbound_contribution, deduction_total,
                      total_contribution
                    )
                    values (
                      %s, %s, %s, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s
                    )
                    """,
                    (
                        row.period_month,
                        region_code,
                        franchise_id,
                        row.franchise_name,
                        site_id,
                        row.site_name,
                        row.site_status,
                        row.daily_over_5000_flag,
                        row.outbound_tickets,
                        row.outbound_weight,
                        row.outbound_contribution,
                        row.inbound_signed_tickets,
                        row.inbound_contribution,
                        row.deduction_total,
                        row.total_contribution,
                    ),
                )
        conn.commit()
    return len(rows)
