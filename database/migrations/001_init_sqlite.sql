create table if not exists source_file (
  id integer primary key autoincrement,
  file_name text not null,
  file_hash text not null unique,
  file_path text not null,
  region_code text not null,
  period_month text not null,
  template_code text,
  import_status text not null default 'pending',
  uploaded_by text,
  uploaded_at text not null default CURRENT_TIMESTAMP
);

create table if not exists import_job (
  id integer primary key autoincrement,
  file_id integer not null references source_file(id),
  status text not null default 'pending',
  progress integer not null default 0,
  started_at text,
  finished_at text,
  message text,
  created_at text not null default CURRENT_TIMESTAMP
);

create table if not exists import_error (
  id integer primary key autoincrement,
  job_id integer not null references import_job(id),
  severity text not null,
  sheet_name text,
  row_number integer,
  column_name text,
  error_code text not null,
  error_message text not null,
  created_at text not null default CURRENT_TIMESTAMP
);

create table if not exists import_validation_result (
  id integer primary key autoincrement,
  job_id integer references import_job(id),
  rule_code text not null,
  metric_code text not null,
  expected_value real,
  actual_value real,
  diff_value real,
  tolerance real,
  passed integer not null,
  severity text not null,
  message text,
  created_at text not null default CURRENT_TIMESTAMP
);

create table if not exists source_sheet (
  id integer primary key autoincrement,
  file_id integer not null references source_file(id),
  sheet_name text not null,
  standard_sheet_code text,
  max_row integer,
  max_col integer,
  header_start_row integer,
  header_end_row integer,
  data_start_row integer,
  total_row integer,
  is_active integer not null default 1
);

create table if not exists template_config (
  template_code text primary key,
  template_name text not null,
  version text not null,
  effective_from text,
  effective_to text,
  is_active integer not null default 1
);

create table if not exists sheet_mapping (
  id integer primary key autoincrement,
  template_code text not null references template_config(template_code),
  standard_sheet_code text not null,
  sheet_name_pattern text not null,
  header_start_row integer not null,
  header_end_row integer not null,
  data_start_row integer not null,
  total_row integer,
  required integer not null default 1
);

create table if not exists field_mapping (
  id integer primary key autoincrement,
  template_code text not null references template_config(template_code),
  standard_sheet_code text not null,
  raw_header_path text,
  raw_column_letter text,
  standard_field text not null,
  data_type text not null,
  required integer not null default 0,
  default_value text,
  transform_rule text
);

create table if not exists dim_month (
  period_month text primary key,
  year integer not null,
  month integer not null
);

create table if not exists dim_region (
  region_code text primary key,
  region_name text not null
);

create table if not exists dim_franchise (
  id integer primary key autoincrement,
  franchise_code text unique,
  franchise_name text not null,
  region_code text references dim_region(region_code),
  active integer not null default 1,
  created_at text not null default CURRENT_TIMESTAMP,
  updated_at text not null default CURRENT_TIMESTAMP
);

create unique index if not exists ux_dim_franchise_region_name
  on dim_franchise(region_code, franchise_name);

create table if not exists dim_site (
  id integer primary key autoincrement,
  site_code text unique,
  site_name text not null,
  franchise_id integer references dim_franchise(id),
  city text,
  district text,
  status text,
  active integer not null default 1,
  created_at text not null default CURRENT_TIMESTAMP,
  updated_at text not null default CURRENT_TIMESTAMP
);

create unique index if not exists ux_dim_site_name_franchise
  on dim_site(site_name, franchise_id);

create table if not exists dim_weight_band (
  weight_band text primary key,
  sort_order integer not null unique,
  display_name text not null
);

create table if not exists dim_province (
  province_name text primary key,
  sort_order integer
);

create table if not exists dim_fee_type (
  fee_type_code text primary key,
  fee_type_name text not null,
  fee_group text
);

