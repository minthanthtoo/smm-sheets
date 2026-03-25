from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.db import get_conn

router = APIRouter()


@router.get("/health")
def health():
    return JSONResponse({"status": "ok"})


@router.get("/ready")
def ready():
    conn = get_conn()
    try:
        conn.execute("SELECT 1")
        return JSONResponse({"status": "ok"})
    finally:
        conn.close()

