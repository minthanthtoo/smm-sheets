from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.db import get_conn, row_to_dict

router = APIRouter(prefix="/api/quality")


def build_where(kind: str) -> str:
    if kind == "missing_outlet":
        return "(outlet_id IS NULL OR outlet_id = '')"
    if kind == "missing_product":
        return "(product_id IS NULL OR product_id = '')"
    if kind == "missing_date":
        return "(date IS NULL)"
    if kind == "missing_liter":
        return "(qty_liter IS NULL)"
    if kind == "missing_route":
        return "(route_id IS NULL OR route_id = '')"
    raise HTTPException(status_code=400, detail="Invalid kind")


@router.get("/issues")
def quality_issues(kind: str, start: str | None = None, end: str | None = None, limit: int = 200):
    limit = max(1, min(int(limit), 1000))
    where = build_where(kind)
    params: List[Any] = []
    if start and end:
        where = f"{where} AND date BETWEEN ? AND ?"
        params.extend([start, end])

    conn = get_conn()
    try:
        rows = conn.execute(
            f"""
            SELECT txn_id, date, outlet_id, outlet_name_raw, township_name_raw,
                   product_id, stock_name_raw, route_id, car_no,
                   qty_pack, qty_bottle, qty_liter, channel, voucher_no
            FROM sales_transactions
            WHERE {where}
            ORDER BY date DESC, txn_id
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/fix")
async def quality_fix(request: Request):
    payload = await request.json()
    txn_id = payload.get("txn_id")
    if not txn_id:
        raise HTTPException(status_code=400, detail="txn_id is required")

    fields: Dict[str, Any] = {}
    for key in ("outlet_id", "product_id", "route_id", "date", "qty_liter"):
        if key in payload and payload.get(key) not in (None, ""):
            fields[key] = payload.get(key)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    conn = get_conn()
    try:
        sets = ", ".join([f"{k} = ?" for k in fields.keys()])
        vals = list(fields.values())
        vals.append(txn_id)
        conn.execute(
            f"UPDATE sales_transactions SET {sets} WHERE txn_id = ?",
            vals,
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok"})
