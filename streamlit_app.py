from __future__ import annotations

import sys
import tempfile
from pathlib import Path

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
METRIC_LABELS = {
    "franchise_count": "加盟商数",
    "site_count": "网点数",
    "outbound_tickets": "出港票量",
    "outbound_weight": "出港重量",
    "inbound_signed_tickets": "进港签收量",
    "outbound_contribution": "出港总贡献",
    "inbound_contribution": "进港总贡献",
    "total_contribution": "总贡献",
    "deduction_total": "扣款小计",
}
WEIGHT_BAND_ORDER = ["0.3", "0.5", "1", "2", "3.2", "4", "5.2", "6", "7", "8", "9", "10.3", "＞10.3"]


def number(value: float | int | None) -> str:
    return "-" if value is None else f"{value:,.0f}"


def money_wan(value: float | int | None) -> str:
    return "-" if value is None else f"{value / 10000:,.2f} 万元"


def count_wan(value: float | int | None) -> str:
    return "-" if value is None else f"{value / 10000:,.2f} 万"


def to_dataframe(rows: list[object]) -> pd.DataFrame:
    return pd.DataFrame([row.as_dict() for row in rows])


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

with st.spinner("正在解析 Excel..."):
    parsed = parse_workbook(upload.getvalue(), upload.name)

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
        rank_df["total_contribution_wan"] = rank_df["total_contribution"].fillna(0) / 10000
        top = rank_df.sort_values("total_contribution_wan", ascending=False).head(10)
        bottom = rank_df.sort_values("total_contribution_wan", ascending=True).head(10)

        left, right = st.columns(2)
        with left:
            st.caption("Top 10，总贡献，万元")
            st.bar_chart(top.set_index("franchise_name")["total_contribution_wan"])
        with right:
            st.caption("Bottom 10，总贡献，万元")
            st.bar_chart(bottom.set_index("franchise_name")["total_contribution_wan"])

        risk = rank_df[
            (rank_df["total_contribution"].fillna(0) < 0)
            | (rank_df["inbound_contribution"].fillna(0) < 0)
            | (rank_df["deduction_total"].fillna(0) >= 50000)
        ].copy()
        st.caption("风险样本")
        st.dataframe(
            risk[
                [
                    "franchise_name",
                    "total_contribution",
                    "outbound_contribution",
                    "inbound_contribution",
                    "deduction_total",
                    "outbound_tickets",
                ]
            ].head(30),
            use_container_width=True,
        )

with tabs[1]:
    st.subheader("网点样本")
    if site_df.empty:
        st.warning("未解析到网点汇总数据。")
    else:
        display = site_df.copy()
        display["total_contribution_wan"] = display["total_contribution"].fillna(0) / 10000
        st.bar_chart(
            display.sort_values("total_contribution_wan", ascending=False)
            .head(12)
            .set_index("site_name")["total_contribution_wan"]
        )
        st.dataframe(
            display[
                [
                    "site_name",
                    "franchise_name",
                    "site_status",
                    "total_contribution",
                    "outbound_contribution",
                    "inbound_contribution",
                    "deduction_total",
                    "outbound_tickets",
                ]
            ].head(100),
            use_container_width=True,
        )

with tabs[2]:
    st.subheader("目的省份与公斤段热力表")
    if region_flow_df.empty:
        st.warning("未解析到区域流向数据。")
    else:
        flow = region_flow_df.copy()
        flow["contribution_wan"] = flow["contribution_total"].fillna(0) / 10000
        pivot = flow.pivot_table(
            index="destination_province",
            columns="weight_band",
            values="contribution_wan",
            aggfunc="sum",
            fill_value=0,
        )
        existing_columns = [band for band in WEIGHT_BAND_ORDER if band in pivot.columns]
        pivot = pivot[existing_columns]
        pivot = pivot.loc[pivot.abs().sum(axis=1).sort_values(ascending=False).head(20).index]
        st.dataframe(
            pivot.style.background_gradient(cmap="RdYlGn", axis=None).format("{:.2f}"),
            use_container_width=True,
        )

with tabs[3]:
    st.subheader("校验明细")
    if validation_df.empty:
        st.warning("暂无校验结果。")
    else:
        validation_display = validation_df.copy()
        validation_display["metric_name"] = validation_display["metric_code"].map(METRIC_LABELS).fillna(
            validation_display["metric_code"]
        )
        st.dataframe(
            validation_display[
                [
                    "passed",
                    "metric_name",
                    "expected_value",
                    "actual_value",
                    "diff_value",
                    "tolerance",
                    "message",
                ]
            ],
            use_container_width=True,
        )

with tabs[4]:
    st.subheader("Workbook 结构")
    sheet_df = pd.DataFrame(inspection["sheets"])
    st.write(f"Sheet 数量：{inspection['sheet_count']}")
    st.dataframe(sheet_df, use_container_width=True)
