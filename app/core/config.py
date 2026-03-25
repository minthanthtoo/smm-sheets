from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("SMM_DB", str(ROOT / "db" / "app.db"))).resolve()
STATIC_DIR = Path(os.environ.get("SMM_STATIC_DIR", str(ROOT / "app" / "static"))).resolve()
EXPORT_ROOT = Path(os.environ.get("SMM_EXPORT_ROOT", str(ROOT / "out" / "exports"))).resolve()
IMPORT_ROOT = Path(os.environ.get("SMM_IMPORT_ROOT", str(ROOT / "out" / "imports"))).resolve()
