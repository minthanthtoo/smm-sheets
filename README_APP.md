# SMM App Prototype (Single Source of Truth)

This prototype demonstrates:
- Migration from Excel to a SQLite database
- Effective-dated master data (outlets/products/routes/townships)
- A working UI for Daily Sales, Outlet Master, and Report Dashboard

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

## Environment
- Set `DATABASE_URL` for Postgres, or `SMM_DB` for a different SQLite DB path.

## Notes
- The migration script seeds history tables with effective dates.
- Outlet updates from the UI create new history rows (no overwriting of past states).
- Reports read from the transaction ledger and respect date ranges.
