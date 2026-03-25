from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.db import get_conn, row_to_dict

router = APIRouter(prefix="/api/master")


def today_iso() -> str:
    return dt.date.today().isoformat()


@router.get("/regions")
def list_regions():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM regions ORDER BY region_id").fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/regions")
async def upsert_region(request: Request):
    payload = await request.json()
    region_id = payload.get("region_id")
    if not region_id:
        raise HTTPException(status_code=400, detail="region_id is required")

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO regions (region_id, region_name)
            VALUES (?, ?)
            ON CONFLICT (region_id) DO UPDATE SET
              region_name = excluded.region_name
            """,
            (region_id, payload.get("region_name") or region_id),
        )
        conn.commit()
    finally:
        conn.close()
    return JSONResponse({"status": "ok", "region_id": region_id})


@router.get("/townships")
def list_townships(region_id: str | None = None):
    conn = get_conn()
    try:
        if region_id:
            rows = conn.execute(
                "SELECT * FROM townships WHERE region_id = ? ORDER BY township_name",
                (region_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM townships ORDER BY township_name").fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/townships")
async def upsert_township(request: Request):
    payload = await request.json()
    township_id = payload.get("township_id") or f"tsp_{uuid.uuid4().hex}"
    region_id = payload.get("region_id")
    if not region_id:
        raise HTTPException(status_code=400, detail="region_id is required")

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO townships (
              township_id, township_name, township_name_en, region_id, aliases, source_file, source_sheet, source_row
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (township_id) DO UPDATE SET
              township_name = excluded.township_name,
              township_name_en = excluded.township_name_en,
              region_id = excluded.region_id,
              aliases = excluded.aliases,
              source_file = excluded.source_file,
              source_sheet = excluded.source_sheet,
              source_row = excluded.source_row
            """,
            (
                township_id,
                payload.get("township_name"),
                payload.get("township_name_en"),
                region_id,
                payload.get("aliases"),
                "app",
                "master",
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok", "township_id": township_id})


@router.get("/townships/history")
def township_history(township_id: str):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM township_history WHERE township_id = ? ORDER BY effective_from DESC",
            (township_id,),
        ).fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/townships/history")
