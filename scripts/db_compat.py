from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # optional dependency
    psycopg = None
    dict_row = None


def is_postgres(dsn: str) -> bool:
    return dsn.startswith("postgres://") or dsn.startswith("postgresql://")


def resolve_db_target(root: Path, db_arg: str) -> str:
    if is_postgres(db_arg):
        return db_arg
    return str((root / db_arg).resolve())


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

    def executescript(self, script: str):
        if self.flavor == "sqlite":
            return self._conn.executescript(script)
        statements = [s.strip() for s in script.split(";") if s.strip()]
        for stmt in statements:
            self._conn.execute(stmt)

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()

    def __getattr__(self, item):
        return getattr(self._conn, item)


def get_conn(dsn_or_path: str) -> DBConn:
    if is_postgres(dsn_or_path):
        if psycopg is None:
            raise RuntimeError("psycopg is required for Postgres connections")
        conn = psycopg.connect(dsn_or_path, row_factory=dict_row)
        return DBConn(conn, "postgres")

    conn = sqlite3.connect(dsn_or_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return DBConn(conn, "sqlite")

