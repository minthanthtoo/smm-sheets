#!/usr/bin/env python3
"""Migrate Excel inputs into SQLite/Postgres DB with history tables.

Usage:
  python3 scripts/db_init.py --db db/app.db
  python3 scripts/migrate_from_excel.py --in-dir in --db db/app.db
  python3 scripts/migrate_from_excel.py --in-dir in/MTL --db db/app.db --region MTL
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from incremental_ingest import iter_input_files, process_files
from etl_load_sources import infer_region_id, norm_key
from db_compat import get_conn, resolve_db_target


def iso_date(value) -> str:
    if value in (None, ""):
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def normalize_value(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


def parse_date_value(value):
    if value in (None, ""):
        return None
    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            return None
    if isinstance(value, str):
        try:
            return dt.datetime.fromisoformat(value).date()
        except Exception:
            return None
    return None


def normalize_int(value, *, fallback_date=None, part: str | None = None):
    if value in (None, ""):
        if fallback_date and part:
            return getattr(fallback_date, part, None)
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if hasattr(value, "date"):
        try:
            d = value.date()
            return getattr(d, part, None) if part else None
        except Exception:
            return None
    if isinstance(value, str):
        if value.isdigit():
            try:
                return int(value)
            except Exception:
                return None
        d = parse_date_value(value)
        if d and part:
            return getattr(d, part, None)
    return None


def today_iso() -> str:
    return dt.date.today().isoformat()


def ensure_region(conn, region_id: str):
    conn.execute(
        """
        INSERT INTO regions (region_id, region_name)
        VALUES (?, ?)
        ON CONFLICT (region_id) DO NOTHING
        """,
        (region_id, region_id),
    )


def parse_pack_size(packing: str) -> int | None:
    if not packing:
        return None
    try:
        return int(float(str(packing).strip()))
    except Exception:
        return None


def earliest_dates_by_key(rows: List[dict], key: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in rows:
        rid = row.get(key)
        if not rid:
            continue
        d = iso_date(row.get("date"))
        if not d:
            continue
        if rid not in out or d < out[rid]:
            out[rid] = d
    return out


def migrate(in_dir: Path, db_target: str, region_filter: str | None) -> None:
    files = iter_input_files(in_dir)
    if region_filter:
        region_filter = region_filter.upper()
        files = [p for p in files if infer_region_id(p.name).upper() == region_filter]

    products, outlets, townships, routes, sales_rows, financial_rows, pjp_rows, route_outlet_rows = process_files(files)

    conn = get_conn(db_target)
    try:
        if conn.flavor == "sqlite":
            conn.execute("PRAGMA foreign_keys = ON")

        # regions
        for p in files:
            ensure_region(conn, infer_region_id(p.name))

        # townships
        for t in townships.values():
            township_id = t.get("township_id")
            if not township_id:
                continue
            conn.execute(
                """
                INSERT INTO townships (
                  township_id, township_name, township_name_en, region_id, source_file
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (township_id) DO NOTHING
                """,
                (
                    township_id,
                    t.get("township_name"),
                    t.get("township_name_en"),
                    t.get("region_id"),
                    t.get("source_file"),
                ),
            )

        # lookup for township ids
        township_id_by_key: Dict[Tuple[str, str], str] = {}
        for t in townships.values():
            township_id = t.get("township_id")
            if not township_id:
                continue
            region_id = t.get("region_id") or ""
            name = t.get("township_name") or ""
            if region_id and name:
                township_id_by_key[(region_id, norm_key(name))] = township_id

        # routes
        route_id_by_key: Dict[Tuple[str, str], str] = {}
        for r in routes.values():
            route_id = r.get("route_id")
            if not route_id:
                continue
            conn.execute(
                """
                INSERT INTO routes (
                  route_id, region_id, van_id, way_code, route_name, source_file
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (route_id) DO NOTHING
                """,
                (
                    route_id,
                    r.get("region_id"),
                    r.get("van_id"),
                    r.get("way_code"),
                    r.get("route_name"),
                    r.get("source_file"),
                ),
            )
            region_id = r.get("region_id") or ""
            way_code = r.get("way_code") or ""
            if region_id and way_code:
                route_id_by_key[(region_id, norm_key(way_code))] = route_id

        # products
        for p in products.values():
            product_id = p.get("product_id")
            product_name = (p.get("product_name") or "").strip() if isinstance(p.get("product_name"), str) else p.get("product_name")
            if not product_id or not product_name:
                continue
            conn.execute(
                """
                INSERT INTO products (
                  product_id, product_name, ml, packing, sales_price, unit_type, category,
                  source_file, source_sheet, source_row
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (product_id) DO NOTHING
                """,
                (
                    product_id,
                    product_name,
                    p.get("ml"),
                    p.get("packing"),
                    p.get("sales_price"),
                    p.get("unit_type"),
                    p.get("category"),
                    p.get("source_file"),
                    p.get("source_sheet"),
                    p.get("source_row"),
                ),
            )

        # outlets
        for o in outlets.values():
            outlet_id = o.get("outlet_id")
            if not outlet_id:
                continue
            township_name = o.get("township_name") or ""
            township_id = None
            # infer region from township id mapping
            for (rid, tname), tid in township_id_by_key.items():
                if norm_key(tname) == norm_key(township_name):
                    township_id = tid
                    region_id = rid
                    break
            else:
                region_id = ""
            conn.execute(
                """
                INSERT INTO outlets (
                  outlet_id, outlet_code, outlet_name_mm, outlet_name_en, outlet_type, address_full,
                  township_id, township_name_raw, way_code, contact_phone, agent_name, responsible_person,
                  notes, source_file, source_sheet, source_row
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (outlet_id) DO NOTHING
                """,
                (
                    outlet_id,
                    o.get("outlet_code"),
                    o.get("outlet_name_mm"),
                    o.get("outlet_name_en"),
                    o.get("outlet_type"),
                    o.get("address_full"),
                    township_id,
                    township_name,
                    o.get("way_code"),
                    o.get("contact_phone"),
                    o.get("agent_name"),
                    o.get("responsible_person"),
                    o.get("notes"),
                    o.get("source_file"),
                    o.get("source_sheet"),
                    o.get("source_row"),
                ),
            )

            # if route can be inferred
            way_code = o.get("way_code") or ""
            if way_code and region_id:
                route_id = route_id_by_key.get((region_id, norm_key(way_code)))
            else:
                route_id = None

            # outlet history seed
            effective_from = today_iso()
            if outlet_id:
                conn.execute(
                    """
                    INSERT INTO outlet_history (
                      outlet_history_id, outlet_id, outlet_name_mm, outlet_name_en, outlet_type,
                      category, route_id, contact_phone, address_full, responsible_person, agent_name,
                      status, effective_from, created_at, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (outlet_history_id) DO NOTHING
                    """,
                    (
                        f"outh_{uuid.uuid4().hex}",
                        outlet_id,
                        o.get("outlet_name_mm"),
                        o.get("outlet_name_en"),
                        o.get("outlet_type"),
                        "",
                        route_id,
                        o.get("contact_phone"),
                        o.get("address_full"),
                        o.get("responsible_person"),
                        o.get("agent_name"),
                        "active",
                        effective_from,
                        dt.datetime.utcnow().isoformat(),
                        "migration",
                    ),
                )

        # sales transactions
        for s in sales_rows:
            txn_hash = s.get("txn_hash")
            txn_id = s.get("txn_id") or (f"txn_{txn_hash}" if txn_hash else f"txn_{uuid.uuid4().hex}")
            date_obj = parse_date_value(s.get("date"))
            values = (
                txn_id,
                s.get("txn_key"),
                txn_hash,
                s.get("day_key"),
                s.get("outlet_key"),
                s.get("trader_key"),
                iso_date(s.get("date")),
                normalize_int(s.get("year"), fallback_date=date_obj, part="year"),
                normalize_int(s.get("month"), fallback_date=date_obj, part="month"),
                normalize_int(s.get("day"), fallback_date=date_obj, part="day"),
                s.get("day_label"),
                s.get("period"),
                s.get("outlet_id") or None,
                None,
                s.get("customer_id_raw"),
                s.get("outlet_name_raw"),
                s.get("township_name_raw"),
                s.get("address_raw"),
                s.get("product_id") or None,
                s.get("stock_id_raw"),
                s.get("stock_name_raw"),
                s.get("ml_raw"),
                s.get("packing_raw"),
                s.get("channel"),
                s.get("voucher_no"),
                s.get("car_no"),
                s.get("qty_pack"),
                s.get("qty_bottle"),
                s.get("qty_liter"),
                s.get("sale_type_raw"),
                s.get("sale_class_raw"),
                s.get("participation_raw"),
                s.get("parking_fee"),
                s.get("source_file"),
                s.get("source_sheet"),
                s.get("source_row"),
            )
            values = tuple(normalize_value(v) for v in values)

            conn.execute(
                """
                INSERT INTO sales_transactions (
                  txn_id, txn_key, txn_hash, day_key, outlet_key, trader_key,
                  date, year, month, day, day_label, period,
                  outlet_id, route_id, customer_id_raw, outlet_name_raw, township_name_raw, address_raw,
                  product_id, stock_id_raw, stock_name_raw, ml_raw, packing_raw,
                  channel, voucher_no, car_no,
                  qty_pack, qty_bottle, qty_liter,
                  sale_type_raw, sale_class_raw, participation_raw, parking_fee,
                  source_file, source_sheet, source_row
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (txn_hash) DO NOTHING
                """,
                values,
            )

        # financials
        for f in financial_rows:
            if not f.get("txn_hash"):
                continue
            conn.execute(
                """
                INSERT INTO sales_financials (
                  txn_hash, unit_rate, gross_amount, opening_balance, old_price_discount, commission,
                  discount, transport_discount, transport_add, payment_date_1, receivable_1,
                  payment_date_2, receivable_2, payment_date_3, receivable_3, payment_date_4,
                  receivable_4, outstanding_balance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (txn_hash) DO NOTHING
                """,
                (
                    f.get("txn_hash"),
                    f.get("unit_rate"),
                    f.get("gross_amount"),
                    f.get("opening_balance"),
                    f.get("old_price_discount"),
                    f.get("commission"),
                    f.get("discount"),
                    f.get("transport_discount"),
                    f.get("transport_add"),
                    iso_date(f.get("payment_date_1")),
                    f.get("receivable_1"),
                    iso_date(f.get("payment_date_2")),
                    f.get("receivable_2"),
                    iso_date(f.get("payment_date_3")),
                    f.get("receivable_3"),
                    iso_date(f.get("payment_date_4")),
                    f.get("receivable_4"),
                    f.get("outstanding_balance"),
                ),
            )

        # history seeding (use earliest txn date or today)
        earliest_outlet = earliest_dates_by_key(sales_rows, "outlet_id")
        earliest_product = earliest_dates_by_key(sales_rows, "product_id")

        for oid, d in earliest_outlet.items():
            conn.execute(
                "UPDATE outlet_history SET effective_from = ? WHERE outlet_id = ?",
                (d, oid),
            )

        for p in products.values():
            pid = p.get("product_id")
            pname = (p.get("product_name") or "").strip() if isinstance(p.get("product_name"), str) else p.get("product_name")
            if not pid or not pname:
                continue
            effective_from = earliest_product.get(pid, today_iso())
            pack_size = parse_pack_size(p.get("packing") or "")
            ml = None
            try:
                ml = int(float(p.get("ml"))) if p.get("ml") not in (None, "") else None
            except Exception:
                ml = None
            conn.execute(
                """
                INSERT INTO product_history (
                  product_history_id, product_id, sales_price, pack_size, ml_per_bottle,
                  unit_type, category, effective_from, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (product_history_id) DO NOTHING
                """,
                (
                    f"prh_{uuid.uuid4().hex}",
                    pid,
                    p.get("sales_price"),
                    pack_size,
                    ml,
                    p.get("unit_type"),
                    p.get("category"),
                    effective_from,
                    dt.datetime.utcnow().isoformat(),
                    "migration",
                ),
            )

        for r in routes.values():
            rid = r.get("route_id")
            if not rid:
                continue
            conn.execute(
                """
                INSERT INTO route_history (
                  route_history_id, route_id, region_id, van_id, way_code, route_name,
                  township_id, effective_from, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (route_history_id) DO NOTHING
                """,
                (
                    f"rth_{uuid.uuid4().hex}",
                    rid,
                    r.get("region_id"),
                    r.get("van_id"),
                    r.get("way_code"),
                    r.get("route_name"),
                    None,
                    today_iso(),
                    dt.datetime.utcnow().isoformat(),
                    "migration",
                ),
            )

        # route_outlets
        for ro in route_outlet_rows:
            if not ro.get("route_id") or not ro.get("outlet_id"):
                continue
            start_date = ro.get("start_date") or today_iso()
            conn.execute(
                """
                INSERT INTO route_outlets (
                  route_id, outlet_id, category, start_date, end_date
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (route_id, outlet_id, start_date) DO NOTHING
                """,
                (
                    ro.get("route_id"),
                    ro.get("outlet_id"),
                    ro.get("category"),
                    start_date,
                    ro.get("end_date") or None,
                ),
            )
            conn.execute(
                """
                UPDATE outlet_history
                SET route_id = ?
                WHERE outlet_id = ? AND route_id IS NULL AND effective_to IS NULL
                """,
                (ro.get("route_id"), ro.get("outlet_id")),
            )

        for t in townships.values():
            tid = t.get("township_id")
            if not tid:
                continue
            conn.execute(
                """
                INSERT INTO township_history (
                  township_history_id, township_id, township_name, township_name_en, region_id,
                  effective_from, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (township_history_id) DO NOTHING
                """,
                (
                    f"twh_{uuid.uuid4().hex}",
                    tid,
                    t.get("township_name"),
                    t.get("township_name_en"),
                    t.get("region_id"),
                    today_iso(),
                    dt.datetime.utcnow().isoformat(),
                    "migration",
                ),
            )

        # pjp plans
        for plan in pjp_rows:
            if not plan.get("plan_id"):
                continue
            conn.execute(
                """
                INSERT INTO pjp_plans (
                  plan_id, date, route_id, planned_a, planned_b, planned_c,
                  planned_d, planned_s, total_planned, source_file, source_sheet, source_row
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (plan_id) DO NOTHING
                """,
                (
                    plan.get("plan_id"),
                    plan.get("date"),
                    plan.get("route_id"),
                    plan.get("planned_a"),
                    plan.get("planned_b"),
                    plan.get("planned_c"),
                    plan.get("planned_d"),
                    plan.get("planned_s"),
                    plan.get("total_planned"),
                    plan.get("source_file"),
                    plan.get("source_sheet"),
                    plan.get("source_row"),
                ),
            )

        conn.commit()
    finally:
        conn.close()

    print(f"Migrated {len(files)} files into {db_target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", default="in", help="Input directory with Excel files")
    parser.add_argument("--db", default="db/app.db", help="DB path or Postgres URL")
    parser.add_argument("--region", default=None, help="Optional region filter (e.g., MTL)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    in_dir = (root / args.in_dir).resolve()
    db_target = resolve_db_target(root, args.db)

    migrate(in_dir, db_target, args.region)


if __name__ == "__main__":
    main()