async def add_township_history(request: Request):
    payload = await request.json()
    township_id = payload.get("township_id")
    if not township_id:
        raise HTTPException(status_code=400, detail="township_id is required")
    effective_from = payload.get("effective_from") or today_iso()

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO township_history (
              township_history_id, township_id, township_name, township_name_en, region_id,
              effective_from, effective_to, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"tsh_{uuid.uuid4().hex}",
                township_id,
                payload.get("township_name"),
                payload.get("township_name_en"),
                payload.get("region_id"),
                effective_from,
                payload.get("effective_to"),
                dt.datetime.utcnow().isoformat(),
                payload.get("created_by", "app"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok"})


@router.get("/routes")
def list_routes(region_id: str | None = None):
    conn = get_conn()
    try:
        if region_id:
            rows = conn.execute(
                "SELECT * FROM routes WHERE region_id = ? ORDER BY route_name",
                (region_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM routes ORDER BY route_name").fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/routes")
async def upsert_route(request: Request):
    payload = await request.json()
    route_id = payload.get("route_id") or f"rte_{uuid.uuid4().hex}"

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO routes (
              route_id, region_id, van_id, way_code, route_name, township_id,
              source_file, source_sheet, source_row
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (route_id) DO UPDATE SET
              region_id = excluded.region_id,
              van_id = excluded.van_id,
              way_code = excluded.way_code,
              route_name = excluded.route_name,
              township_id = excluded.township_id,
              source_file = excluded.source_file,
              source_sheet = excluded.source_sheet,
              source_row = excluded.source_row
            """,
            (
                route_id,
                payload.get("region_id"),
                payload.get("van_id"),
                payload.get("way_code"),
                payload.get("route_name"),
                payload.get("township_id"),
                "app",
                "master",
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok", "route_id": route_id})


@router.get("/routes/history")
def route_history(route_id: str):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM route_history WHERE route_id = ? ORDER BY effective_from DESC",
            (route_id,),
        ).fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/routes/history")
async def add_route_history(request: Request):
    payload = await request.json()
    route_id = payload.get("route_id")
    if not route_id:
        raise HTTPException(status_code=400, detail="route_id is required")
    effective_from = payload.get("effective_from") or today_iso()

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO route_history (
              route_history_id, route_id, region_id, van_id, way_code, route_name, township_id,
              effective_from, effective_to, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"rth_{uuid.uuid4().hex}",
                route_id,
                payload.get("region_id"),
                payload.get("van_id"),
                payload.get("way_code"),
                payload.get("route_name"),
                payload.get("township_id"),
                effective_from,
                payload.get("effective_to"),
                dt.datetime.utcnow().isoformat(),
                payload.get("created_by", "app"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok"})


@router.get("/products")
def list_products():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM products ORDER BY product_name").fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/products")
async def upsert_product(request: Request):
    payload = await request.json()
    product_id = payload.get("product_id") or f"prd_{uuid.uuid4().hex}"

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO products (
              product_id, product_name, ml, packing, unit_type, sales_price, brand, category,
              pack_size, ml_per_bottle, source_file, source_sheet, source_row
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (product_id) DO UPDATE SET
              product_name = excluded.product_name,
              ml = excluded.ml,
              packing = excluded.packing,
              unit_type = excluded.unit_type,
              sales_price = excluded.sales_price,
              brand = excluded.brand,
              category = excluded.category,
              pack_size = excluded.pack_size,
              ml_per_bottle = excluded.ml_per_bottle,
              source_file = excluded.source_file,
              source_sheet = excluded.source_sheet,
              source_row = excluded.source_row
            """,
            (
                product_id,
                payload.get("product_name"),
                payload.get("ml"),
                payload.get("packing"),
                payload.get("unit_type"),
                payload.get("sales_price"),
                payload.get("brand"),
                payload.get("category"),
                payload.get("pack_size"),
                payload.get("ml_per_bottle"),
                "app",
                "master",
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok", "product_id": product_id})


@router.get("/products/history")
def product_history(product_id: str):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM product_history WHERE product_id = ? ORDER BY effective_from DESC",
            (product_id,),
        ).fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/products/history")
async def add_product_history(request: Request):
    payload = await request.json()
    product_id = payload.get("product_id")
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    effective_from = payload.get("effective_from") or today_iso()

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO product_history (
              product_history_id, product_id, sales_price, pack_size, ml_per_bottle,
              unit_type, category, effective_from, effective_to, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"prh_{uuid.uuid4().hex}",
                product_id,
                payload.get("sales_price"),
                payload.get("pack_size"),
                payload.get("ml_per_bottle"),
                payload.get("unit_type"),
                payload.get("category"),
                effective_from,
                payload.get("effective_to"),
                dt.datetime.utcnow().isoformat(),
                payload.get("created_by", "app"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok"})


@router.get("/pjp")
def list_pjp(date: str | None = None, route_id: str | None = None):
    conn = get_conn()
    try:
        if date and route_id:
            rows = conn.execute(
                "SELECT * FROM pjp_plans WHERE date = ? AND route_id = ? ORDER BY route_id",
                (date, route_id),
            ).fetchall()
        elif date:
            rows = conn.execute(
                "SELECT * FROM pjp_plans WHERE date = ? ORDER BY route_id",
                (date,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM pjp_plans ORDER BY date DESC, route_id").fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/pjp")
async def upsert_pjp(request: Request):
    payload = await request.json()
    plan_id = payload.get("plan_id") or f"pjp_{uuid.uuid4().hex}"
    date_val = payload.get("date")
    route_id = payload.get("route_id")
    if not date_val or not route_id:
        raise HTTPException(status_code=400, detail="date and route_id are required")

    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT plan_id FROM pjp_plans WHERE date = ? AND route_id = ?",
            (date_val, route_id),
        ).fetchone()
        if existing:
            plan_id = existing["plan_id"]

        conn.execute(
            """
            INSERT INTO pjp_plans (
              plan_id, date, route_id, planned_a, planned_b, planned_c, planned_d, planned_s, total_planned,
              source_file, source_sheet, source_row
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (plan_id) DO UPDATE SET
              date = excluded.date,
              route_id = excluded.route_id,
              planned_a = excluded.planned_a,
              planned_b = excluded.planned_b,
              planned_c = excluded.planned_c,
              planned_d = excluded.planned_d,
              planned_s = excluded.planned_s,
              total_planned = excluded.total_planned,
              source_file = excluded.source_file,
              source_sheet = excluded.source_sheet,
              source_row = excluded.source_row
            """,
            (
                plan_id,
                date_val,
                route_id,
                payload.get("planned_a"),
                payload.get("planned_b"),
                payload.get("planned_c"),
                payload.get("planned_d"),
                payload.get("planned_s"),
                payload.get("total_planned"),
                "app",
                "master",
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok", "plan_id": plan_id})
