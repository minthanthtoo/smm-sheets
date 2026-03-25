from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.db import get_conn, row_to_dict
from app.core.utils import norm_key, today_iso

router = APIRouter(prefix="/api")


@router.get("/outlets")
def outlets(search: str | None = None, as_of: str | None = None, include_inactive: int = 0):
    as_of = as_of or today_iso()
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM outlet_history
            WHERE effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
            ORDER BY effective_from DESC
            """,
            (as_of, as_of),
        ).fetchall()
        outlet_map: Dict[str, dict] = {}
        base_outlets = {r["outlet_id"]: row_to_dict(r) for r in conn.execute("SELECT * FROM outlets").fetchall()}
        for r in rows:
            oid = r["outlet_id"]
            if oid not in outlet_map:
                merged = row_to_dict(r)
                base = base_outlets.get(oid, {})
                merged["township_name_raw"] = base.get("township_name_raw")
                merged["address_full"] = merged.get("address_full") or base.get("address_full")
                outlet_map[oid] = merged

        results = list(outlet_map.values())
        if not include_inactive:
            results = [o for o in results if base_outlets.get(o.get("outlet_id"), {}).get("active", 1) == 1]
        if search:
            s = search.lower()
            results = [o for o in results if s in (o.get("outlet_name_mm") or "").lower() or s in (o.get("outlet_name_en") or "").lower() or s in (o.get("contact_phone") or "").lower()]

        return JSONResponse({"as_of": as_of, "outlets": results})
    finally:
        conn.close()


@router.get("/outlets/dedupe")
def outlet_dedupe(as_of: str | None = None):
    as_of = as_of or today_iso()
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM outlet_history
            WHERE effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
            ORDER BY effective_from DESC
            """,
            (as_of, as_of),
        ).fetchall()
        base_outlets = {r["outlet_id"]: row_to_dict(r) for r in conn.execute("SELECT * FROM outlets").fetchall()}
        latest: Dict[str, dict] = {}
        for r in rows:
            oid = r["outlet_id"]
            if oid not in latest:
                merged = row_to_dict(r)
                base = base_outlets.get(oid, {})
                merged["township_name_raw"] = base.get("township_name_raw")
                latest[oid] = merged

        groups = []
        by_phone: Dict[str, List[dict]] = {}
        by_name: Dict[str, List[dict]] = {}
        for o in latest.values():
            phone = norm_key(o.get("contact_phone"))
            name = o.get("outlet_name_en") or o.get("outlet_name_mm") or ""
            township = o.get("township_name_raw") or ""
            name_key = norm_key(f"{name}|{township}")
            if phone:
                by_phone.setdefault(phone, []).append(o)
            if name_key.strip("|"):
                by_name.setdefault(name_key, []).append(o)

        for key, items in by_phone.items():
            if len(items) > 1:
                groups.append({"reason": "phone", "key": key, "outlets": items})
        for key, items in by_name.items():
            if len(items) > 1:
                groups.append({"reason": "name_township", "key": key, "outlets": items})

        return JSONResponse({"as_of": as_of, "groups": groups})
    finally:
        conn.close()


@router.get("/outlets/{outlet_id}/history")
def outlet_history(outlet_id: str):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM outlet_history WHERE outlet_id = ? ORDER BY effective_from DESC",
            (outlet_id,),
        ).fetchall()
        return JSONResponse({"outlet_id": outlet_id, "history": [row_to_dict(r) for r in rows]})
    finally:
        conn.close()


