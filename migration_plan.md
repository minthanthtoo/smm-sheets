# SMM App Migration Plan (v1)

This plan migrates the Excel-based workflow into a centralized application while keeping current reporting intact.

## Phase 0: Preparation
1. Freeze a baseline month of Excel files for reference.
2. Confirm target outputs that must match Excel exactly (reports to reproduce first).
3. Define canonical master data lists: Region, Township, Outlet, Product, Route.

## Phase 1: Data Dictionary and ID Strategy
1. Decide ID generation rules:
- product_id = Stock ID when available.
- outlet_id = hashed normalized name + township + phone (manual override allowed).
- route_id = region + van + way.
2. Build normalization dictionaries:
- township names per region.
- product name aliases.
- outlet name aliases.
3. Define unit conversion rules:
- pack_size, bottle_size_ml, liters_per_pack.

## Phase 2: Import Pipelines
1. Product master import
- Source: Table sheets + SKU Summary sheets.
- Resolve duplicates by Stock ID, then name+ml+packing.

2. Outlet master import
- Source: Outlet List sheets + Individual Sales sheets.
- Merge by normalized name + township + phone.

3. Route/Van import
- Source: Way Plan + Outlet Summary sheets.
- Map way codes and route names per region.

4. Transaction import
- Source: DailySales sheets.
- Map outlet, product, route, and channel.

5. Competition import (optional)
- Source: Competition Information sheet.

## Phase 3: Validation and Reconciliation
1. Report totals for baseline month in app.
2. Compare against Excel totals for:
- Individual Sales
- Township Summary
- SKU Summary
- Van Wise SKU
3. Investigate and fix mismatches:
- missing outlet or product ID
- inconsistent township names
- unit conversion issues

## Phase 4: Report Parity
1. Generate app reports that match Excel layouts.
2. Export to Excel format for side-by-side comparison.
3. Obtain sign-off from business users.

## Phase 5: Transition
1. Data entry moves to app (DailySales + PJP + Outlet updates).
2. Excel becomes read-only output.
3. Monitor for 1-2 months with dual reporting.

## Phase 6: Optimization
1. Add dashboards and role-based access.
2. Add scheduled exports.
3. Automate alerts for anomalies (missing data, sudden drops, etc.).

---

## Data Quality Checklist
- Orphan transactions (no matching outlet or product)
- Duplicate outlets under different spellings
- Mixed units in same field
- Transactions with missing date or township

---

## Deliverables
- Canonical database schema
- Import scripts with logs
- Report templates that match Excel outputs
- Migration reconciliation report

