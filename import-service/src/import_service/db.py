from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

from .models import ContributionFlowRow, FranchiseMonthRow, SiteMonthRow, ValidationResult, WorkbookInspection

WEIGHT_BANDS = ["0.3", "0.5", "1", "2", "3.2", "4", "5.2", "6", "7", "8", "9", "10.3", "＞10.3"]


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


def ensure_weight_bands(cursor) -> None:
    for index, weight_band in enumerate(WEIGHT_BANDS, start=1):
        cursor.execute(
            """
            insert into dim_weight_band(weight_band, sort_order, display_name)
            values (%s, %s, %s)
            on conflict (weight_band) do update
            set sort_order = excluded.sort_order,
                display_name = excluded.display_name
            """,
            (weight_band, index, weight_band),
        )


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_import_job(
    database_url: str,
    *,
    workbook_path: str | Path,
    inspection: WorkbookInspection,
    period_month: str,
    region_code: str = "LN",
    template_code: str = "franchise_contribution_v1",
) -> tuple[int, int]:
    psycopg = _require_psycopg()
    source = Path(workbook_path)
    file_hash = file_sha256(source)

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into source_file (
                  file_name, file_hash, file_path, region_code, period_month,
                  template_code, import_status
                )
                values (%s, %s, %s, %s, %s, %s, 'running')
                on conflict (file_hash) do update
                set file_name = excluded.file_name,
                    file_path = excluded.file_path,
                    region_code = excluded.region_code,
                    period_month = excluded.period_month,
                    template_code = excluded.template_code,
                    import_status = 'running'
                returning id
                """,
                (source.name, file_hash, str(source), region_code, period_month, template_code),
            )
            file_id = int(cursor.fetchone()[0])

            cursor.execute("delete from source_sheet where file_id = %s", (file_id,))
            for sheet in inspection.sheets:
                cursor.execute(
                    """
                    insert into source_sheet (
                      file_id, sheet_name, standard_sheet_code, max_row, max_col,
                      header_start_row, header_end_row, data_start_row, total_row
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        file_id,
                        sheet.name,
                        sheet.standard_sheet_code,
                        sheet.max_row,
                        sheet.max_col,
                        sheet.header_start_row,
                        sheet.header_end_row,
                        sheet.data_start_row,
                        sheet.total_row,
                    ),
                )

            cursor.execute(
                """
                insert into import_job(file_id, status, progress, started_at, message)
                values (%s, 'running', 5, now(), 'Import started')
                returning id
                """,
                (file_id,),
            )
            job_id = int(cursor.fetchone()[0])
        conn.commit()
    return file_id, job_id


def finish_import_job(
    database_url: str,
    *,
    file_id: int,
    job_id: int,
    status: str,
    progress: int,
    message: str,
) -> None:
    psycopg = _require_psycopg()
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                update import_job
                set status = %s,
                    progress = %s,
                    finished_at = now(),
                    message = %s
                where id = %s
                """,
                (status, progress, message, job_id),
            )
            cursor.execute(
                """
                update source_file
                set import_status = %s
                where id = %s
                """,
                (status, file_id),
            )
        conn.commit()


def save_validation_results(database_url: str, *, job_id: int, results: Iterable[ValidationResult]) -> int:
    psycopg = _require_psycopg()
    results = list(results)
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("delete from import_validation_result where job_id = %s", (job_id,))
            for result in results:
                cursor.execute(
                    """
                    insert into import_validation_result (
                      job_id, rule_code, metric_code, expected_value, actual_value,
                      diff_value, tolerance, passed, severity, message
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        job_id,
                        result.rule_code,
                        result.metric_code,
                        result.expected_value,
                        result.actual_value,
                        result.diff_value,
                        result.tolerance,
                        result.passed,
                        result.severity,
                        result.message,
                    ),
                )
        conn.commit()
    return len(results)


def load_franchise_month_rows(
    database_url: str,
    rows: Iterable[FranchiseMonthRow],
    *,
    region_code: str = "LN",
    region_name: str = "辽宁区域",
    replace_period: bool = False,
    file_id: int | None = None,
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
            ensure_weight_bands(cursor)

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
                      file_id, period_month, region_code, franchise_id, franchise_name,
                      daily_over_5000_flag, outbound_tickets, outbound_weight, outbound_avg_weight,
                      waybill_fee, transfer_fee, warehouse_fee, operation_fee, dispatch_fee,
                      one_price_rebate, outbound_contribution, outbound_unit_contribution,
                      outbound_kg_contribution, inbound_signed_tickets, inbound_weight,
                      inbound_dispatch_income, inbound_dispatch_cost, deduction_total,
                      inbound_contribution, total_contribution, outbound_pass_contribution,
                      inbound_pass_contribution
                    )
                    values (
                      %s, %s, %s, %s, %s,
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
                        file_id,
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
    file_id: int | None = None,
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
            ensure_weight_bands(cursor)

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
                      file_id, period_month, region_code, franchise_id, franchise_name,
                      site_id, site_name, site_status, daily_over_5000_flag,
                      outbound_tickets, outbound_weight, outbound_contribution,
                      inbound_signed_tickets, inbound_contribution, deduction_total,
                      total_contribution
                    )
                    values (
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s
                    )
                    """,
                    (
                        file_id,
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


def load_contribution_flow_rows(
    database_url: str,
    rows: Iterable[ContributionFlowRow],
    *,
    region_code: str = "LN",
    region_name: str = "辽宁区域",
    replace_period: bool = False,
    file_id: int | None = None,
) -> int:
    psycopg = _require_psycopg()
    rows = list(rows)
    if not rows:
        return 0

    period_month = rows[0].period_month
    scope_type = rows[0].scope_type

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            ensure_region(cursor, region_code, region_name)
            ensure_month(cursor, period_month)
            ensure_weight_bands(cursor)

            if replace_period:
                cursor.execute(
                    "delete from fact_contribution_flow where period_month = %s and scope_type = %s",
                    (period_month, scope_type),
                )

            for row in rows:
                franchise_id = None
                if row.scope_type == "franchise" and row.franchise_name:
                    franchise_id = upsert_franchise(cursor, row.franchise_name, region_code)

                cursor.execute(
                    """
                    insert into fact_contribution_flow (
                      file_id, period_month, scope_type, region_code, franchise_id, franchise_name,
                      destination_province, weight_band, ticket_count, ticket_share,
                      weight_total, four_fee_total, settlement_price, dispatch_fee,
                      contribution_total, unit_four_fee, unit_settlement_price,
                      unit_dispatch_fee, unit_contribution, kg_contribution
                    )
                    values (
                      %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s
                    )
                    """,
                    (
                        file_id,
                        row.period_month,
                        row.scope_type,
                        row.region_code or region_code,
                        franchise_id,
                        row.franchise_name,
                        row.destination_province,
                        row.weight_band,
                        row.ticket_count,
                        row.ticket_share,
                        row.weight_total,
                        row.four_fee_total,
                        row.settlement_price,
                        row.dispatch_fee,
                        row.contribution_total,
                        row.unit_four_fee,
                        row.unit_settlement_price,
                        row.unit_dispatch_fee,
                        row.unit_contribution,
                        row.kg_contribution,
                    ),
                )
        conn.commit()
    return len(rows)
