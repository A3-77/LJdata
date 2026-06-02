from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase


@dataclass(frozen=True)
class SheetRule:
    standard_sheet_code: str
    sheet_name_patterns: tuple[str, ...]
    header_start_row: int
    header_end_row: int
    data_start_row: int
    total_row: int | None
    required: bool = True

    @property
    def sheet_name_pattern(self) -> str:
        return self.sheet_name_patterns[0]

    def matches(self, sheet_name: str) -> bool:
        return any(fnmatchcase(sheet_name, pattern) for pattern in self.sheet_name_patterns)


@dataclass(frozen=True)
class TemplateProfile:
    template_code: str
    template_name: str
    version: str
    sheet_rules: tuple[SheetRule, ...]
    weight_bands: tuple[str, ...]
    contribution_group_starts: dict[str, int]

    def rule_for_sheet(self, sheet_name: str) -> SheetRule | None:
        for rule in self.sheet_rules:
            if rule.matches(sheet_name):
                return rule
        return None

    def sheet_name_for_code(self, sheet_names: list[str], standard_sheet_code: str) -> str | None:
        rule = self.rule_for_code(standard_sheet_code)
        if rule is None:
            return None
        for sheet_name in sheet_names:
            if rule.matches(sheet_name):
                return sheet_name
        return None

    def rule_for_code(self, standard_sheet_code: str) -> SheetRule | None:
        for rule in self.sheet_rules:
            if rule.standard_sheet_code == standard_sheet_code:
                return rule
        return None


DEFAULT_WEIGHT_BANDS = ("0.3", "0.5", "1", "2", "3.2", "4", "5.2", "6", "7", "8", "9", "10.3", "＞10.3")

DEFAULT_CONTRIBUTION_GROUP_STARTS = {
    "ticket_count": 6,
    "ticket_share": 20,
    "weight_total": 34,
    "four_fee_total": 48,
    "settlement_price": 62,
    "dispatch_fee": 76,
    "contribution_total": 90,
    "unit_four_fee": 104,
    "unit_settlement_price": 118,
    "unit_dispatch_fee": 132,
    "unit_contribution": 146,
    "kg_contribution": 160,
}

FRANCHISE_CONTRIBUTION_V1 = TemplateProfile(
    template_code="franchise_contribution_v1",
    template_name="加盟商贡献表",
    version="1.0.0",
    sheet_rules=(
        SheetRule("franchise_summary", ("总表-加盟商",), 1, 3, 5, 4, True),
        SheetRule("site_summary", ("总表-网点",), 1, 3, 5, 4, True),
        SheetRule("one_price_summary", ("总表-一口价",), 2, 2, 3, 1, False),
        SheetRule("contribution_region", ("辽宁区域贡献", "*区域贡献"), 1, 2, 3, None, False),
        SheetRule("contribution_franchise", ("加盟商贡献",), 1, 2, 3, None, False),
        SheetRule("fee_policy", ("出港考核、派费补贴",), 1, 1, 2, None, False),
        SheetRule("warehouse_fee", ("包仓费明细",), 1, 1, 2, None, False),
        SheetRule("operation_fee", ("运营管理类汇总表",), 1, 1, 2, None, False),
    ),
    weight_bands=DEFAULT_WEIGHT_BANDS,
    contribution_group_starts=DEFAULT_CONTRIBUTION_GROUP_STARTS,
)

TEMPLATE_PROFILES = {
    FRANCHISE_CONTRIBUTION_V1.template_code: FRANCHISE_CONTRIBUTION_V1,
}


def get_template_profile(template_code: str = "franchise_contribution_v1") -> TemplateProfile:
    try:
        return TEMPLATE_PROFILES[template_code]
    except KeyError as exc:
        known = ", ".join(sorted(TEMPLATE_PROFILES))
        raise ValueError(f"Unknown template profile: {template_code}. Known profiles: {known}") from exc
