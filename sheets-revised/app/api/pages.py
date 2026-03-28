from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

from app.core.config import STATIC_DIR

router = APIRouter()


@router.get("/")
def root():
    return RedirectResponse("/daily-sales")


@router.get("/daily-sales")
def daily_sales_page():
    return FileResponse(STATIC_DIR / "daily_sales.html")


@router.get("/reports")
def reports_page():
    return FileResponse(STATIC_DIR / "reports.html")


@router.get("/outlets")
def outlets_page():
    return FileResponse(STATIC_DIR / "outlets.html")


@router.get("/imports")
def imports_page():
    return FileResponse(STATIC_DIR / "imports.html")


@router.get("/master-data")
def master_data_page():
    return FileResponse(STATIC_DIR / "master_data.html")


@router.get("/quality")
def quality_page():
    return FileResponse(STATIC_DIR / "quality.html")
