from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.db import get_conn, row_to_dict
from app.core.utils import today_iso

router = APIRouter(prefix="/api")


@router.get("/metadata")
def metadata(as_of: str | None = None):
    as_of = as_of or today_iso()
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM outlet_history
            WHERE effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
            ORDER BY effective_from DESC
            """,
            (as_of, as_of),
        ).fetchall()
        outlets_map: dict[str, dict] = {}
        base_outlets = {r["outlet_id"]: row_to_dict(r) for r in conn.execute("SELECT * FROM outlets").fetchall()}
        for r in rows:
            oid = r["outlet_id"]
            if oid not in outlets_map:
                merged = row_to_dict(r)
                base = base_outlets.get(oid, {})
                merged["township_name_raw"] = base.get("township_name_raw")
                merged["address_full"] = merged.get("address_full") or base.get("address_full")
                outlets_map[oid] = merged

        prows = conn.execute(
            """
            SELECT * FROM product_history
            WHERE effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
            ORDER BY effective_from DESC
            """,
            (as_of, as_of),
        ).fetchall()
        products_map: dict[str, dict] = {}
        for r in prows:
            pid = r["product_id"]
            if pid not in products_map:
                products_map[pid] = row_to_dict(r)

        base_products = {r["product_id"]: row_to_dict(r) for r in conn.execute("SELECT * FROM products").fetchall()}

        products = []
        for pid, hist in products_map.items():
            base = base_products.get(pid, {})
            products.append({
                "product_id": pid,
                "product_name": base.get("product_name"),
                "ml": base.get("ml"),
                "pack_size": hist.get("pack_size"),
                "ml_per_bottle": hist.get("ml_per_bottle"),
                "sales_price": hist.get("sales_price"),
            })

        routes = [row_to_dict(r) for r in conn.execute("SELECT * FROM routes").fetchall()]

        return JSONResponse({
            "as_of": as_of,
            "outlets": list(outlets_map.values()),
            "products": products,
            "routes": routes,
        })
    finally:
        conn.close()

