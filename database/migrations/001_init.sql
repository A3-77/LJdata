create table if not exists source_file (
  id bigserial primary key,
  file_name text not null,
  file_hash text not null unique,
  file_path text not null,
  region_code text not null,
  period_month text not null,
  template_code text,
  import_status text not null default 'pending',
  uploaded_by text,
  uploaded_at timestamptz not null default now()
);

create table if not exists import_job (
  id bigserial primary key,
  file_id bigint not null references source_file(id),
  status text not null default 'pending',
  progress integer not null default 0,
  started_at timestamptz,
  finished_at timestamptz,
  message text,
  created_at timestamptz not null default now()
);

create table if not exists import_error (
  id bigserial primary key,
  job_id bigint not null references import_job(id),
  severity text not null,
  sheet_name text,
  row_number integer,
  column_name text,
  error_code text not null,
  error_message text not null,
  created_at timestamptz not null default now()
);

create table if not exists source_sheet (
  id bigserial primary key,
  file_id bigint not null references source_file(id),
  sheet_name text not null,
  standard_sheet_code text,
  max_row integer,
  max_col integer,
  header_start_row integer,
  header_end_row integer,
  data_start_row integer,
  total_row integer,
  is_active boolean not null default true
);

create table if not exists template_config (
  template_code text primary key,
  template_name text not null,
  version text not null,
  effective_from date,
  effective_to date,
  is_active boolean not null default true
);

create table if not exists sheet_mapping (
  id bigserial primary key,
  template_code text not null references template_config(template_code),
  standard_sheet_code text not null,
  sheet_name_pattern text not null,
  header_start_row integer not null,
  header_end_row integer not null,
  data_start_row integer not null,
  total_row integer,
  required boolean not null default true
);

create table if not exists field_mapping (
  id bigserial primary key,
  template_code text not null references template_config(template_code),
  standard_sheet_code text not null,
  raw_header_path text,
  raw_column_letter text,
  standard_field text not null,
  data_type text not null,
  required boolean not null default false,
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
  id bigserial primary key,
  franchise_code text unique,
  franchise_name text not null,
  region_code text references dim_region(region_code),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists ux_dim_franchise_region_name
  on dim_franchise(region_code, franchise_name);

create table if not exists dim_site (
  id bigserial primary key,
  site_code text unique,
  site_name text not null,
  franchise_id bigint references dim_franchise(id),
  city text,
  district text,
  status text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
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
  id bigserial primary key,
  file_id bigint references source_file(id),
  period_month text not null references dim_month(period_month),
  region_code text not null references dim_region(region_code),
  franchise_id bigint references dim_franchise(id),
  franchise_name text not null,
  daily_over_5000_flag boolean,
  outbound_tickets numeric,
  outbound_weight numeric,
  outbound_avg_weight numeric,
  waybill_fee numeric,
  transfer_fee numeric,
  warehouse_fee numeric,
  operation_fee numeric,
  dispatch_fee numeric,
  one_price_rebate numeric,
  outbound_contribution numeric,
  outbound_unit_contribution numeric,
  outbound_kg_contribution numeric,
  inbound_signed_tickets numeric,
  inbound_weight numeric,
  inbound_dispatch_income numeric,
  inbound_dispatch_cost numeric,
  deduction_total numeric,
  inbound_contribution numeric,
  total_contribution numeric,
  outbound_pass_contribution numeric,
  inbound_pass_contribution numeric,
  created_at timestamptz not null default now()
);

create index if not exists idx_fact_franchise_month_period
  on fact_franchise_month(period_month);
create index if not exists idx_fact_franchise_month_rank
  on fact_franchise_month(period_month, total_contribution desc);

create table if not exists fact_site_month (
  id bigserial primary key,
  file_id bigint references source_file(id),
  period_month text not null references dim_month(period_month),
  region_code text not null references dim_region(region_code),
  franchise_id bigint references dim_franchise(id),
  franchise_name text not null,
  site_id bigint references dim_site(id),
  site_name text not null,
  site_status text,
  daily_over_5000_flag boolean,
  outbound_tickets numeric,
  outbound_weight numeric,
  outbound_contribution numeric,
  inbound_signed_tickets numeric,
  inbound_contribution numeric,
  deduction_total numeric,
  total_contribution numeric,
  created_at timestamptz not null default now()
);

create index if not exists idx_fact_site_month_period
  on fact_site_month(period_month);
create index if not exists idx_fact_site_month_rank
  on fact_site_month(period_month, total_contribution desc);

create table if not exists fact_contribution_flow (
  id bigserial primary key,
  file_id bigint references source_file(id),
  period_month text not null references dim_month(period_month),
  scope_type text not null,
  region_code text references dim_region(region_code),
  franchise_id bigint references dim_franchise(id),
  franchise_name text,
  destination_province text,
  weight_band text references dim_weight_band(weight_band),
  ticket_count numeric,
  ticket_share numeric,
  weight_total numeric,
  four_fee_total numeric,
  settlement_price numeric,
  dispatch_fee numeric,
  contribution_total numeric,
  unit_four_fee numeric,
  unit_settlement_price numeric,
  unit_dispatch_fee numeric,
  unit_contribution numeric,
  kg_contribution numeric,
  created_at timestamptz not null default now()
);

create index if not exists idx_fact_contribution_flow_heatmap
  on fact_contribution_flow(period_month, scope_type, destination_province, weight_band);

create table if not exists fact_one_price_summary (
  id bigserial primary key,
  file_id bigint references source_file(id),
  period_month text not null references dim_month(period_month),
  franchise_id bigint references dim_franchise(id),
  franchise_name text not null,
  ticket_count numeric,
  daily_ticket_count numeric,
  billed_weight numeric,
  avg_weight numeric,
  four_fee numeric,
  settlement_price numeric,
  dispatch_fee numeric,
  contribution_total numeric,
  unit_contribution numeric,
  kg_contribution numeric,
  created_at timestamptz not null default now()
);

create table if not exists fact_fee_event (
  id bigserial primary key,
  file_id bigint references source_file(id),
  period_month text not null references dim_month(period_month),
  franchise_id bigint references dim_franchise(id),
  franchise_name text,
  site_id bigint references dim_site(id),
  site_name text,
  event_source text not null,
  fee_main_type text,
  fee_sub_type text,
  raw_amount numeric,
  display_amount numeric,
  remark text,
  created_at timestamptz not null default now()
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
  id bigserial primary key,
  rule_code text not null unique,
  rule_name text not null,
  rule_type text not null,
  severity text not null,
  rule_sql text,
  is_active boolean not null default true
);

create table if not exists dim_tag (
  tag_code text primary key,
  tag_name text not null,
  tag_group text not null,
  target_type text not null,
  description text
);

create table if not exists tag_rule (
  id bigserial primary key,
  tag_code text not null references dim_tag(tag_code),
  rule_sql text not null,
  priority integer not null default 100,
  is_active boolean not null default true
);

create table if not exists tag_assignment (
  id bigserial primary key,
  target_type text not null,
  target_id bigint not null,
  period_month text not null references dim_month(period_month),
  tag_code text not null references dim_tag(tag_code),
  source_type text not null default 'auto',
  assigned_at timestamptz not null default now(),
  unique(target_type, target_id, period_month, tag_code)
);

