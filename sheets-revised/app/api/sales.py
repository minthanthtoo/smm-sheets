from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.db import get_conn, row_to_dict
from app.core.utils import hash_txn, today_iso, to_num
from app.services.lookup import get_outlet_route_as_of, get_product_meta

router = APIRouter(prefix="/api")


@router.get("/sales")
def sales(date: str):
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT s.*, o.outlet_name_mm, o.outlet_name_en, p.product_name, p.ml
            FROM sales_transactions s
            LEFT JOIN outlets o ON s.outlet_id = o.outlet_id
            LEFT JOIN products p ON s.product_id = p.product_id
            WHERE s.date = ?
            ORDER BY s.source_row
            """,
            (date,),
        ).fetchall()
        return JSONResponse({"date": date, "rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.get("/sales/sku_breakdown")
def sales_sku_breakdown(date: str | None = None, start: str | None = None, end: str | None = None):
    if not date and not (start and end):
        raise HTTPException(status_code=400, detail="date or start/end is required")
    where = "s.date = ?"
    params: List[Any] = [date]
    if start and end:
        where = "s.date BETWEEN ? AND ?"
        params = [start, end]
    conn = get_conn()
    try:
        rows = conn.execute(
            f"""
            SELECT s.product_id, p.product_name,
                   COALESCE(SUM(s.qty_pack), 0) AS total_pack,
                   COALESCE(SUM(s.qty_bottle), 0) AS total_bottle,
                   COALESCE(SUM(s.qty_liter), 0) AS total_liter,
                   COUNT(*) AS txn_count
            FROM sales_transactions s
            LEFT JOIN products p ON s.product_id = p.product_id
            WHERE {where}
            GROUP BY s.product_id, p.product_name
            ORDER BY total_liter DESC
            """,
            params,
        ).fetchall()
        return JSONResponse({
            "date": date,
            "start": start,
            "end": end,
            "rows": [row_to_dict(r) for r in rows],
        })
    finally:
        conn.close()


@router.get("/sales/outlet_performance")
def sales_outlet_performance(date: str | None = None, start: str | None = None, end: str | None = None):
    if not date and not (start and end):
        raise HTTPException(status_code=400, detail="date or start/end is required")
    where = "s.date = ?"
    params: List[Any] = [date]
    if start and end:
        where = "s.date BETWEEN ? AND ?"
        params = [start, end]
    conn = get_conn()
    try:
        rows = conn.execute(
            f"""
            SELECT s.outlet_id, o.outlet_name_mm, o.outlet_name_en, o.outlet_type,
                   COALESCE(SUM(s.qty_pack), 0) AS total_pack,
                   COALESCE(SUM(s.qty_bottle), 0) AS total_bottle,
                   COALESCE(SUM(s.qty_liter), 0) AS total_liter,
                   COUNT(*) AS txn_count
            FROM sales_transactions s
            LEFT JOIN outlets o ON s.outlet_id = o.outlet_id
            WHERE {where}
            GROUP BY s.outlet_id, o.outlet_name_mm, o.outlet_name_en, o.outlet_type
            ORDER BY total_liter DESC
            """,
            params,
        ).fetchall()
        return JSONResponse({
            "date": date,
            "start": start,
            "end": end,
            "rows": [row_to_dict(r) for r in rows],
        })
    finally:
        conn.close()


@router.get("/sales/route_performance")
def sales_route_performance(date: str | None = None, start: str | None = None, end: str | None = None):
    if not date and not (start and end):
        raise HTTPException(status_code=400, detail="date or start/end is required")
    where = "s.date = ?"
    params: List[Any] = [date]
    if start and end:
        where = "s.date BETWEEN ? AND ?"
        params = [start, end]
    conn = get_conn()
    try:
        rows = conn.execute(
            f"""
            SELECT s.route_id, r.route_name, r.van_id, r.way_code,
                   COALESCE(SUM(s.qty_pack), 0) AS total_pack,
                   COALESCE(SUM(s.qty_bottle), 0) AS total_bottle,
                   COALESCE(SUM(s.qty_liter), 0) AS total_liter,
                   COUNT(*) AS txn_count
            FROM sales_transactions s
            LEFT JOIN routes r ON s.route_id = r.route_id
            WHERE {where}
            GROUP BY s.route_id, r.route_name, r.van_id, r.way_code
            ORDER BY total_liter DESC
            """,
            params,
        ).fetchall()
        return JSONResponse({
            "date": date,
            "start": start,
            "end": end,
            "rows": [row_to_dict(r) for r in rows],
        })
    finally:
        conn.close()


@router.post("/sales")
async def create_sales(request: Request):
    payload = await request.json()
    rows = payload if isinstance(payload, list) else [payload]
    conn = get_conn()
    try:
        inserted = 0
        duplicates = 0
        for r in rows:
            txn_id = r.get("txn_id") or f"txn_{uuid.uuid4().hex}"
            date = r.get("date") or today_iso()
            outlet_id = r.get("outlet_id")
            product_id = r.get("product_id")
            route_id = r.get("route_id")
            voucher = r.get("voucher_no") or ""
            car_no = r.get("car_no") or ""
            channel = r.get("channel") or ""
            sale_type = r.get("sale_type_raw") or ""
            if not outlet_id or not product_id:
                raise HTTPException(status_code=400, detail="outlet_id and product_id are required")

            qty_pack = to_num(r.get("qty_pack"))
            qty_bottle = to_num(r.get("qty_bottle"))
            qty_liter = r.get("qty_liter")
            if qty_pack < 0 or qty_bottle < 0:
                raise HTTPException(status_code=400, detail="quantities must be non-negative")

            if qty_liter in (None, ""):
                meta = get_product_meta(conn, product_id, date)
                pack_size = to_num(meta.get("pack_size"))
                ml_per_bottle = to_num(meta.get("ml_per_bottle"))
                if pack_size and ml_per_bottle:
                    total_bottles = qty_pack * pack_size + qty_bottle
                    qty_liter = (total_bottles * ml_per_bottle) / 1000.0
                else:
                    qty_liter = 0.0
            else:
                qty_liter = to_num(qty_liter)

            if not route_id:
                route_id = get_outlet_route_as_of(conn, outlet_id, date)
            key_parts = [date, outlet_id or "", product_id or "", voucher, car_no, channel, sale_type]
            txn_key = r.get("txn_key") or "|".join(key_parts)
            txn_hash = r.get("txn_hash") or hash_txn(key_parts + [str(qty_pack), str(qty_bottle), str(qty_liter)])

            existing = conn.execute(
                "SELECT 1 FROM sales_transactions WHERE txn_hash = ?",
                (txn_hash,),
            ).fetchone()
            if existing:
                duplicates += 1
                continue

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
                (
                    txn_id,
                    txn_key,
                    txn_hash,
                    date,
                    outlet_id or "",
                    outlet_id or "",
                    date,
                    None,
                    None,
                    None,
                    r.get("day_label"),
                    r.get("period"),
                    outlet_id,
                    route_id,
                    r.get("customer_id_raw"),
                    r.get("outlet_name_raw"),
                    r.get("township_name_raw"),
                    r.get("address_raw"),
                    product_id,
                    r.get("stock_id_raw"),
                    r.get("stock_name_raw"),
                    r.get("ml_raw"),
                    r.get("packing_raw"),
                    channel,
                    voucher,
                    car_no,
                    qty_pack,
                    qty_bottle,
                    qty_liter,
                    sale_type,
                    r.get("sale_class_raw"),
                    r.get("participation_raw"),
                    r.get("parking_fee"),
                    "app",
                    "daily-sales",
                    None,
                ),
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok", "count": len(rows), "inserted": inserted, "duplicates": duplicates})
