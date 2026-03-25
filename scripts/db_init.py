#!/usr/bin/env python3
"""Initialize database using db/schema.sql (SQLite or Postgres)."""
import argparse
from pathlib import Path

from db_compat import get_conn, resolve_db_target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="db/app.db", help="SQLite DB path or Postgres URL")
    parser.add_argument("--schema", default="db/schema.sql", help="Schema SQL path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    db_target = resolve_db_target(root, args.db)
    schema_path = (root / args.schema).resolve()

    schema_sql = schema_path.read_text(encoding="utf-8")
    if not db_target.startswith("postgres"):
        Path(db_target).parent.mkdir(parents=True, exist_ok=True)

    conn = get_conn(db_target)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"Initialized DB at {db_target}")


if __name__ == "__main__":
    main()
