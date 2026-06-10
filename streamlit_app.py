from __future__ import annotations

import re
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
    "source_file": "来源文件",
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
    "total_unit_contribution": "单票边际贡献",
    "contribution_share": "贡献占比",
    "cumulative_share": "累计贡献占比",
    "risk_tag": "风险标签",
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
    "dispatch_unit_fee": "派费单票",
    "delivery_density_proxy": "派送密度代理",
    "dispatch_pressure_score": "派费压力分",
    "nearest_site_hint": "近邻网点提示",
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
RATE_FIELDS = {"ticket_share", "contribution_share", "cumulative_share"}
UNIT_FIELDS = {
    "outbound_avg_weight",
    "outbound_unit_contribution",
    "outbound_kg_contribution",
    "outbound_pass_contribution",
    "inbound_pass_contribution",
    "total_unit_contribution",
    "unit_four_fee",
    "unit_settlement_price",
    "unit_dispatch_fee",
    "unit_contribution",
    "kg_contribution",
    "dispatch_unit_fee",
    "delivery_density_proxy",
    "dispatch_pressure_score",
}


def number(value: float | int | None) -> str:
    return "-" if value is None else f"{value:,.0f}"


def money_wan(value: float | int | None) -> str:
    return "-" if value is None else f"{value / 10000:,.2f} 万元"


def count_wan(value: float | int | None) -> str:
    return "-" if value is None else f"{value / 10000:,.2f} 万"


def format_percent(value: float | int | None) -> str:
    return "-" if value is None else f"{value * 100:,.1f}%"


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = numeric(denominator)
    result = numeric(numerator) / denominator.where(denominator != 0)
    return result.replace([float("inf"), float("-inf")], pd.NA).fillna(0)


def to_dataframe(rows: list[object], source_file: str) -> pd.DataFrame:
    df = pd.DataFrame([row.as_dict() for row in rows])
    if not df.empty:
        df["source_file"] = source_file
    return df


def infer_period(file_name: str, *frames: pd.DataFrame) -> str:
    for frame in frames:
        if not frame.empty and "period_month" in frame.columns:
            value = frame["period_month"].dropna().astype(str)
            if not value.empty:
                return value.iloc[0]
    match = re.search(r"(20\d{4})", file_name)
    return match.group(1) if match else "unknown"


def add_franchise_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()
    result["total_unit_contribution"] = safe_divide(result["total_contribution"], result["outbound_tickets"])
    total_positive = numeric(result["total_contribution"]).clip(lower=0).sum()
    if total_positive:
        result["contribution_share"] = numeric(result["total_contribution"]).clip(lower=0) / total_positive
    else:
        result["contribution_share"] = 0
    result = result.sort_values(["period_month", "total_contribution"], ascending=[True, False])
    result["cumulative_share"] = result.groupby("period_month")["contribution_share"].cumsum()
    result["risk_tag"] = "正常"
    result.loc[numeric(result["total_unit_contribution"]) < 0, "risk_tag"] = "单票为负"
    result.loc[
        (numeric(result["total_unit_contribution"]) >= 0) & (numeric(result["total_unit_contribution"]) < 0.3),
        "risk_tag",
    ] = "单票低于 0.3"
    result.loc[numeric(result["deduction_total"]) >= 50000, "risk_tag"] = "高扣款"
    return result


def add_site_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()
    result["total_unit_contribution"] = safe_divide(result["total_contribution"], result["outbound_tickets"])
    result["dispatch_unit_fee"] = safe_divide(result["deduction_total"], result["outbound_tickets"])
    result["delivery_density_proxy"] = numeric(result["outbound_tickets"]) / numeric(result["outbound_weight"]).where(
        numeric(result["outbound_weight"]) != 0
    )
    result["delivery_density_proxy"] = result["delivery_density_proxy"].fillna(0)
    result["dispatch_pressure_score"] = (
        numeric(result["deduction_total"]).rank(pct=True)
        + numeric(result["outbound_tickets"]).rank(pct=True)
        - numeric(result["total_unit_contribution"]).rank(pct=True)
    )
    result["nearest_site_hint"] = result.groupby("franchise_name")["site_name"].transform(
        lambda values: "、".join(values.dropna().astype(str).head(3))
    )
    return result


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
        elif any(label in column for label in ["单票", "公斤", "均重", "密度", "压力"]):
            config[column] = st.column_config.NumberColumn(column, format="%.3f")
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
    unit: str = "万元",
    scale_by_10000: bool = True,
) -> None:
    if df.empty or name_col not in df.columns or metric_col not in df.columns:
        st.warning("当前筛选下没有可展示的排行数据。")
        return

    chart_df = df[[name_col, metric_col]].copy()
    chart_df[metric_col] = numeric(chart_df[metric_col])
    chart_df = chart_df.sort_values(metric_col, ascending=ascending).head(limit)
    chart_df["name_label"] = chart_df[name_col].astype(str)
    chart_df["value_display"] = chart_df[metric_col] / 10000 if scale_by_10000 else chart_df[metric_col]
    sort_order = chart_df["name_label"].tolist()

    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X("value_display:Q", title=f"{FIELD_LABELS.get(metric_col, metric_col)}（{unit}）", scale=alt.Scale(zero=True)),
            y=alt.Y("name_label:N", sort=sort_order, title=None, axis=alt.Axis(labelLimit=300)),
            color=alt.condition("datum.value_display >= 0", alt.value("#2f7d57"), alt.value("#c2413d")),
            tooltip=[
                alt.Tooltip("name_label:N", title=FIELD_LABELS.get(name_col, name_col)),
                alt.Tooltip("value_display:Q", title=f"{FIELD_LABELS.get(metric_col, metric_col)}（{unit}）", format=",.2f"),
            ],
        )
        .properties(title=title, height=max(260, len(chart_df) * 30))
    )
    st.altair_chart(chart, width="stretch")


