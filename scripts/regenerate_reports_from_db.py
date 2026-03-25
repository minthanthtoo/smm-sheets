#!/usr/bin/env python3
"""Regenerate Excel reports from DB using template-based filler.

Writes master CSVs into out/<dir>/staging then fills Excel templates from source/<REGION>.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List

from regenerate_templates import regenerate_templates
from db_compat import get_conn, resolve_db_target


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def export_db(db_target: str, staging_dir: Path) -> None:
    conn = get_conn(db_target)
    try:
        products = [dict(r) for r in conn.execute("SELECT * FROM products").fetchall()]
        outlets = [dict(r) for r in conn.execute("SELECT * FROM outlets").fetchall()]

        # sales with region_id for template aggregation
        sales = [dict(r) for r in conn.execute(
            """
            SELECT s.*, t.region_id as region_id
            FROM sales_transactions s
            LEFT JOIN outlets o ON s.outlet_id = o.outlet_id
            LEFT JOIN townships t ON o.township_id = t.township_id
            """
        ).fetchall()]

        # aliases
        aliases_products = [dict(r) for r in conn.execute("SELECT * FROM aliases_products").fetchall()]
        aliases_outlets = [dict(r) for r in conn.execute("SELECT * FROM aliases_outlets").fetchall()]

    finally:
        conn.close()

    # normalize outlet fieldname for templates
    for o in outlets:
        if "township_name" not in o:
            o["township_name"] = o.get("township_name_raw", "")

    write_csv(staging_dir / "master_products.csv", products, [
        "product_id", "product_name", "ml", "packing", "sales_price", "unit_type", "category",
        "source_file", "source_sheet", "source_row",
    ])

    write_csv(staging_dir / "master_outlets.csv", outlets, [
        "outlet_id", "outlet_code", "outlet_name_mm", "outlet_name_en", "outlet_type", "address_full",
        "township_name", "way_code", "contact_phone", "agent_name", "responsible_person", "notes",
        "source_file", "source_sheet", "source_row",
    ])

    write_csv(staging_dir / "master_sales_transactions.csv", sales, [
        "txn_id", "txn_key", "txn_hash", "day_key", "outlet_key", "trader_key",
        "date", "year", "month", "day", "day_label", "period",
        "outlet_id", "customer_id_raw", "outlet_name_raw", "township_name_raw",
        "product_id", "stock_id_raw", "stock_name_raw", "ml_raw", "packing_raw",
        "channel", "voucher_no", "car_no",
        "qty_pack", "qty_bottle", "qty_liter",
        "sale_type_raw", "sale_class_raw", "participation_raw", "parking_fee",
        "source_file", "source_sheet", "source_row",
        "region_id",
    ])

    write_csv(staging_dir / "aliases_products.csv", aliases_products, [
        "alias_name", "alias_ml", "alias_packing", "canonical_product_id",
        "canonical_name", "canonical_ml", "canonical_packing", "notes",
    ])
    write_csv(staging_dir / "aliases_outlets.csv", aliases_outlets, [
        "alias_name", "alias_township", "canonical_outlet_id",
        "canonical_name", "canonical_township", "notes",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="db/app.db")
    parser.add_argument("--out-dir", default="out")
    parser.add_argument("--root-dir", default=".")
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()

    root = Path(args.root_dir).resolve()
    out_dir = (root / args.out_dir).resolve()
    staging_dir = out_dir / "staging"
    db_target = resolve_db_target(root, args.db)

    export_db(db_target, staging_dir)
    regenerate_templates(root, root / "in", out_dir, clean_out=not args.no_clean)


if __name__ == "__main__":
    main()
