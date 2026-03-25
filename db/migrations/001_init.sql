-- SMM App schema v1 (core tables)
-- Compatible with Postgres and SQLite (no vendor-specific types).

CREATE TABLE IF NOT EXISTS regions (
  region_id TEXT PRIMARY KEY,
  region_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS townships (
  township_id TEXT PRIMARY KEY,
  township_name TEXT NOT NULL,
  township_name_en TEXT,
  region_id TEXT NOT NULL,
  aliases TEXT,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER,
  FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

CREATE TABLE IF NOT EXISTS products (
  product_id TEXT PRIMARY KEY,
  product_name TEXT NOT NULL,
  ml TEXT,
  packing TEXT,
  unit_type TEXT,
  sales_price NUMERIC,
  brand TEXT,
  category TEXT,
  pack_size INTEGER,
  ml_per_bottle INTEGER,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER
);

CREATE TABLE IF NOT EXISTS outlets (
  outlet_id TEXT PRIMARY KEY,
  outlet_code TEXT,
  outlet_name_mm TEXT,
  outlet_name_en TEXT,
  outlet_type TEXT,
  address_full TEXT,
  township_id TEXT,
  township_name_raw TEXT,
  way_code TEXT,
  contact_name_mm TEXT,
  contact_name_en TEXT,
  contact_phone TEXT,
  responsible_person TEXT,
  agent_name TEXT,
  category TEXT,
  notes TEXT,
  active INTEGER DEFAULT 1,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER,
  FOREIGN KEY (township_id) REFERENCES townships(township_id)
);

CREATE TABLE IF NOT EXISTS routes (
  route_id TEXT PRIMARY KEY,
  region_id TEXT,
  van_id TEXT,
  way_code TEXT,
  route_name TEXT,
  township_id TEXT,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER,
  FOREIGN KEY (region_id) REFERENCES regions(region_id),
  FOREIGN KEY (township_id) REFERENCES townships(township_id)
);

CREATE TABLE IF NOT EXISTS route_outlets (
  route_id TEXT NOT NULL,
  outlet_id TEXT NOT NULL,
  category TEXT,
  start_date DATE,
  end_date DATE,
  PRIMARY KEY (route_id, outlet_id, start_date),
  FOREIGN KEY (route_id) REFERENCES routes(route_id),
  FOREIGN KEY (outlet_id) REFERENCES outlets(outlet_id)
);

CREATE TABLE IF NOT EXISTS sales_transactions (
  txn_id TEXT PRIMARY KEY,
  txn_key TEXT NOT NULL,
  txn_hash TEXT NOT NULL,
  day_key TEXT,
  outlet_key TEXT,
  trader_key TEXT,
  date DATE,
  year INTEGER,
  month INTEGER,
  day INTEGER,
  day_label TEXT,
  period TEXT,
  outlet_id TEXT,
  route_id TEXT,
  customer_id_raw TEXT,
  outlet_name_raw TEXT,
  township_name_raw TEXT,
  address_raw TEXT,
  product_id TEXT,
  stock_id_raw TEXT,
  stock_name_raw TEXT,
  ml_raw TEXT,
  packing_raw TEXT,
  channel TEXT,
  voucher_no TEXT,
  car_no TEXT,
  qty_pack NUMERIC,
  qty_bottle NUMERIC,
  qty_liter NUMERIC,
  sale_type_raw TEXT,
  sale_class_raw TEXT,
  participation_raw TEXT,
  parking_fee NUMERIC,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER,
  FOREIGN KEY (outlet_id) REFERENCES outlets(outlet_id),
  FOREIGN KEY (route_id) REFERENCES routes(route_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS sales_financials (
  txn_hash TEXT PRIMARY KEY,
  unit_rate NUMERIC,
  gross_amount NUMERIC,
  opening_balance NUMERIC,
  old_price_discount NUMERIC,
  commission NUMERIC,
  discount NUMERIC,
  transport_discount NUMERIC,
  transport_add NUMERIC,
  payment_date_1 DATE,
  receivable_1 NUMERIC,
  payment_date_2 DATE,
  receivable_2 NUMERIC,
  payment_date_3 DATE,
  receivable_3 NUMERIC,
  payment_date_4 DATE,
  receivable_4 NUMERIC,
  outstanding_balance NUMERIC,
  FOREIGN KEY (txn_hash) REFERENCES sales_transactions(txn_hash) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pjp_plans (
  plan_id TEXT PRIMARY KEY,
  date DATE NOT NULL,
  route_id TEXT NOT NULL,
  planned_a INTEGER,
  planned_b INTEGER,
  planned_c INTEGER,
  planned_d INTEGER,
  planned_s INTEGER,
  total_planned INTEGER,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER,
  FOREIGN KEY (route_id) REFERENCES routes(route_id)
);

CREATE TABLE IF NOT EXISTS competition_entries (
  competition_id TEXT PRIMARY KEY,
  region_id TEXT,
  township_id TEXT,
  company_name TEXT,
  distributor_name TEXT,
  product_name TEXT,
  size_ml TEXT,
  packing TEXT,
  landing_price NUMERIC,
  selling_price NUMERIC,
  margin NUMERIC,
  freight_cost NUMERIC,
  promo_cost NUMERIC,
  notes TEXT,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER,
  FOREIGN KEY (region_id) REFERENCES regions(region_id),
  FOREIGN KEY (township_id) REFERENCES townships(township_id)
);

CREATE TABLE IF NOT EXISTS targets_followups (
  target_id TEXT PRIMARY KEY,
  outlet_id TEXT,
  year INTEGER,
  month INTEGER,
  target_value NUMERIC,
  follow_up_notes TEXT,
  source_file TEXT,
  source_sheet TEXT,
  source_row INTEGER,
  FOREIGN KEY (outlet_id) REFERENCES outlets(outlet_id)
);

CREATE TABLE IF NOT EXISTS aliases_products (
  alias_name TEXT NOT NULL,
  alias_ml TEXT,
  alias_packing TEXT,
  canonical_product_id TEXT,
  canonical_name TEXT,
  canonical_ml TEXT,
  canonical_packing TEXT,
  notes TEXT,
  PRIMARY KEY (alias_name, alias_ml, alias_packing),
  FOREIGN KEY (canonical_product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS aliases_outlets (
  alias_name TEXT NOT NULL,
  alias_township TEXT,
  canonical_outlet_id TEXT,
  canonical_name TEXT,
  canonical_township TEXT,
  notes TEXT,
  PRIMARY KEY (alias_name, alias_township),
  FOREIGN KEY (canonical_outlet_id) REFERENCES outlets(outlet_id)
);

CREATE TABLE IF NOT EXISTS ingested_days (
  day_key TEXT PRIMARY KEY,
  txn_count INTEGER,
  unique_outlets INTEGER,
  unique_traders INTEGER
);

CREATE TABLE IF NOT EXISTS ingested_outlets (
  outlet_key TEXT PRIMARY KEY,
  txn_count INTEGER,
  first_day TEXT,
  last_day TEXT
);

CREATE TABLE IF NOT EXISTS ingested_traders (
  trader_key TEXT PRIMARY KEY,
  txn_count INTEGER,
  first_day TEXT,
  last_day TEXT
);
