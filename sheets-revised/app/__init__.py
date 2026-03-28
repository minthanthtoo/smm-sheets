from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.api import health, imports, master, meta, outlets, pages, quality, reports, sales
from app.core.config import STATIC_DIR
from app.core.logging import configure_logging, get_request_id
from app.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware


def create_app() -> FastAPI:
    configure_logging()
    logger = logging.getLogger("smm")
    app = FastAPI(title="SMM App Prototype")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(pages.router)
    app.include_router(health.router)
    app.include_router(imports.router)
    app.include_router(master.router)
    app.include_router(meta.router)
    app.include_router(sales.router)
    app.include_router(outlets.router)
    app.include_router(quality.router)
    app.include_router(reports.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "request_id": get_request_id()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": get_request_id()},
        )

    return app


app = create_app()
