from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from app.core.db import get_conn, row_to_dict
from app.services.excel_export import build_export_zip, list_regions, prepare_export_dir, run_excel_regeneration


EXPORT_CATEGORIES = {
    "individual_sales",
    "sku_summary",
    "township_summary",
    "van_wise_sku",
    "sales_compare",
    "follow_up_sales",
    "debtors",
    "other",
}

router = APIRouter(prefix="/api")


def ensure_export_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS export_jobs (
          export_id TEXT PRIMARY KEY,
          requested_at TEXT NOT NULL,
          completed_at TEXT,
          region TEXT,
          status TEXT NOT NULL,
          file_path TEXT,
          error_message TEXT,
          requested_by TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_export_jobs_requested_at
          ON export_jobs (requested_at)
        """
    )


@router.get("/regions")
def regions():
    return JSONResponse({"regions": list_regions()})


@router.get("/reports/summary")
def report_summary(start: str, end: str):
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT
              COALESCE(SUM(qty_pack), 0) AS total_pack,
              COALESCE(SUM(qty_bottle), 0) AS total_bottle,
              COALESCE(SUM(qty_liter), 0) AS total_liter,
              COUNT(DISTINCT outlet_id) AS active_outlets
            FROM sales_transactions
            WHERE date BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()
        return JSONResponse({"start": start, "end": end, **row_to_dict(row)})
    finally:
        conn.close()


@router.get("/reports/sales_export")
def sales_export(start: str, end: str):
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT s.date, s.outlet_id, o.outlet_name_mm, o.outlet_name_en,
                   s.product_id, p.product_name, s.qty_pack, s.qty_bottle, s.qty_liter,
                   s.channel, s.voucher_no, s.car_no, s.route_id
            FROM sales_transactions s
            LEFT JOIN outlets o ON s.outlet_id = o.outlet_id
            LEFT JOIN products p ON s.product_id = p.product_id
            WHERE s.date BETWEEN ? AND ?
            ORDER BY s.date, s.outlet_id
            """,
            (start, end),
        ).fetchall()

        header = [
            "date", "outlet_id", "outlet_name_mm", "outlet_name_en",
            "product_id", "product_name", "qty_pack", "qty_bottle", "qty_liter",
            "channel", "voucher_no", "car_no", "route_id",
        ]
        lines = [",".join(header)]
        for r in rows:
            vals = [row_to_dict(r).get(h, "") for h in header]
            out = []
            for v in vals:
                v = "" if v is None else str(v)
                if "," in v or "\"" in v or "\n" in v:
                    v = "\"" + v.replace("\"", "\"\"") + "\""
                out.append(v)
            lines.append(",".join(out))
        csv_data = "\n".join(lines)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=\"sales_{start}_to_{end}.csv\""},
        )
    finally:
        conn.close()


@router.get("/quality/summary")
def quality_summary(start: str | None = None, end: str | None = None):
    conn = get_conn()
    try:
        where = ""
        params: List[Any] = []
        if start and end:
            where = "WHERE date BETWEEN ? AND ?"
            params.extend([start, end])
        row = conn.execute(
            f"""
            SELECT
              COUNT(*) AS total_rows,
              SUM(CASE WHEN outlet_id IS NULL OR outlet_id = '' THEN 1 ELSE 0 END) AS missing_outlet,
              SUM(CASE WHEN product_id IS NULL OR product_id = '' THEN 1 ELSE 0 END) AS missing_product,
              SUM(CASE WHEN date IS NULL THEN 1 ELSE 0 END) AS missing_date,
              SUM(CASE WHEN qty_liter IS NULL THEN 1 ELSE 0 END) AS missing_liter,
              SUM(CASE WHEN route_id IS NULL OR route_id = '' THEN 1 ELSE 0 END) AS missing_route
            FROM sales_transactions
            {where}
            """,
            params,
        ).fetchone()
        return JSONResponse({"start": start, "end": end, **row_to_dict(row)})
    finally:
        conn.close()


@router.post("/reports/export_excel")
async def export_excel(request: Request):
    payload = await request.json()
    region = payload.get("region") if isinstance(payload, dict) else None
    include = payload.get("include") if isinstance(payload, dict) else None
    if include is not None and isinstance(include, str):
        include = [v.strip() for v in include.split(",") if v.strip()]
    if include is not None and not isinstance(include, list):
        raise HTTPException(status_code=400, detail="include must be a list or comma-separated string")
    if include:
        include = [str(v) for v in include]
        invalid = [v for v in include if v not in EXPORT_CATEGORIES]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unknown export categories: {', '.join(invalid)}")
    if region:
        region = str(region).upper()
        if region not in list_regions():
            raise HTTPException(status_code=404, detail=f"Unknown region: {region}")

    export_root = prepare_export_dir()
    stamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = export_root / f"export_{stamp}_{uuid.uuid4().hex[:8]}"
    out_dir.mkdir(parents=True, exist_ok=True)

    export_id = f"exp_{uuid.uuid4().hex}"
    requested_at = dt.datetime.utcnow().isoformat()
    conn = get_conn()
    try:
        ensure_export_table(conn)
        conn.execute(
            """
            INSERT INTO export_jobs (
              export_id, requested_at, region, status, requested_by
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (export_id, requested_at, region, "running", "app"),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        run_excel_regeneration(out_dir, include=include or None)
        zip_path = build_export_zip(out_dir, region)
    except HTTPException as exc:
        conn = get_conn()
        try:
            ensure_export_table(conn)
            conn.execute(
                """
                UPDATE export_jobs
                SET status = ?, completed_at = ?, error_message = ?
                WHERE export_id = ?
                """,
                ("failed", dt.datetime.utcnow().isoformat(), str(exc.detail), export_id),
            )
            conn.commit()
        finally:
            conn.close()
        raise
    except Exception as exc:
        conn = get_conn()
        try:
            ensure_export_table(conn)
            conn.execute(
                """
                UPDATE export_jobs
                SET status = ?, completed_at = ?, error_message = ?
                WHERE export_id = ?
                """,
                ("failed", dt.datetime.utcnow().isoformat(), str(exc), export_id),
            )
            conn.commit()
        finally:
            conn.close()
        raise

    conn = get_conn()
    try:
        ensure_export_table(conn)
        conn.execute(
            """
            UPDATE export_jobs
            SET status = ?, completed_at = ?, file_path = ?
            WHERE export_id = ?
            """,
            ("success", dt.datetime.utcnow().isoformat(), str(zip_path), export_id),
        )
        conn.commit()
    finally:
        conn.close()

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=zip_path.name,
    )


@router.get("/reports/export_history")
def export_history(limit: int = 25):
    limit = max(1, min(int(limit), 200))
    conn = get_conn()
    try:
        ensure_export_table(conn)
        rows = conn.execute(
            """
            SELECT export_id, requested_at, completed_at, region, status, file_path, error_message, requested_by
            FROM export_jobs
            ORDER BY requested_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return JSONResponse({"rows": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.get("/reports/export_download")
def export_download(export_id: str):
    conn = get_conn()
    try:
        ensure_export_table(conn)
        row = conn.execute(
            "SELECT file_path FROM export_jobs WHERE export_id = ?",
            (export_id,),
        ).fetchone()
        if not row or not row["file_path"]:
            raise HTTPException(status_code=404, detail="Export file not found")
        file_path = Path(row["file_path"]).resolve()
    finally:
        conn.close()

    export_root = prepare_export_dir().resolve()
    if export_root not in file_path.parents:
        raise HTTPException(status_code=400, detail="Invalid export file path")

    return FileResponse(file_path, media_type="application/zip", filename=file_path.name)
