from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List

from fastapi import HTTPException

from app.core.config import DB_DSN, EXPORT_ROOT, ROOT


def list_regions() -> List[str]:
    source_dir = ROOT / "source"
    if not source_dir.exists():
        return []
    regions = []
    for p in source_dir.iterdir():
        if p.is_dir() and p.name.isupper():
            regions.append(p.name.upper())
    return sorted(regions)


def run_excel_regeneration(out_dir: Path, include: List[str] | None = None) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "regenerate_reports_from_db.py"),
        "--db",
        str(DB_DSN),
        "--root-dir",
        str(ROOT),
        "--out-dir",
        str(out_dir),
    ]
    if include:
        cmd.extend(["--include", ",".join(include)])
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
            files = [
                p for p in rdir.iterdir()
                if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm"}
            ]
            for book in sorted(files):
                arcname = f"{rdir.name}/{book.name}"
                zf.write(book, arcname)
            for manifest in sorted(rdir.glob("*_manifest.json")):
                arcname = f"{rdir.name}/{manifest.name}"
                zf.write(manifest, arcname)
        staging_dir = out_dir / "staging"
        if staging_dir.exists():
            for csv_path in sorted(staging_dir.glob("*.csv")):
                arcname = f"staging/{csv_path.name}"
                zf.write(csv_path, arcname)
        top_manifest = out_dir / "regeneration_manifest.json"
        if top_manifest.exists():
            zf.write(top_manifest, "regeneration_manifest.json")
    return zip_path


def prepare_export_dir() -> Path:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    return EXPORT_ROOT
