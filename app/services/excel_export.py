from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List

from fastapi import HTTPException

from app.core.config import DB_PATH, EXPORT_ROOT, ROOT


def list_regions() -> List[str]:
    source_dir = ROOT / "source"
    if not source_dir.exists():
        return []
    regions = []
    for p in source_dir.iterdir():
        if p.is_dir() and p.name.isupper():
            regions.append(p.name.upper())
    return sorted(regions)


def run_excel_regeneration(out_dir: Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "regenerate_reports_from_db.py"),
        "--db",
        str(DB_PATH),
        "--root-dir",
        str(ROOT),
        "--out-dir",
        str(out_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Export failed"
        raise HTTPException(status_code=500, detail=detail)


def build_export_zip(out_dir: Path, region: str | None) -> Path:
    region = region.upper() if region else None
    if region:
        region_dir = out_dir / region
        if not region_dir.exists():
            raise HTTPException(status_code=404, detail=f"Region {region} not found in export")
        region_dirs = [region_dir]
        zip_name = f"excel_export_{region}.zip"
    else:
        region_dirs = [p for p in out_dir.iterdir() if p.is_dir() and p.name.isupper()]
        if not region_dirs:
            raise HTTPException(status_code=404, detail="No regions found in export")
        zip_name = "excel_export_ALL.zip"

    zip_path = out_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rdir in sorted(region_dirs):
            for xlsx in sorted(rdir.glob("*.xlsx")):
                arcname = f"{rdir.name}/{xlsx.name}"
                zf.write(xlsx, arcname)
    return zip_path


def prepare_export_dir() -> Path:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    return EXPORT_ROOT

