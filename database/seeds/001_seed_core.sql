insert into dim_region(region_code, region_name)
values ('LN', '辽宁区域')
on conflict (region_code) do update set region_name = excluded.region_name;

insert into dim_month(period_month, year, month)
values ('202604', 2026, 4)
on conflict (period_month) do nothing;

insert into template_config(template_code, template_name, version, effective_from, is_active)
values ('franchise_contribution_v1', '加盟商贡献表', '1.0.0', '2026-04-01', true)
on conflict (template_code) do update
set template_name = excluded.template_name,
    version = excluded.version,
    is_active = excluded.is_active;

insert into sheet_mapping(template_code, standard_sheet_code, sheet_name_pattern, header_start_row, header_end_row, data_start_row, total_row, required)
values
  ('franchise_contribution_v1', 'franchise_summary', '总表-加盟商', 1, 3, 5, 4, true),
  ('franchise_contribution_v1', 'site_summary', '总表-网点', 1, 3, 5, 4, true),
  ('franchise_contribution_v1', 'one_price_summary', '总表-一口价', 2, 2, 3, 1, false),
  ('franchise_contribution_v1', 'contribution_region', '辽宁区域贡献', 1, 2, 3, null, false),
  ('franchise_contribution_v1', 'contribution_franchise', '加盟商贡献', 1, 2, 3, null, false),
  ('franchise_contribution_v1', 'fee_policy', '出港考核、派费补贴', 1, 1, 2, null, false),
  ('franchise_contribution_v1', 'warehouse_fee', '包仓费明细', 1, 1, 2, null, false),
  ('franchise_contribution_v1', 'operation_fee', '运营管理类汇总表', 1, 1, 2, null, false)
on conflict do nothing;

insert into dim_weight_band(weight_band, sort_order, display_name)
values
  ('0.3', 1, '0.3'),
  ('0.5', 2, '0.5'),
  ('1', 3, '1'),
  ('2', 4, '2'),
  ('3.2', 5, '3.2'),
  ('4', 6, '4'),
  ('5.2', 7, '5.2'),
  ('6', 8, '6'),
  ('7', 9, '7'),
  ('8', 10, '8'),
  ('9', 11, '9'),
  ('10.3', 12, '10.3'),
  ('＞10.3', 13, '＞10.3')
on conflict (weight_band) do update
set sort_order = excluded.sort_order,
    display_name = excluded.display_name;

insert into metric_definition(metric_code, metric_name, metric_group, formula, source_table, unit, display_unit, precision, direction, description)
values
  ('total_contribution', '总贡献', '贡献', 'outbound_contribution + inbound_contribution', 'fact_franchise_month', '元', '万元', 2, 'higher_better', '进出港总贡献'),
  ('outbound_contribution', '出港总贡献', '贡献', null, 'fact_franchise_month', '元', '万元', 2, 'higher_better', '出港经营贡献'),
  ('inbound_contribution', '进港总贡献', '贡献', null, 'fact_franchise_month', '元', '万元', 2, 'higher_better', '进港经营贡献'),
  ('outbound_unit_contribution', '出港单票贡献', '效率', 'outbound_contribution / outbound_tickets', 'fact_franchise_month', '元/票', '元/票', 2, 'higher_better', '出港每票贡献'),
  ('inbound_unit_contribution', '进港通票贡献', '效率', 'inbound_contribution / inbound_signed_tickets', 'fact_franchise_month', '元/票', '元/票', 2, 'higher_better', '进港每票贡献'),
  ('deduction_total', '扣款小计', '扣款', null, 'fact_franchise_month', '元', '万元', 2, 'lower_better', '进港扣款小计')
on conflict (metric_code) do update
set metric_name = excluded.metric_name,
    metric_group = excluded.metric_group,
    formula = excluded.formula,
    source_table = excluded.source_table,
    unit = excluded.unit,
    display_unit = excluded.display_unit,
    precision = excluded.precision,
    direction = excluded.direction,
    description = excluded.description;

insert into dim_tag(tag_code, tag_name, tag_group, target_type, description)
values
  ('high-contribution', '高贡献', '贡献', 'franchise', '总贡献进入当月头部'),
  ('negative-contribution', '负贡献', '风险', 'franchise', '总贡献小于0'),
  ('high-volume-low-profit', '高票低利', '风险', 'franchise', '出港票量高但单票贡献低'),
  ('inbound-loss', '进港亏损', '风险', 'franchise', '进港总贡献小于0'),
  ('high-deduction-risk', '扣款高风险', '风险', 'franchise', '扣款小计较高')
on conflict (tag_code) do update
set tag_name = excluded.tag_name,
    tag_group = excluded.tag_group,
    target_type = excluded.target_type,
    description = excluded.description;
