from __future__ import annotations

import sys
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Iterable

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
IMPORT_SERVICE_SRC = ROOT / "import-service" / "src"
if str(IMPORT_SERVICE_SRC) not in sys.path:
    sys.path.insert(0, str(IMPORT_SERVICE_SRC))

from import_service.validation import validate_summary_totals  # noqa: E402
from import_service.workbook import (  # noqa: E402
    inspect_workbook,
    parse_contribution_flow_rows,
    parse_franchise_month_rows,
    parse_site_month_rows,
)


TEMPLATE_CODE = "franchise_contribution_v1"
WEIGHT_BAND_ORDER = ["0.3", "0.5", "1", "2", "3.2", "4", "5.2", "6", "7", "8", "9", "10.3", "＞10.3"]

FIELD_LABELS = {
    "period_month": "月份",
    "franchise_name": "加盟商",
    "site_name": "网点",
    "site_status": "网点状态",
    "daily_over_5000_flag": "日均超 5000",
    "destination_province": "目的省份",
    "weight_band": "公斤段",
    "franchise_count": "加盟商数",
    "site_count": "网点数",
    "outbound_tickets": "出港票量",
    "outbound_weight": "出港重量",
    "outbound_avg_weight": "出港均重",
    "inbound_signed_tickets": "进港签收量",
    "inbound_weight": "进港重量",
    "waybill_fee": "面单费",
    "transfer_fee": "中转费",
    "warehouse_fee": "仓储费",
    "operation_fee": "操作费",
    "dispatch_fee": "派费",
    "one_price_rebate": "一口价返利",
    "outbound_contribution": "出港总贡献",
    "outbound_unit_contribution": "出港单票贡献",
    "outbound_kg_contribution": "出港公斤贡献",
    "inbound_dispatch_income": "进港派费收入",
    "inbound_dispatch_cost": "进港派费成本",
    "inbound_contribution": "进港总贡献",
    "total_contribution": "总贡献",
    "deduction_total": "扣款小计",
    "outbound_pass_contribution": "出港票均贡献",
    "inbound_pass_contribution": "进港票均贡献",
    "ticket_count": "票量",
    "ticket_share": "票量占比",
    "weight_total": "重量",
    "four_fee_total": "四费合计",
    "settlement_price": "结算价",
    "contribution_total": "贡献",
    "unit_four_fee": "单票四费",
    "unit_settlement_price": "单票结算价",
    "unit_dispatch_fee": "单票派费",
    "unit_contribution": "单票贡献",
    "kg_contribution": "公斤贡献",
    "metric_code": "校验指标",
    "passed": "是否通过",
    "expected_value": "源表值",
    "actual_value": "解析值",
    "diff_value": "差异",
    "tolerance": "容差",
    "message": "说明",
}

AMOUNT_FIELDS = {
    "waybill_fee",
    "transfer_fee",
    "warehouse_fee",
    "operation_fee",
    "dispatch_fee",
    "one_price_rebate",
    "outbound_contribution",
    "inbound_dispatch_income",
    "inbound_dispatch_cost",
    "inbound_contribution",
    "total_contribution",
    "deduction_total",
    "four_fee_total",
    "settlement_price",
    "contribution_total",
}
COUNT_FIELDS = {"outbound_tickets", "inbound_signed_tickets", "ticket_count"}
WEIGHT_FIELDS = {"outbound_weight", "inbound_weight", "weight_total"}
RATE_FIELDS = {"ticket_share"}
UNIT_FIELDS = {
    "outbound_avg_weight",
    "outbound_unit_contribution",
    "outbound_kg_contribution",
    "outbound_pass_contribution",
    "inbound_pass_contribution",
    "unit_four_fee",
    "unit_settlement_price",
    "unit_dispatch_fee",
    "unit_contribution",
    "kg_contribution",
}


def number(value: float | int | None) -> str:
    return "-" if value is None else f"{value:,.0f}"


def money_wan(value: float | int | None) -> str:
    return "-" if value is None else f"{value / 10000:,.2f} 万元"


