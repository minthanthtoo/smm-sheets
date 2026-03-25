from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_db_raw = os.environ.get("DATABASE_URL") or os.environ.get("SMM_DB", str(ROOT / "db" / "app.db"))
DB_DSN = _db_raw.strip()
STATIC_DIR = Path(os.environ.get("SMM_STATIC_DIR", str(ROOT / "app" / "static"))).resolve()
EXPORT_ROOT = Path(os.environ.get("SMM_EXPORT_ROOT", str(ROOT / "out" / "exports"))).resolve()
IMPORT_ROOT = Path(os.environ.get("SMM_IMPORT_ROOT", str(ROOT / "out" / "imports"))).resolve()
