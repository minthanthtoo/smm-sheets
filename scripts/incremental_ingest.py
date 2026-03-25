#!/usr/bin/env python3
"""Incremental ingest with de-dup and master canonical store.

- Scans in/ for .xlsx/.xlsm (recursive)
- Processes only new/changed files (by sha256)
- Upserts into master CSVs with de-dup
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional

import openpyxl

from etl_load_sources import (
    infer_region_id,
    norm,
    norm_key,
    parse_daily_sales_sheet,
    parse_outlet_list_sheet,
    parse_table_sheet,
)


MASTER_FILES = {
    "products": "master_products.csv",
    "outlets": "master_outlets.csv",
    "townships": "master_townships.csv",
    "routes": "master_routes.csv",
    "sales": "master_sales_transactions.csv",
    "financials": "master_sales_financials.csv",
    "pjp_plans": "master_pjp_plans.csv",
    "route_outlets": "master_route_outlets.csv",
}


FIELDNAMES = {
    "products": [
        "product_id", "product_name", "ml", "packing", "sales_price", "unit_type", "category",
        "source_file", "source_sheet", "source_row",
    ],
    "outlets": [
        "outlet_id", "outlet_code", "outlet_name_mm", "outlet_name_en", "outlet_type", "address_full",
        "township_name", "way_code", "contact_phone", "agent_name", "responsible_person", "notes",
        "source_file", "source_sheet", "source_row",
    ],
    "townships": [
        "township_id", "township_name", "township_name_en", "region_id", "source_file",
    ],
    "routes": [
        "route_id", "region_id", "van_id", "way_code", "route_name", "source_file",
    ],
    "sales": [
        "txn_id", "txn_key", "txn_hash",
        "day_key", "outlet_key", "trader_key",
        "date", "year", "month", "day", "day_label", "period",
        "outlet_id", "customer_id_raw", "outlet_name_raw", "township_name_raw",
        "product_id", "stock_id_raw", "stock_name_raw", "ml_raw", "packing_raw",
        "channel", "voucher_no", "car_no",
        "qty_pack", "qty_bottle", "qty_liter",
        "sale_type_raw", "sale_class_raw", "participation_raw", "parking_fee",
        "source_file", "source_sheet", "source_row",
    ],
    "financials": [
        "txn_key", "txn_hash",
        "unit_rate", "gross_amount", "opening_balance", "old_price_discount", "commission",
        "discount", "transport_discount", "transport_add", "payment_date_1", "receivable_1",
        "payment_date_2", "receivable_2", "payment_date_3", "receivable_3", "payment_date_4",
        "receivable_4", "outstanding_balance",
    ],
    "pjp_plans": [
        "plan_id", "date", "route_id", "planned_a", "planned_b", "planned_c",
        "planned_d", "planned_s", "total_planned", "source_file", "source_sheet", "source_row",
    ],
    "route_outlets": [
        "route_id", "outlet_id", "category", "start_date", "end_date", "source_file", "source_sheet", "source_row",
    ],
    "ingested_days": [
        "day_key", "txn_count", "unique_outlets", "unique_traders",
    ],
    "ingested_outlets": [
        "outlet_key", "txn_count", "first_day", "last_day",
    ],
    "ingested_traders": [
        "trader_key", "txn_count", "first_day", "last_day",
    ],
    "aliases_products": [
        "alias_name", "alias_ml", "alias_packing", "canonical_name", "canonical_ml", "canonical_packing", "notes",
    ],
    "aliases_outlets": [
        "alias_name", "alias_township", "canonical_name", "canonical_township", "notes",
    ],
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> Dict:
    if not path.exists():
        return {"files": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, manifest: Dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def iter_input_files(in_dir: Path) -> List[Path]:
    files = []
    for p in in_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm"}:
            files.append(p)
    return sorted(files)


def day_key_from_row(row: Dict[str, str]) -> str:
    date_val = row.get("date") or ""
    if not date_val:
        y = row.get("year") or ""
        m = row.get("month") or ""
        d = row.get("day") or ""
        date_val = f"{y}-{m}-{d}"
    return norm_key(date_val)


def outlet_key_from_row(row: Dict[str, str]) -> str:
    outlet_name = row.get("outlet_name_raw") or ""
    township = row.get("township_name_raw") or ""
    outlet_id = row.get("outlet_id") or ""
    if outlet_name or township:
        return norm_key(f"{outlet_name}|{township}")
    if outlet_id:
        return norm_key(outlet_id)
    return ""


def trader_key_from_row(row: Dict[str, str]) -> str:
    cust_id = row.get("customer_id_raw") or ""
    if cust_id:
        return norm_key(cust_id)
    return outlet_key_from_row(row)


def txn_key(row: Dict[str, str]) -> str:
    day_key = day_key_from_row(row)
    trader_key = trader_key_from_row(row)
    voucher = norm_key(row.get("voucher_no"))
    base_parts = [
        day_key,
        trader_key,
        norm_key(row.get("outlet_name_raw")),
        norm_key(row.get("township_name_raw")),
        norm_key(row.get("product_id") or row.get("stock_id_raw") or row.get("stock_name_raw")),
        norm_key(row.get("ml_raw")),
        norm_key(row.get("car_no")),
        norm_key(row.get("channel")),
        norm_key(row.get("sale_type_raw")),
    ]
    if voucher:
        base_parts.insert(1, voucher)
        return "|".join(base_parts)
    # fallback (voucher missing): include quantities to reduce collisions
    fallback = base_parts + [
        str(row.get("qty_pack") or ""),
        str(row.get("qty_bottle") or ""),
        str(row.get("qty_liter") or ""),
    ]
    return "|".join(fallback)


def txn_hash(row: Dict[str, str]) -> str:
    parts = [
        txn_key(row),
        str(row.get("qty_pack") or ""),
        str(row.get("qty_bottle") or ""),
        str(row.get("qty_liter") or ""),
        str(row.get("parking_fee") or ""),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def merge_records(existing: Dict[str, Dict[str, str]], incoming: Dict[str, Dict[str, str]]):
    for key, row in incoming.items():
        if key not in existing:
            existing[key] = row
            continue
        # merge: prefer non-empty values from incoming
        cur = existing[key]
        for k, v in row.items():
            if v not in (None, ""):
                cur[k] = v


def process_files(paths: List[Path]):
    products: Dict[str, dict] = {}
    outlets: Dict[str, dict] = {}
    townships: Dict[str, dict] = {}
    routes: Dict[str, dict] = {}
    sales_rows: List[dict] = []
    financial_rows: List[dict] = []
    pjp_rows: List[dict] = []
    route_outlet_rows: List[dict] = []

    for path in paths:
        region_id = infer_region_id(path.name)
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True, keep_links=False)
        for ws in wb.worksheets:
            title_norm = norm_key(ws.title)
            title_key = re.sub(r"[^a-z0-9]+", "", title_norm)
            if title_key.startswith("table"):
                parse_table_sheet(path, ws, region_id, products, outlets, townships, routes, [])
            elif title_key.startswith("dailysales"):
                parse_daily_sales_sheet(path, ws, region_id, products, outlets, townships, sales_rows, financial_rows)
            elif "outletlist" in title_key:
                parse_outlet_list_sheet(path, ws, region_id, outlets, townships, routes)
            elif "wayplan" in title_key or "wayplay" in title_key or "wayplan" in title_norm or "wayplay" in title_norm:
                from etl_load_sources import parse_way_plan_sheet
                parse_way_plan_sheet(path, ws, region_id, routes, pjp_rows)
            elif "pjpoutlets" in title_key or ("pjp" in title_key and "outlet" in title_key):
                from etl_load_sources import parse_pjp_outlets_sheet
                parse_pjp_outlets_sheet(path, ws, region_id, outlets, routes, route_outlet_rows)
        wb.close()

    # enrich with txn_key/hash
    by_txn_id = {}
    for row in sales_rows:
        row["txn_key"] = txn_key(row)
        row["txn_hash"] = txn_hash(row)
        row["day_key"] = day_key_from_row(row)
        row["outlet_key"] = outlet_key_from_row(row)
        row["trader_key"] = trader_key_from_row(row)
        by_txn_id[row.get("txn_id")] = row

    for fin in financial_rows:
        txn_id = fin.get("txn_id")
        srow = by_txn_id.get(txn_id, {})
        fin["txn_key"] = srow.get("txn_key", "")
        fin["txn_hash"] = srow.get("txn_hash", "")

    return products, outlets, townships, routes, sales_rows, financial_rows, pjp_rows, route_outlet_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", default="in")
    parser.add_argument("--out-dir", default="out")
    parser.add_argument("--full-rebuild", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    in_dir = (root / args.in_dir).resolve()
    out_dir = (root / args.out_dir).resolve()
    staging_dir = out_dir / "staging"
    manifest_path = staging_dir / "manifest.json"

    manifest = load_manifest(manifest_path)
    known = manifest.get("files", {})

    all_files = iter_input_files(in_dir)
    new_files = []
    file_meta = {}

    for p in all_files:
        rel = str(p.relative_to(in_dir))
        h = sha256_file(p)
        meta = {"hash": h, "size": p.stat().st_size, "mtime": int(p.stat().st_mtime)}
        file_meta[rel] = meta
        if args.full_rebuild or rel not in known or known[rel].get("hash") != h:
            new_files.append(p)

    if args.full_rebuild:
        known = {}

    if not new_files and not args.full_rebuild:
        print("No new files to ingest.")
        return

    products, outlets, townships, routes, sales_rows, financial_rows, pjp_rows, route_outlet_rows = process_files(new_files if not args.full_rebuild else all_files)

    # load existing masters
    master_products = {r["product_id"]: r for r in read_csv(staging_dir / MASTER_FILES["products"]) if r.get("product_id")}
    master_outlets = {r["outlet_id"]: r for r in read_csv(staging_dir / MASTER_FILES["outlets"]) if r.get("outlet_id")}
    master_townships = {r["township_id"]: r for r in read_csv(staging_dir / MASTER_FILES["townships"]) if r.get("township_id")}
    master_routes = {r["route_id"]: r for r in read_csv(staging_dir / MASTER_FILES["routes"]) if r.get("route_id")}

    master_sales = {r["txn_key"]: r for r in read_csv(staging_dir / MASTER_FILES["sales"]) if r.get("txn_key")}
    master_fin = {r["txn_key"]: r for r in read_csv(staging_dir / MASTER_FILES["financials"]) if r.get("txn_key")}
    master_pjp = {r["plan_id"]: r for r in read_csv(staging_dir / MASTER_FILES["pjp_plans"]) if r.get("plan_id")}
    master_route_outlets = {(r.get("route_id"), r.get("outlet_id")): r for r in read_csv(staging_dir / MASTER_FILES["route_outlets"]) if r.get("route_id")}

    # merge dictionaries
    merge_records(master_products, products)
    merge_records(master_outlets, outlets)
    merge_records(master_townships, townships)
    merge_records(master_routes, routes)

    for row in sales_rows:
        key = row.get("txn_key")
        if not key:
            continue
        master_sales[key] = row  # upsert by txn_key

    for fin in financial_rows:
        key = fin.get("txn_key")
        if not key:
            continue
        master_fin[key] = fin

    for plan in pjp_rows:
        pid = plan.get("plan_id")
        if not pid:
            continue
        master_pjp[pid] = plan

    for ro in route_outlet_rows:
        key = (ro.get("route_id"), ro.get("outlet_id"))
        if not key[0] or not key[1]:
            continue
        master_route_outlets[key] = ro

    # write masters
    write_csv(staging_dir / MASTER_FILES["products"], list(master_products.values()), FIELDNAMES["products"])
    write_csv(staging_dir / MASTER_FILES["outlets"], list(master_outlets.values()), FIELDNAMES["outlets"])
    write_csv(staging_dir / MASTER_FILES["townships"], list(master_townships.values()), FIELDNAMES["townships"])
    write_csv(staging_dir / MASTER_FILES["routes"], list(master_routes.values()), FIELDNAMES["routes"])
    write_csv(staging_dir / MASTER_FILES["sales"], list(master_sales.values()), FIELDNAMES["sales"])
    write_csv(staging_dir / MASTER_FILES["financials"], list(master_fin.values()), FIELDNAMES["financials"])
    write_csv(staging_dir / MASTER_FILES["pjp_plans"], list(master_pjp.values()), FIELDNAMES["pjp_plans"])
    write_csv(staging_dir / MASTER_FILES["route_outlets"], list(master_route_outlets.values()), FIELDNAMES["route_outlets"])

    # also keep compatibility copies
    write_csv(staging_dir / "products.csv", list(master_products.values()), FIELDNAMES["products"])
    write_csv(staging_dir / "outlets.csv", list(master_outlets.values()), FIELDNAMES["outlets"])
    write_csv(staging_dir / "townships.csv", list(master_townships.values()), FIELDNAMES["townships"])
    write_csv(staging_dir / "routes.csv", list(master_routes.values()), FIELDNAMES["routes"])
    write_csv(staging_dir / "sales_transactions.csv", list(master_sales.values()), FIELDNAMES["sales"])
    write_csv(staging_dir / "sales_financials.csv", list(master_fin.values()), FIELDNAMES["financials"])
    write_csv(staging_dir / "pjp_plans.csv", list(master_pjp.values()), FIELDNAMES["pjp_plans"])
    write_csv(staging_dir / "route_outlets.csv", list(master_route_outlets.values()), FIELDNAMES["route_outlets"])

    # tracking indexes (days / outlets / traders)
    day_counts: Dict[str, dict] = {}
    outlet_counts: Dict[str, dict] = {}
    trader_counts: Dict[str, dict] = {}
    for row in master_sales.values():
        day = row.get("day_key") or ""
        outlet_key = row.get("outlet_key") or ""
        trader_key = row.get("trader_key") or ""

        if day:
            d = day_counts.setdefault(day, {"day_key": day, "txn_count": 0, "outlets": set(), "traders": set()})
            d["txn_count"] += 1
            if outlet_key:
                d["outlets"].add(outlet_key)
            if trader_key:
                d["traders"].add(trader_key)

        if outlet_key:
            o = outlet_counts.setdefault(outlet_key, {"outlet_key": outlet_key, "txn_count": 0, "first_day": day, "last_day": day})
            o["txn_count"] += 1
            if day:
                if not o["first_day"] or day < o["first_day"]:
                    o["first_day"] = day
                if not o["last_day"] or day > o["last_day"]:
                    o["last_day"] = day

        if trader_key:
            t = trader_counts.setdefault(trader_key, {"trader_key": trader_key, "txn_count": 0, "first_day": day, "last_day": day})
            t["txn_count"] += 1
            if day:
                if not t["first_day"] or day < t["first_day"]:
                    t["first_day"] = day
                if not t["last_day"] or day > t["last_day"]:
                    t["last_day"] = day

    days_rows = []
    for d in day_counts.values():
        days_rows.append({
            "day_key": d["day_key"],
            "txn_count": d["txn_count"],
            "unique_outlets": len(d["outlets"]),
            "unique_traders": len(d["traders"]),
        })
    write_csv(staging_dir / "ingested_days.csv", sorted(days_rows, key=lambda x: x["day_key"]), FIELDNAMES["ingested_days"])

    outlets_rows = []
    for o in outlet_counts.values():
        outlets_rows.append({
            "outlet_key": o["outlet_key"],
            "txn_count": o["txn_count"],
            "first_day": o.get("first_day") or "",
            "last_day": o.get("last_day") or "",
        })
    write_csv(staging_dir / "ingested_outlets.csv", sorted(outlets_rows, key=lambda x: x["outlet_key"]), FIELDNAMES["ingested_outlets"])

    traders_rows = []
    for t in trader_counts.values():
        traders_rows.append({
            "trader_key": t["trader_key"],
            "txn_count": t["txn_count"],
            "first_day": t.get("first_day") or "",
            "last_day": t.get("last_day") or "",
        })
    write_csv(staging_dir / "ingested_traders.csv", sorted(traders_rows, key=lambda x: x["trader_key"]), FIELDNAMES["ingested_traders"])

    # ensure alias template files exist (no overwrite)
    alias_prod = staging_dir / "aliases_products.csv"
    alias_out = staging_dir / "aliases_outlets.csv"
    if not alias_prod.exists():
        write_csv(alias_prod, [], FIELDNAMES["aliases_products"])
    if not alias_out.exists():
        write_csv(alias_out, [], FIELDNAMES["aliases_outlets"])

    # update manifest
    now = int(time.time())
    for rel, meta in file_meta.items():
        if args.full_rebuild or rel not in known or known[rel].get("hash") != meta["hash"]:
            meta["ingested_at"] = now
            known[rel] = meta
    manifest["files"] = known
    save_manifest(manifest_path, manifest)

    print(f"Ingested {len(new_files)} new/changed files.")


if __name__ == "__main__":
    main()