def count_wan(value: float | int | None) -> str:
    return "-" if value is None else f"{value / 10000:,.2f} 万"


def to_dataframe(rows: list[object]) -> pd.DataFrame:
    return pd.DataFrame([row.as_dict() for row in rows])


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def business_table(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    output = pd.DataFrame(index=df.index)
    for column in columns:
        if column not in df.columns:
            continue
        label = FIELD_LABELS.get(column, column)
        if column in AMOUNT_FIELDS:
            output[f"{label}（万元）"] = numeric(df[column]) / 10000
        elif column in COUNT_FIELDS:
            output[f"{label}（万票）"] = numeric(df[column]) / 10000
        elif column in WEIGHT_FIELDS:
            output[f"{label}（万公斤）"] = numeric(df[column]) / 10000
        elif column in RATE_FIELDS:
            output[f"{label}（%）"] = numeric(df[column]) * 100
        elif column == "daily_over_5000_flag":
            output[label] = df[column].map({True: "是", False: "否"}).fillna("-")
        elif column == "passed":
            output[label] = df[column].map({True: "通过", False: "失败"}).fillna("-")
        else:
            output[label] = df[column]
    return output.reset_index(drop=True)


def dataframe_config(df: pd.DataFrame) -> dict[str, object]:
    config: dict[str, object] = {}
    for column in df.columns:
        if "万元" in column or "万票" in column or "万公斤" in column or column.endswith("（%）"):
            config[column] = st.column_config.NumberColumn(column, format="%.2f")
    return config


def show_business_table(df: pd.DataFrame, columns: Iterable[str], height: int | None = None) -> None:
    display = business_table(df, columns)
    st.dataframe(
        display,
        column_config=dataframe_config(display),
        hide_index=True,
        height=height,
        width="stretch",
    )


def render_rank_bar(
    df: pd.DataFrame,
    name_col: str,
    metric_col: str,
    title: str,
    *,
    limit: int = 10,
    ascending: bool = False,
) -> None:
    if df.empty or name_col not in df.columns or metric_col not in df.columns:
        st.warning("当前筛选下没有可展示的排行数据。")
        return

    chart_df = df[[name_col, metric_col]].copy()
    chart_df[metric_col] = numeric(chart_df[metric_col])
    chart_df = chart_df.sort_values(metric_col, ascending=ascending).head(limit)
    chart_df["name_label"] = chart_df[name_col].astype(str)
    chart_df["value_wan"] = chart_df[metric_col] / 10000
    sort_order = chart_df["name_label"].tolist()

    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X("value_wan:Q", title="总贡献（万元）", axis=alt.Axis(format=",.0f"), scale=alt.Scale(zero=True)),
            y=alt.Y("name_label:N", sort=sort_order, title=None, axis=alt.Axis(labelLimit=280)),
            color=alt.condition(
                "datum.value_wan >= 0",
                alt.value("#2f7d57"),
                alt.value("#c2413d"),
            ),
            tooltip=[
                alt.Tooltip("name_label:N", title=FIELD_LABELS.get(name_col, name_col)),
                alt.Tooltip("value_wan:Q", title="总贡献（万元）", format=",.2f"),
            ],
        )
        .properties(title=title, height=max(260, len(chart_df) * 30))
    )
    st.altair_chart(chart, width="stretch")


