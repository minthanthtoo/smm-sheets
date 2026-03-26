from __future__ import annotations

import sqlite3
from decimal import Decimal
from datetime import date, datetime
from typing import Any, Dict

from .config import DB_DSN

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover - optional dependency
    psycopg = None
    dict_row = None


def is_postgres(dsn: str) -> bool:
    return dsn.startswith("postgres://") or dsn.startswith("postgresql://")


class DBConn:
    def __init__(self, conn, flavor: str):
        self._conn = conn
        self.flavor = flavor

    def execute(self, sql: str, params: Any | None = None):
        if params is None:
            return self._conn.execute(sql)
        if self.flavor == "postgres":
            sql = sql.replace("?", "%s")
        return self._conn.execute(sql, params)

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()

    def __getattr__(self, item):
        return getattr(self._conn, item)


def get_conn() -> DBConn:
    if is_postgres(DB_DSN):
        if psycopg is None:
            raise RuntimeError("psycopg is required for Postgres connections")
        conn = psycopg.connect(DB_DSN, row_factory=dict_row)
        return DBConn(conn, "postgres")

    conn = sqlite3.connect(DB_DSN)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return DBConn(conn, "sqlite")


def row_to_dict(row: Any) -> Dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        items = row.items()
    else:
        items = ((k, row[k]) for k in row.keys())
    out: Dict[str, Any] = {}
    for k, v in items:
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, (date, datetime)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out
