from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path
from typing import List

from fastapi import HTTPException

from app.core.config import DB_PATH, IMPORT_ROOT, ROOT


def prepare_import_dir() -> Path:
    IMPORT_ROOT.mkdir(parents=True, exist_ok=True)
    return IMPORT_ROOT


def new_job_dir() -> Path:
    base = prepare_import_dir()
    job_dir = base / f"import_{uuid.uuid4().hex[:8]}"
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def run_migration(in_dir: Path, region: str | None = None) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "migrate_from_excel.py"),
        "--db",
        str(DB_PATH),
        "--in-dir",
        str(in_dir),
    ]
    if region:
        cmd.extend(["--region", region])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Import failed"
        raise HTTPException(status_code=500, detail=detail)


def list_input_files(in_dir: Path) -> List[str]:
    if not in_dir.exists():
        return []
    return sorted([p.name for p in in_dir.iterdir() if p.is_file()])