def render_heatmap(flow_df: pd.DataFrame) -> None:
    if flow_df.empty:
        st.warning("未解析到区域流向数据。")
        return

    flow = flow_df.copy()
    flow["contribution_wan"] = numeric(flow["contribution_total"]) / 10000
    flow["ticket_count_wan"] = numeric(flow["ticket_count"]) / 10000
    flow["weight_total_wan"] = numeric(flow["weight_total"]) / 10000

    top_provinces = (
        flow.groupby("destination_province")["contribution_wan"]
        .sum()
        .abs()
        .sort_values(ascending=False)
        .head(20)
        .index.tolist()
    )
    heatmap_df = flow[flow["destination_province"].isin(top_provinces)].copy()
    heatmap_df["weight_band"] = pd.Categorical(
        heatmap_df["weight_band"],
        categories=[band for band in WEIGHT_BAND_ORDER if band in set(heatmap_df["weight_band"])],
        ordered=True,
    )
    heatmap_df = heatmap_df.sort_values(["destination_province", "weight_band"])

    chart = (
        alt.Chart(heatmap_df)
        .mark_rect()
        .encode(
            x=alt.X("weight_band:N", sort=WEIGHT_BAND_ORDER, title="公斤段"),
            y=alt.Y("destination_province:N", sort=top_provinces, title="目的省份"),
            color=alt.Color(
                "contribution_wan:Q",
                title="贡献（万元）",
                scale=alt.Scale(scheme="redblue", domainMid=0),
            ),
            tooltip=[
                alt.Tooltip("destination_province:N", title="目的省份"),
                alt.Tooltip("weight_band:N", title="公斤段"),
                alt.Tooltip("contribution_wan:Q", title="贡献（万元）", format=",.2f"),
                alt.Tooltip("ticket_count_wan:Q", title="票量（万票）", format=",.2f"),
                alt.Tooltip("weight_total_wan:Q", title="重量（万公斤）", format=",.2f"),
                alt.Tooltip("unit_contribution:Q", title="单票贡献", format=",.2f"),
                alt.Tooltip("kg_contribution:Q", title="公斤贡献", format=",.2f"),
            ],
        )
        .properties(height=max(360, len(top_provinces) * 24))
    )
    st.altair_chart(chart, width="stretch")

    st.caption("明细表按贡献绝对值取前 20 个目的省份，金额单位为万元。")
    show_business_table(
        heatmap_df.sort_values("contribution_total", ascending=False).head(200),
        [
            "destination_province",
            "weight_band",
            "ticket_count",
            "weight_total",
            "contribution_total",
            "unit_contribution",
            "kg_contribution",
        ],
        height=420,
    )


@st.cache_data(show_spinner=False)
def parse_workbook(file_bytes: bytes, file_name: str) -> dict[str, object]:
    suffix = Path(file_name).suffix or ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(file_bytes)
        temp_path = Path(handle.name)

    try:
        inspection = inspect_workbook(temp_path, template_code=TEMPLATE_CODE)
        franchise_rows = parse_franchise_month_rows(temp_path, template_code=TEMPLATE_CODE)
        site_rows = parse_site_month_rows(temp_path, template_code=TEMPLATE_CODE)
        region_flow_rows = parse_contribution_flow_rows(
            temp_path,
            scope_type="region",
            template_code=TEMPLATE_CODE,
        )
        validation = validate_summary_totals(inspection.overview, franchise_rows, site_rows)
    finally:
        with suppress(OSError):
            temp_path.unlink(missing_ok=True)

    return {
        "inspection": inspection.as_dict(),
        "overview": inspection.overview.as_dict(),
        "franchise_df": to_dataframe(franchise_rows),
        "site_df": to_dataframe(site_rows),
        "region_flow_df": to_dataframe(region_flow_rows),
        "validation_df": pd.DataFrame([result.as_dict() for result in validation]),
    }


st.set_page_config(
    page_title="加盟商贡献数据看板",
    layout="wide",
)

st.title("加盟商贡献数据看板")
st.caption("Streamlit 快速分析版：上传 Excel 后即时解析，不依赖 PostgreSQL。")

with st.sidebar:
    st.header("数据导入")
    upload = st.file_uploader("上传贡献表 Excel", type=["xlsx", "xlsm"])
    st.divider()
    st.caption("正式 React/FastAPI 版本仍以 PostgreSQL 为主；这个页面用于快速分享和复核。")

if upload is None:
    st.info("请在左侧上传 Excel 文件。")
    st.stop()

try:
    with st.spinner("正在解析 Excel..."):
        parsed = parse_workbook(upload.getvalue(), upload.name)
except Exception as exc:  # pragma: no cover - Streamlit runtime feedback
    st.error("Excel 解析失败，请确认上传的是当前模板的加盟商贡献表。")
    st.caption(f"错误信息：{exc}")
    st.stop()

