-- SMM App schema v1 (indexes and constraints)

CREATE UNIQUE INDEX IF NOT EXISTS ux_sales_transactions_txn_hash
  ON sales_transactions (txn_hash);

CREATE INDEX IF NOT EXISTS ix_sales_transactions_date
  ON sales_transactions (date);

CREATE INDEX IF NOT EXISTS ix_sales_transactions_outlet
  ON sales_transactions (outlet_id);

CREATE INDEX IF NOT EXISTS ix_sales_transactions_product
  ON sales_transactions (product_id);

CREATE INDEX IF NOT EXISTS ix_sales_transactions_route
  ON sales_transactions (route_id);

CREATE INDEX IF NOT EXISTS ix_sales_transactions_channel
  ON sales_transactions (channel);

CREATE INDEX IF NOT EXISTS ix_sales_transactions_township_raw
  ON sales_transactions (township_name_raw);

CREATE INDEX IF NOT EXISTS ix_outlets_township
  ON outlets (township_id);

CREATE INDEX IF NOT EXISTS ix_outlets_name_mm
  ON outlets (outlet_name_mm);

CREATE INDEX IF NOT EXISTS ix_products_name_ml_packing
  ON products (product_name, ml, packing);

CREATE INDEX IF NOT EXISTS ix_routes_region_van_way
  ON routes (region_id, van_id, way_code);

CREATE INDEX IF NOT EXISTS ix_pjp_plans_route_date
  ON pjp_plans (route_id, date);

CREATE INDEX IF NOT EXISTS ix_competition_region_township
  ON competition_entries (region_id, township_id);

CREATE INDEX IF NOT EXISTS ix_aliases_products_canonical
  ON aliases_products (canonical_product_id);

CREATE INDEX IF NOT EXISTS ix_aliases_outlets_canonical
  ON aliases_outlets (canonical_outlet_id);
