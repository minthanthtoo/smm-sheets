#!/usr/bin/env python3
"""Initialize SQLite database using db/schema.sql."""
import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="db/app.db", help="SQLite DB path")
    parser.add_argument("--schema", default="db/schema.sql", help="Schema SQL path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    db_path = (root / args.db).resolve()
    schema_path = (root / args.schema).resolve()

    schema_sql = schema_path.read_text(encoding="utf-8")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"Initialized DB at {db_path}")


if __name__ == "__main__":
    main()
