from __future__ import annotations

import datetime as dt
import hashlib
import re
from typing import Any, List


def today_iso() -> str:
    return dt.date.today().isoformat()


def hash_txn(parts: List[str]) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def norm_key(value: str | None) -> str:
    if not value:
        return ""
    s = str(value).strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[;:.,]", "", s)
    return s


def to_num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0