def render_trend(overview_df: pd.DataFrame) -> None:
    if overview_df["period_month"].nunique() < 2:
        st.info("当前只上传了一个月份。上传多个月份贡献表后，这里会展示单票边际贡献的时间变化。")
        return

    trend = overview_df.copy()
    trend["total_unit_contribution"] = safe_divide(trend["total_contribution"], trend["outbound_tickets"])
    trend["total_contribution_wan"] = numeric(trend["total_contribution"]) / 10000
    chart = (
        alt.Chart(trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("period_month:N", title="月份"),
            y=alt.Y("total_unit_contribution:Q", title="单票边际贡献"),
            tooltip=[
                alt.Tooltip("period_month:N", title="月份"),
                alt.Tooltip("total_unit_contribution:Q", title="单票边际贡献", format=",.3f"),
                alt.Tooltip("total_contribution_wan:Q", title="总贡献（万元）", format=",.2f"),
            ],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, width="stretch")


def render_pareto(franchise_df: pd.DataFrame, top_n: int) -> None:
    if franchise_df.empty:
        st.warning("未解析到加盟商汇总数据。")
        return
    latest_period = franchise_df["period_month"].max()
    base = franchise_df[franchise_df["period_month"] == latest_period].copy()
    base = base.sort_values("total_contribution", ascending=False)
    base["rank"] = range(1, len(base) + 1)
    base["contribution_wan"] = numeric(base["total_contribution"]) / 10000
    positive_total = numeric(base["total_contribution"]).clip(lower=0).sum()
    base["cumulative_share_pct"] = (
        numeric(base["total_contribution"]).clip(lower=0).cumsum() / positive_total * 100 if positive_total else 0
    )
    top_share = numeric(base.head(top_n)["total_contribution"]).clip(lower=0).sum() / positive_total if positive_total else 0
    st.metric(f"Top {top_n} 贡献占比", format_percent(top_share))

    chart_df = base.head(max(top_n, 30))
    bars = alt.Chart(chart_df).mark_bar(color="#2f7d57").encode(
        x=alt.X("rank:O", title="排名"),
        y=alt.Y("contribution_wan:Q", title="总贡献（万元）"),
        tooltip=[
            alt.Tooltip("franchise_name:N", title="加盟商"),
            alt.Tooltip("contribution_wan:Q", title="总贡献（万元）", format=",.2f"),
            alt.Tooltip("cumulative_share_pct:Q", title="累计占比（%）", format=",.1f"),
        ],
    )
    line = alt.Chart(chart_df).mark_line(point=True, color="#2563eb").encode(
        x=alt.X("rank:O"),
        y=alt.Y("cumulative_share_pct:Q", title="累计贡献占比（%）"),
    )
    st.altair_chart(alt.layer(bars, line).resolve_scale(y="independent").properties(height=300), width="stretch")


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
            color=alt.Color("contribution_wan:Q", title="贡献（万元）", scale=alt.Scale(scheme="redblue", domainMid=0)),
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
        region_flow_rows = parse_contribution_flow_rows(temp_path, scope_type="region", template_code=TEMPLATE_CODE)
        validation = validate_summary_totals(inspection.overview, franchise_rows, site_rows)
    finally:
        with suppress(OSError):
            temp_path.unlink(missing_ok=True)

    franchise_df = to_dataframe(franchise_rows, file_name)
    site_df = to_dataframe(site_rows, file_name)
    region_flow_df = to_dataframe(region_flow_rows, file_name)
    period_month = infer_period(file_name, franchise_df, site_df, region_flow_df)
    overview = inspection.overview.as_dict()
    overview["period_month"] = period_month
    overview["source_file"] = file_name

    for frame in [franchise_df, site_df, region_flow_df]:
        if not frame.empty and "period_month" not in frame.columns:
            frame["period_month"] = period_month

    return {
        "inspection": inspection.as_dict(),
        "overview": overview,
        "franchise_df": franchise_df,
        "site_df": site_df,
        "region_flow_df": region_flow_df,
        "validation_df": pd.DataFrame([result.as_dict() for result in validation]),
    }


st.set_page_config(page_title="加盟商贡献数据看板", layout="wide")

st.title("加盟商贡献数据看板")
st.caption("按单票边际贡献、加盟商集中度、项目总览、流向重点和派费异常来复核贡献表。")

with st.sidebar:
    st.header("数据导入")
    uploads = st.file_uploader("上传贡献表 Excel，可多选月份", type=["xlsx", "xlsm"], accept_multiple_files=True)
    st.divider()
    st.caption("快速分析版不依赖 PostgreSQL。多个月份文件用于趋势，单月文件用于当月诊断。")

if not uploads:
    st.info("请在左侧上传 Excel 文件。")
    st.stop()

parsed_files: list[dict[str, object]] = []
try:
    with st.spinner("正在解析 Excel..."):
        for upload in uploads:
            parsed_files.append(parse_workbook(upload.getvalue(), upload.name))
except Exception as exc:  # pragma: no cover - Streamlit runtime feedback
    st.error("Excel 解析失败，请确认上传的是当前模板的加盟商贡献表。")
    st.caption(f"错误信息：{exc}")
    st.stop()

overview_df = pd.DataFrame([item["overview"] for item in parsed_files])
franchise_df = pd.concat([item["franchise_df"] for item in parsed_files], ignore_index=True)
site_df = pd.concat([item["site_df"] for item in parsed_files], ignore_index=True)
region_flow_df = pd.concat([item["region_flow_df"] for item in parsed_files], ignore_index=True)
validation_df = pd.concat([item["validation_df"] for item in parsed_files], ignore_index=True)
inspection = parsed_files[-1]["inspection"]

franchise_df = add_franchise_metrics(franchise_df)
site_df = add_site_metrics(site_df)

latest_period = overview_df["period_month"].max()
latest_overview = overview_df[overview_df["period_month"] == latest_period].iloc[-1].to_dict()
latest_franchise = franchise_df[franchise_df["period_month"] == latest_period].copy()
latest_site = site_df[site_df["period_month"] == latest_period].copy()
latest_flow = region_flow_df[region_flow_df["period_month"] == latest_period].copy()

st.subheader("经营总览")
kpi_cols = st.columns(4)
kpi_cols[0].metric("加盟商数", number(latest_overview.get("franchise_count")))
kpi_cols[1].metric("网点数", number(latest_overview.get("site_count")))
kpi_cols[2].metric("出港票量", count_wan(latest_overview.get("outbound_tickets")))
kpi_cols[3].metric("进港签收量", count_wan(latest_overview.get("inbound_signed_tickets")))

kpi_cols = st.columns(4)
kpi_cols[0].metric("出港总贡献", money_wan(latest_overview.get("outbound_contribution")))
kpi_cols[1].metric("进港总贡献", money_wan(latest_overview.get("inbound_contribution")))
kpi_cols[2].metric("总贡献", money_wan(latest_overview.get("total_contribution")))
kpi_cols[3].metric("单票边际贡献", f"{float(latest_overview.get('total_contribution', 0)) / max(float(latest_overview.get('outbound_tickets', 0)), 1):,.3f}")

passed = int(validation_df["passed"].sum()) if not validation_df.empty else 0
failed = int(len(validation_df) - passed)
if failed:
    st.error(f"校验失败 {failed} 项，请先复核源表。")
else:
    st.success(f"校验通过 {passed} 项。")

tabs = st.tabs(["单票贡献", "加盟商卡片", "综合大表", "流向/供应商", "派费分析", "校验/表结构"])

with tabs[0]:
    st.subheader("单票边际贡献")
    render_trend(overview_df)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        top_n = st.radio("集中度范围", [20, 30], horizontal=True)
    with col_b:
        low_threshold = st.number_input("低单票阈值", min_value=0.0, value=0.3, step=0.1)

    render_pareto(latest_franchise, top_n)

    low_unit = latest_franchise[numeric(latest_franchise["total_unit_contribution"]) < low_threshold].sort_values(
        "total_unit_contribution"
    )
    st.caption("单票边际贡献为负或低于阈值的加盟商。")
    show_business_table(
        low_unit.head(60),
        [
            "franchise_name",
            "total_unit_contribution",
            "total_contribution",
            "outbound_tickets",
            "outbound_contribution",
            "inbound_contribution",
            "deduction_total",
            "risk_tag",
        ],
        height=420,
    )

with tabs[1]:
    st.subheader("加盟商维度卡片")
    selected = st.selectbox(
        "选择加盟商",
        latest_franchise.sort_values("total_contribution", ascending=False)["franchise_name"].dropna().tolist(),
    )
    selected_rows = franchise_df[franchise_df["franchise_name"] == selected].sort_values("period_month")
    current = selected_rows[selected_rows["period_month"] == latest_period].iloc[-1]

    card_cols = st.columns(4)
    card_cols[0].metric("加盟商总贡献", money_wan(current.get("total_contribution")))
    card_cols[1].metric("加盟商单票边际贡献", f"{current.get('total_unit_contribution', 0):,.3f}")
    card_cols[2].metric("加盟商贡献占比", format_percent(current.get("contribution_share")))
    card_cols[3].metric("加盟商风险标签", str(current.get("risk_tag", "-")))

    if selected_rows["period_month"].nunique() >= 2:
        history = selected_rows.copy()
        history["total_contribution_wan"] = numeric(history["total_contribution"]) / 10000
        chart = (
            alt.Chart(history)
            .mark_line(point=True)
            .encode(
                x=alt.X("period_month:N", title="月份"),
                y=alt.Y("total_unit_contribution:Q", title="单票边际贡献"),
                tooltip=[
                    alt.Tooltip("period_month:N", title="月份"),
                    alt.Tooltip("total_unit_contribution:Q", title="单票边际贡献", format=",.3f"),
                    alt.Tooltip("total_contribution_wan:Q", title="总贡献（万元）", format=",.2f"),
                ],
            )
            .properties(height=280)
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("当前只有一个月份，卡片展示当月总值。上传历史月份后会显示该加盟商历史贡献变化。")

    show_business_table(
        selected_rows,
        [
            "period_month",
            "franchise_name",
            "total_contribution",
            "total_unit_contribution",
            "outbound_tickets",
            "outbound_contribution",
            "inbound_contribution",
            "deduction_total",
            "risk_tag",
        ],
        height=260,
    )

with tabs[2]:
    st.subheader("综合大表")
    st.caption("大表覆盖时间、加盟商、项目总贡献、流向风险所需字段。当前版本按加盟商粒度展示，后续可接供应商字段。")
    show_business_table(
        latest_franchise.sort_values("total_contribution", ascending=False),
        [
            "period_month",
            "franchise_name",
            "total_contribution",
            "contribution_share",
            "cumulative_share",
            "total_unit_contribution",
            "outbound_tickets",
            "outbound_weight",
            "outbound_contribution",
            "inbound_signed_tickets",
            "inbound_contribution",
            "deduction_total",
            "risk_tag",
        ],
        height=560,
    )

with tabs[3]:
    st.subheader("流向维度与供应商维度")
    left, right = st.columns([1, 1])
    with left:
        render_heatmap(latest_flow)
    with right:
        province_rank = (
            latest_flow.groupby("destination_province", as_index=False)
            .agg(
                contribution_total=("contribution_total", "sum"),
                ticket_count=("ticket_count", "sum"),
                weight_total=("weight_total", "sum"),
                unit_contribution=("unit_contribution", "mean"),
            )
            .sort_values("contribution_total")
        )
        st.caption("负贡献目的省份优先复核。")
        show_business_table(
            province_rank.head(30),
            ["destination_province", "contribution_total", "ticket_count", "weight_total", "unit_contribution"],
            height=420,
        )
        st.info("当前 Excel 未提供供应商字段。后续如果补充供应商或代理区字段，可在这里增加供应商 Top、负值和异常费用排行。")

with tabs[4]:
    st.subheader("派费分析与异常识别")
    st.caption("当前用已解析字段构建派费代理分析：扣款小计、票量、重量、单票贡献、同加盟商近邻网点提示。距离、面积、密度字段接入后可替换为正式模型。")

    dispatch_candidates = latest_site.copy()
    dispatch_candidates = dispatch_candidates.sort_values("dispatch_pressure_score", ascending=False)

    render_rank_bar(
        dispatch_candidates,
        "site_name",
        "dispatch_pressure_score",
        "派费压力 Top 20",
        limit=20,
        unit="分",
        scale_by_10000=False,
    )
    show_business_table(
        dispatch_candidates.head(80),
        [
            "site_name",
            "franchise_name",
            "outbound_tickets",
            "outbound_weight",
            "deduction_total",
            "total_unit_contribution",
            "dispatch_unit_fee",
            "delivery_density_proxy",
            "dispatch_pressure_score",
            "nearest_site_hint",
        ],
        height=520,
    )

with tabs[5]:
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
            height=300,
        )

    st.subheader("Workbook 结构")
    sheet_df = pd.DataFrame(inspection["sheets"])
    st.write(f"最近上传文件 Sheet 数量：{inspection['sheet_count']}")
    st.dataframe(sheet_df, hide_index=True, width="stretch")
