-- SMM App schema v1 (history + auditability)

CREATE TABLE IF NOT EXISTS outlet_history (
  outlet_history_id TEXT PRIMARY KEY,
  outlet_id TEXT NOT NULL,
  outlet_name_mm TEXT,
  outlet_name_en TEXT,
  outlet_type TEXT,
  category TEXT,
  route_id TEXT,
  contact_phone TEXT,
  address_full TEXT,
  responsible_person TEXT,
  agent_name TEXT,
  status TEXT DEFAULT 'active',
  effective_from DATE NOT NULL,
  effective_to DATE,
  created_at TEXT,
  created_by TEXT,
  FOREIGN KEY (outlet_id) REFERENCES outlets(outlet_id),
  FOREIGN KEY (route_id) REFERENCES routes(route_id)
);

CREATE INDEX IF NOT EXISTS ix_outlet_history_outlet_effective
  ON outlet_history (outlet_id, effective_from);

CREATE TABLE IF NOT EXISTS product_history (
  product_history_id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  sales_price NUMERIC,
  pack_size INTEGER,
  ml_per_bottle INTEGER,
  unit_type TEXT,
  category TEXT,
  effective_from DATE NOT NULL,
  effective_to DATE,
  created_at TEXT,
  created_by TEXT,
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX IF NOT EXISTS ix_product_history_product_effective
  ON product_history (product_id, effective_from);

CREATE TABLE IF NOT EXISTS route_history (
  route_history_id TEXT PRIMARY KEY,
  route_id TEXT NOT NULL,
  region_id TEXT,
  van_id TEXT,
  way_code TEXT,
  route_name TEXT,
  township_id TEXT,
  effective_from DATE NOT NULL,
  effective_to DATE,
  created_at TEXT,
  created_by TEXT,
  FOREIGN KEY (route_id) REFERENCES routes(route_id),
  FOREIGN KEY (region_id) REFERENCES regions(region_id),
  FOREIGN KEY (township_id) REFERENCES townships(township_id)
);

CREATE INDEX IF NOT EXISTS ix_route_history_route_effective
  ON route_history (route_id, effective_from);

CREATE TABLE IF NOT EXISTS township_history (
  township_history_id TEXT PRIMARY KEY,
  township_id TEXT NOT NULL,
  township_name TEXT,
  township_name_en TEXT,
  region_id TEXT,
  effective_from DATE NOT NULL,
  effective_to DATE,
  created_at TEXT,
  created_by TEXT,
  FOREIGN KEY (township_id) REFERENCES townships(township_id),
  FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

CREATE INDEX IF NOT EXISTS ix_township_history_township_effective
  ON township_history (township_id, effective_from);

CREATE TABLE IF NOT EXISTS outlet_merge_map (
  merge_id TEXT PRIMARY KEY,
  from_outlet_id TEXT NOT NULL,
  to_outlet_id TEXT NOT NULL,
  merged_at TEXT NOT NULL,
  reason TEXT,
  FOREIGN KEY (from_outlet_id) REFERENCES outlets(outlet_id),
  FOREIGN KEY (to_outlet_id) REFERENCES outlets(outlet_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
  audit_id TEXT PRIMARY KEY,
  table_name TEXT NOT NULL,
  record_id TEXT,
  action TEXT NOT NULL,
  old_values TEXT,
  new_values TEXT,
  changed_at TEXT NOT NULL,
  changed_by TEXT
);
