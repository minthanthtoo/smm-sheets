from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.db import get_conn, row_to_dict

router = APIRouter(prefix="/api/quality")


def ensure_import_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS import_jobs (
          import_id TEXT PRIMARY KEY,
          requested_at TEXT NOT NULL,
          completed_at TEXT,
          region TEXT,
          status TEXT NOT NULL,
          input_dir TEXT,
          file_names TEXT,
          error_message TEXT,
          requested_by TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_import_jobs_requested_at
          ON import_jobs (requested_at)
        """
    )


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


@router.get("/import_health")
def import_health(limit: int = 200):
    limit = max(1, min(int(limit), 1000))
    conn = get_conn()
    try:
        ensure_import_table(conn)
        rows = conn.execute(
            """
            SELECT region,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                   MAX(requested_at) AS last_requested,
                   MAX(CASE WHEN status = 'failed' THEN completed_at END) AS last_failed,
                   COUNT(*) AS total_count
            FROM import_jobs
            GROUP BY region
            ORDER BY region
            """,
        ).fetchall()
        out = [row_to_dict(r) for r in rows][:limit]
        return JSONResponse({"rows": out})
    finally:
        conn.close()


@router.get("/actions")
def resolve_actions(limit: int = 200, q: str | None = None):
    limit = max(1, min(int(limit), 1000))
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT audit_id, table_name, record_id, action, old_values, new_values, changed_at, changed_by
            FROM audit_log
            ORDER BY changed_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out = []
        query = (q or "").lower().strip()
        for r in rows:
            d = row_to_dict(r)
            if query:
                hay = f"{d.get('table_name','')} {d.get('record_id','')} {d.get('action','')} {d.get('changed_by','')}".lower()
                if query not in hay:
                    continue
            out.append(d)
        return JSONResponse({"rows": out})
    finally:
        conn.close()
