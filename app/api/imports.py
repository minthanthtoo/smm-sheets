from __future__ import annotations

import datetime as dt
import json
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import ROOT
from app.core.db import get_conn
from app.services.imports import list_input_files, new_job_dir, run_migration

router = APIRouter(prefix="/api")
logger = logging.getLogger("smm")

_executor = ThreadPoolExecutor(max_workers=1)

EXPORT_REGEN = {
    "individual_sales",
    "sku_summary",
    "township_summary",
    "van_wise_sku",
}


def normalize_filename(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def classify_template_name(filename: str) -> str:
    key = normalize_filename(filename)
    if "individual" in key:
        return "individual_sales"
    if "van wise" in key:
        return "van_wise_sku"
    if "sku summary" in key or "sku wise" in key or "sku analysis" in key:
        return "sku_summary"
    if "township" in key and "summary" in key:
        return "township_summary"
    if "sales compare" in key or key.startswith("compare"):
        return "sales_compare"
    if "follow up" in key or "followup" in key or "fus" in key:
        return "follow_up_sales"
    if "debtor" in key:
        return "debtors"
    return "other"


def core_input_reason(filename: str) -> str | None:
    key = normalize_filename(filename)
    if "table" in key and ("dailysales" in key or "daily sales" in key):
        return "Table + DailySales"
    if "pg" in key and ("pg sales" in key or "pg daily sales" in key or "pg dailysales" in key):
        return "PG Table + PGSales"
    return None


def build_source_catalog() -> Dict:
    source_dir = ROOT / "source"
    regions = []
    if not source_dir.exists():
        return {"regions": regions}
    for region_dir in sorted([p for p in source_dir.iterdir() if p.is_dir()]):
        core_files = []
        export_files = []
        files = sorted(
            [p for p in region_dir.iterdir() if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm"}]
        )
        for f in files:
            reason = core_input_reason(f.name)
            if reason:
                core_files.append({"file": f.name, "reason": reason})
                continue
            category = classify_template_name(f.name)
            export_files.append({
                "file": f.name,
                "category": category,
                "export_type": "regen" if category in EXPORT_REGEN else "template",
            })
        regions.append({
            "region": region_dir.name.upper(),
            "core": core_files,
            "exports": export_files,
        })
    return {"regions": regions}


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


def update_job(import_id: str, **fields) -> None:
    conn = get_conn()
    try:
        ensure_import_table(conn)
        sets = []
        vals = []
        for k, v in fields.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(import_id)
        conn.execute(
            f"UPDATE import_jobs SET {', '.join(sets)} WHERE import_id = ?",
            vals,
        )
        conn.commit()
    finally:
        conn.close()


def run_import_job(import_id: str, in_dir: Path, region: str | None) -> None:
    try:
        run_migration(in_dir, region)
        update_job(
            import_id,
            status="success",
            completed_at=dt.datetime.utcnow().isoformat(),
        )
    except HTTPException as exc:
        update_job(
            import_id,
            status="failed",
            completed_at=dt.datetime.utcnow().isoformat(),
            error_message=str(exc.detail),
        )
    except Exception as exc:
        logger.exception("Import failed")
        update_job(
            import_id,
            status="failed",
            completed_at=dt.datetime.utcnow().isoformat(),
            error_message=str(exc),
        )


@router.post("/imports")
async def create_import(
    files: List[UploadFile] = File(...),
    region: str | None = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if region:
        region = region.upper()

    job_dir = new_job_dir()
    saved = []
    for f in files:
        name = Path(f.filename).name
        dest = job_dir / name
        content = await f.read()
        dest.write_bytes(content)
        saved.append(name)

    import_id = f"imp_{uuid.uuid4().hex}"
    requested_at = dt.datetime.utcnow().isoformat()

    conn = get_conn()
    try:
        ensure_import_table(conn)
        conn.execute(
            """
            INSERT INTO import_jobs (
              import_id, requested_at, region, status, input_dir, file_names, requested_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                import_id,
                requested_at,
                region,
                "running",
                str(job_dir),
                json.dumps(saved),
                "app",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    _executor.submit(run_import_job, import_id, job_dir, region)

    return JSONResponse({"import_id": import_id, "status": "running", "files": saved})


@router.get("/imports")
def list_imports(limit: int = 25):
    limit = max(1, min(int(limit), 200))
    conn = get_conn()
    try:
        ensure_import_table(conn)
        rows = conn.execute(
            """
            SELECT import_id, requested_at, completed_at, region, status, input_dir, file_names, error_message, requested_by
            FROM import_jobs
            ORDER BY requested_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["file_names"] = json.loads(d.get("file_names") or "[]")
            except Exception:
                d["file_names"] = []
            out.append(d)
        return JSONResponse({"rows": out})
    finally:
        conn.close()


@router.get("/imports/catalog")
def imports_catalog():
    return JSONResponse(build_source_catalog())


@router.get("/imports/{import_id}")
def import_detail(import_id: str):
    conn = get_conn()
    try:
        ensure_import_table(conn)
        row = conn.execute(
            "SELECT * FROM import_jobs WHERE import_id = ?",
            (import_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Import job not found")
        d = dict(row)
        try:
            d["file_names"] = json.loads(d.get("file_names") or "[]")
        except Exception:
            d["file_names"] = []
        if d.get("input_dir"):
            d["files_present"] = list_input_files(Path(d["input_dir"]))
        return JSONResponse(d)
    finally:
        conn.close()
