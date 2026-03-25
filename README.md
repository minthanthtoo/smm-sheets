# SMM Web App (Single Source of Truth)

A FastAPI + SQLite app that replaces Excel-heavy workflows while preserving Excel outputs via automatic regeneration from the database.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# initialize database
python3 scripts/db_init.py --db db/app.db

# migrate Excel inputs (all regions)
python3 scripts/migrate_from_excel.py --in-dir in --db db/app.db

# or per region (example MTL)
python3 scripts/migrate_from_excel.py --in-dir in/MTL --db db/app.db --region MTL

# run server
uvicorn app.main:app --reload
```

Open:
- http://127.0.0.1:8000/daily-sales
- http://127.0.0.1:8000/outlets
- http://127.0.0.1:8000/reports
- http://127.0.0.1:8000/imports
- http://127.0.0.1:8000/master-data
- http://127.0.0.1:8000/quality

## Excel Regeneration (from DB)

The Reports dashboard includes **Export Excel**, which regenerates Excel files using templates in `source/<REGION>/` and downloads a ZIP.

## Health & Ops

- `GET /health` basic liveness check
- `GET /ready` DB readiness check
- `GET /api/reports/export_history` recent export runs

## Environment Variables

- `DATABASE_URL` : Postgres connection URL (takes priority when set)
- `SMM_DB` : SQLite DB path (used when `DATABASE_URL` is not set; default `db/app.db`)
- `SMM_STATIC_DIR` : static assets path (default `app/static`)
- `SMM_EXPORT_ROOT` : export folder for ZIPs (default `out/exports`)
- `SMM_IMPORT_ROOT` : import upload folder (default `out/imports`)

## Project Structure

```
app/
  api/            # FastAPI routes
  core/           # config + DB helpers
  services/       # domain services (Excel export, lookups)
  static/         # UI
  main.py         # entrypoint
scripts/          # ETL + reporting tools
source/           # Excel templates (by region)
```

## Publishing Notes

- Use `DATABASE_URL` for Postgres (Supabase) or `SMM_DB` for SQLite.
- Ensure `source/<REGION>` templates are present for Excel regeneration.
- Exports are stored under `out/exports/` for auditability.

## Render Deployment

This repo includes `render.yaml` for one‑click deployment. On the free tier, it uses `/tmp` (ephemeral). For persistence, upgrade and mount a disk.
Set `DATABASE_URL` in Render Environment if you want to use Supabase/Postgres.

Behavior:
- On boot, the app runs `scripts/db_init.py` against `DATABASE_URL` (if set) or `SMM_DB` (safe to re-run).
- Uvicorn serves the app on `$PORT` as required by Render.

If you use Render, commit `render.yaml` and connect the repo as a Blueprint.

## Workflow Coverage

The app now includes:
- Import Hub for Excel ingestion
- Master Data screens (Products, Townships, Routes, PJP) with history inserts
- Data Quality desk for fixing missing fields
- Reports dashboard with Excel regeneration + export history