@router.post("/outlets")
async def upsert_outlet(request: Request):
    payload = await request.json()
    outlet_id = payload.get("outlet_id") or f"out_{uuid.uuid4().hex}"
    effective_from = payload.get("effective_from") or today_iso()
    try:
        effective_from_date = dt.date.fromisoformat(effective_from)
        prev_date = (effective_from_date - dt.timedelta(days=1)).isoformat()
    except Exception:
        prev_date = None

    conn = get_conn()
    try:
        old_row = conn.execute(
            "SELECT * FROM outlet_history WHERE outlet_id = ? AND effective_to IS NULL",
            (outlet_id,),
        ).fetchone()

        conn.execute(
            """
            INSERT INTO outlets (
              outlet_id, outlet_code, outlet_name_mm, outlet_name_en, outlet_type, address_full,
              township_id, township_name_raw, way_code, contact_phone, agent_name, responsible_person,
              notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (outlet_id) DO NOTHING
            """,
            (
                outlet_id,
                payload.get("outlet_code"),
                payload.get("outlet_name_mm"),
                payload.get("outlet_name_en"),
                payload.get("outlet_type"),
                payload.get("address_full"),
                payload.get("township_id"),
                payload.get("township_name_raw"),
                payload.get("way_code"),
                payload.get("contact_phone"),
                payload.get("agent_name"),
                payload.get("responsible_person"),
                payload.get("notes"),
            ),
        )

        conn.execute(
            """
            UPDATE outlet_history
            SET effective_to = ?
            WHERE outlet_id = ? AND effective_to IS NULL
            """,
            (prev_date, outlet_id),
        )

        conn.execute(
            """
            INSERT INTO outlet_history (
              outlet_history_id, outlet_id, outlet_name_mm, outlet_name_en, outlet_type, category,
              route_id, contact_phone, address_full, responsible_person, agent_name, status,
              effective_from, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"outh_{uuid.uuid4().hex}",
                outlet_id,
                payload.get("outlet_name_mm"),
                payload.get("outlet_name_en"),
                payload.get("outlet_type"),
                payload.get("category"),
                payload.get("route_id"),
                payload.get("contact_phone"),
                payload.get("address_full"),
                payload.get("responsible_person"),
                payload.get("agent_name"),
                payload.get("status", "active"),
                effective_from,
                dt.datetime.utcnow().isoformat(),
                payload.get("changed_by", "app"),
            ),
        )

        conn.execute(
            """
            INSERT INTO audit_log (
              audit_id, table_name, record_id, action, old_values, new_values, changed_at, changed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"aud_{uuid.uuid4().hex}",
                "outlets",
                outlet_id,
                "update_outlet" if old_row else "create_outlet",
                json.dumps(row_to_dict(old_row)) if old_row else None,
                json.dumps(payload),
                dt.datetime.utcnow().isoformat(),
                payload.get("changed_by", "app"),
            ),
        )

        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok", "outlet_id": outlet_id})


@router.post("/outlets/merge")
async def merge_outlets(request: Request):
    payload = await request.json()
    primary_id = payload.get("primary_outlet_id")
    dup_id = payload.get("duplicate_outlet_id")
    merge_date = payload.get("merge_date") or today_iso()
    try:
        merge_date_dt = dt.date.fromisoformat(merge_date)
        prev_date = (merge_date_dt - dt.timedelta(days=1)).isoformat()
    except Exception:
        prev_date = None
    reason = payload.get("reason") or "merge"

    if not primary_id or not dup_id:
        raise HTTPException(status_code=400, detail="primary_outlet_id and duplicate_outlet_id are required")

    conn = get_conn()
    try:
        conn.execute(
            "UPDATE sales_transactions SET outlet_id = ? WHERE outlet_id = ?",
            (primary_id, dup_id),
        )

        conn.execute(
            "UPDATE outlet_history SET effective_to = ? WHERE outlet_id = ? AND effective_to IS NULL",
            (prev_date, dup_id),
        )

        conn.execute(
            "INSERT INTO outlet_merge_map (merge_id, from_outlet_id, to_outlet_id, merged_at, reason) VALUES (?, ?, ?, ?, ?)",
            (f"mrg_{uuid.uuid4().hex}", dup_id, primary_id, dt.datetime.utcnow().isoformat(), reason),
        )

        conn.execute(
            "UPDATE outlets SET active = 0 WHERE outlet_id = ?",
            (dup_id,),
        )

        conn.execute(
            """
            INSERT INTO audit_log (
              audit_id, table_name, record_id, action, old_values, new_values, changed_at, changed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"aud_{uuid.uuid4().hex}",
                "outlets",
                dup_id,
                "merge",
                json.dumps({"from": dup_id}),
                json.dumps({"to": primary_id}),
                dt.datetime.utcnow().isoformat(),
                payload.get("changed_by", "app"),
            ),
        )

        conn.commit()
    finally:
        conn.close()

    return JSONResponse({"status": "ok"})
