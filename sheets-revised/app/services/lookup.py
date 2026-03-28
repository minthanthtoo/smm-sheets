from __future__ import annotations

from typing import Any, Dict


def get_product_meta(conn: Any, product_id: str, as_of: str) -> Dict[str, Any]:
    hist = conn.execute(
        """
        SELECT * FROM product_history
        WHERE product_id = ? AND effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
        ORDER BY effective_from DESC
        LIMIT 1
        """,
        (product_id, as_of, as_of),
    ).fetchone()
    base = conn.execute(
        "SELECT * FROM products WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    pack_size = hist["pack_size"] if hist else None
    ml_per_bottle = hist["ml_per_bottle"] if hist else None
    if (ml_per_bottle in (None, 0, "")) and base and base["ml"] not in (None, ""):
        try:
            ml_per_bottle = int(float(base["ml"]))
        except Exception:
            ml_per_bottle = None
    return {
        "pack_size": pack_size,
        "ml_per_bottle": ml_per_bottle,
    }


def get_outlet_route_as_of(conn: Any, outlet_id: str, as_of: str) -> str | None:
    row = conn.execute(
        """
        SELECT route_id FROM outlet_history
        WHERE outlet_id = ? AND effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
        ORDER BY effective_from DESC
        LIMIT 1
        """,
        (outlet_id, as_of, as_of),
    ).fetchone()
    return row["route_id"] if row else None
