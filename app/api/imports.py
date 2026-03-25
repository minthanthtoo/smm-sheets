from __future__ import annotations

import datetime as dt
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.db import get_conn
from app.services.imports import list_input_files, new_job_dir, run_migration

router = APIRouter(prefix="/api")
logger = logging.getLogger("smm")

_executor = ThreadPoolExecutor(max_workers=1)


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