create table if not exists fact_franchise_month (
  id integer primary key autoincrement,
  file_id integer references source_file(id),
  period_month text not null references dim_month(period_month),
  region_code text not null references dim_region(region_code),
  franchise_id integer references dim_franchise(id),
  franchise_name text not null,
  daily_over_5000_flag integer,
  outbound_tickets real,
  outbound_weight real,
  outbound_avg_weight real,
  waybill_fee real,
  transfer_fee real,
  warehouse_fee real,
  operation_fee real,
  dispatch_fee real,
  one_price_rebate real,
  outbound_contribution real,
  outbound_unit_contribution real,
  outbound_kg_contribution real,
  inbound_signed_tickets real,
  inbound_weight real,
  inbound_dispatch_income real,
  inbound_dispatch_cost real,
  deduction_total real,
  inbound_contribution real,
  total_contribution real,
  outbound_pass_contribution real,
  inbound_pass_contribution real,
  created_at text not null default CURRENT_TIMESTAMP
);

create index if not exists idx_fact_franchise_month_period
  on fact_franchise_month(period_month);
create index if not exists idx_fact_franchise_month_rank
  on fact_franchise_month(period_month, total_contribution desc);

create table if not exists fact_site_month (
  id integer primary key autoincrement,
  file_id integer references source_file(id),
  period_month text not null references dim_month(period_month),
  region_code text not null references dim_region(region_code),
  franchise_id integer references dim_franchise(id),
  franchise_name text not null,
  site_id integer references dim_site(id),
  site_name text not null,
  site_status text,
  daily_over_5000_flag integer,
  outbound_tickets real,
  outbound_weight real,
  outbound_contribution real,
  inbound_signed_tickets real,
  inbound_contribution real,
  deduction_total real,
  total_contribution real,
  created_at text not null default CURRENT_TIMESTAMP
);

create index if not exists idx_fact_site_month_period
  on fact_site_month(period_month);
create index if not exists idx_fact_site_month_rank
  on fact_site_month(period_month, total_contribution desc);

create table if not exists fact_contribution_flow (
  id integer primary key autoincrement,
  file_id integer references source_file(id),
  period_month text not null references dim_month(period_month),
  scope_type text not null,
  region_code text references dim_region(region_code),
  franchise_id integer references dim_franchise(id),
  franchise_name text,
  destination_province text,
  weight_band text references dim_weight_band(weight_band),
  ticket_count real,
  ticket_share real,
  weight_total real,
  four_fee_total real,
  settlement_price real,
  dispatch_fee real,
  contribution_total real,
  unit_four_fee real,
  unit_settlement_price real,
  unit_dispatch_fee real,
  unit_contribution real,
  kg_contribution real,
  created_at text not null default CURRENT_TIMESTAMP
);

create index if not exists idx_fact_contribution_flow_heatmap
  on fact_contribution_flow(period_month, scope_type, destination_province, weight_band);

create table if not exists fact_one_price_summary (
  id integer primary key autoincrement,
  file_id integer references source_file(id),
  period_month text not null references dim_month(period_month),
  franchise_id integer references dim_franchise(id),
  franchise_name text not null,
  ticket_count real,
  daily_ticket_count real,
  billed_weight real,
  avg_weight real,
  four_fee real,
  settlement_price real,
  dispatch_fee real,
  contribution_total real,
  unit_contribution real,
  kg_contribution real,
  created_at text not null default CURRENT_TIMESTAMP
);

create table if not exists fact_fee_event (
  id integer primary key autoincrement,
  file_id integer references source_file(id),
  period_month text not null references dim_month(period_month),
  franchise_id integer references dim_franchise(id),
  franchise_name text,
  site_id integer references dim_site(id),
  site_name text,
  event_source text not null,
  fee_main_type text,
  fee_sub_type text,
  raw_amount real,
  display_amount real,
  remark text,
  created_at text not null default CURRENT_TIMESTAMP
);

create table if not exists metric_definition (
  metric_code text primary key,
  metric_name text not null,
  metric_group text not null,
  formula text,
  source_table text,
  unit text,
  display_unit text,
  precision integer not null default 2,
  direction text,
  description text
);

create table if not exists validation_rule (
  id integer primary key autoincrement,
  rule_code text not null unique,
  rule_name text not null,
  rule_type text not null,
  severity text not null,
  rule_sql text,
  is_active integer not null default 1
);

create table if not exists dim_tag (
  tag_code text primary key,
  tag_name text not null,
  tag_group text not null,
  target_type text not null,
  description text
);

create table if not exists tag_rule (
  id integer primary key autoincrement,
  tag_code text not null references dim_tag(tag_code),
  rule_sql text not null,
  priority integer not null default 100,
  is_active integer not null default 1
);
