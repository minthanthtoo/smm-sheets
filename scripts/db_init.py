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
        if conn.flavor == "postgres":
            try:
                conn.execute(
                    "ALTER TABLE sales_transactions ADD CONSTRAINT ux_sales_transactions_txn_hash UNIQUE (txn_hash)"
                )
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            try:
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_sales_transactions_txn_hash ON sales_transactions (txn_hash)"
                )
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
        try:
            conn.executescript(schema_sql)
            conn.commit()
        except Exception as exc:
            if conn.flavor == "postgres" and "InvalidForeignKey" in str(exc):
                try:
                    conn.rollback()
                except Exception:
                    pass
                fallback_sql = schema_sql.replace(
                    "FOREIGN KEY (txn_hash) REFERENCES sales_transactions(txn_hash) ON DELETE CASCADE",
                    "",
                )
                try:
                    conn.execute("DROP TABLE IF EXISTS sales_financials")
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                conn.executescript(fallback_sql)
                conn.commit()
            else:
                raise
    finally:
        conn.close()

    print(f"Initialized DB at {db_target}")


if __name__ == "__main__":
    main()