overview = parsed["overview"]
franchise_df = parsed["franchise_df"]
site_df = parsed["site_df"]
region_flow_df = parsed["region_flow_df"]
validation_df = parsed["validation_df"]
inspection = parsed["inspection"]

st.subheader("经营总览")
kpi_cols = st.columns(4)
kpi_cols[0].metric("加盟商数", number(overview.get("franchise_count")))
kpi_cols[1].metric("网点数", number(overview.get("site_count")))
kpi_cols[2].metric("出港票量", count_wan(overview.get("outbound_tickets")))
kpi_cols[3].metric("进港签收量", count_wan(overview.get("inbound_signed_tickets")))

kpi_cols = st.columns(4)
kpi_cols[0].metric("出港总贡献", money_wan(overview.get("outbound_contribution")))
kpi_cols[1].metric("进港总贡献", money_wan(overview.get("inbound_contribution")))
kpi_cols[2].metric("总贡献", money_wan(overview.get("total_contribution")))
kpi_cols[3].metric("扣款小计", money_wan(overview.get("deduction_total")))

passed = int(validation_df["passed"].sum()) if not validation_df.empty else 0
failed = int(len(validation_df) - passed)
if failed:
    st.error(f"校验失败 {failed} 项，请先复核源表。")
else:
    st.success(f"校验通过 {passed} 项。")

tabs = st.tabs(["加盟商排行", "网点样本", "流向热力", "校验明细", "表结构"])

with tabs[0]:
    st.subheader("加盟商贡献排行")
    if franchise_df.empty:
        st.warning("未解析到加盟商汇总数据。")
    else:
        rank_df = franchise_df.copy()
        top, bottom = st.columns(2)
        with top:
            render_rank_bar(rank_df, "franchise_name", "total_contribution", "Top 10，总贡献", limit=10)
        with bottom:
            render_rank_bar(
                rank_df,
                "franchise_name",
                "total_contribution",
                "Bottom 10，总贡献",
                limit=10,
                ascending=True,
            )

        risk = rank_df[
            (numeric(rank_df["total_contribution"]) < 0)
            | (numeric(rank_df["inbound_contribution"]) < 0)
            | (numeric(rank_df["deduction_total"]) >= 50000)
        ].sort_values("total_contribution")
        st.caption("风险样本：负贡献、进港亏损或扣款小计超过 5 万元。")
        show_business_table(
            risk.head(30),
            [
                "franchise_name",
                "total_contribution",
                "outbound_contribution",
                "inbound_contribution",
                "deduction_total",
                "outbound_tickets",
                "daily_over_5000_flag",
            ],
            height=360,
        )

with tabs[1]:
    st.subheader("网点样本")
    if site_df.empty:
        st.warning("未解析到网点汇总数据。")
    else:
        display = site_df.copy()
        render_rank_bar(display, "site_name", "total_contribution", "网点 Top 12，总贡献", limit=12)
        show_business_table(
            display.sort_values("total_contribution", ascending=False).head(100),
            [
                "site_name",
                "franchise_name",
                "site_status",
                "total_contribution",
                "outbound_contribution",
                "inbound_contribution",
                "deduction_total",
                "outbound_tickets",
            ],
            height=460,
        )

with tabs[2]:
    st.subheader("目的省份与公斤段热力")
    render_heatmap(region_flow_df)

with tabs[3]:
    st.subheader("校验明细")
    if validation_df.empty:
        st.warning("暂无校验结果。")
    else:
        validation_display = validation_df.copy()
        validation_display["metric_code"] = validation_display["metric_code"].map(FIELD_LABELS).fillna(
            validation_display["metric_code"]
        )
        show_business_table(
            validation_display,
            ["passed", "metric_code", "expected_value", "actual_value", "diff_value", "tolerance", "message"],
            height=360,
        )

with tabs[4]:
    st.subheader("Workbook 结构")
    sheet_df = pd.DataFrame(inspection["sheets"])
    st.write(f"Sheet 数量：{inspection['sheet_count']}")
    st.dataframe(sheet_df, hide_index=True, width="stretch")
