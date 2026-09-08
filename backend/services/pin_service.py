from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from database import DbClient
from schemas import OwnerPinSet, OwnerPinVerify
from services.business_service import PIN_ADMIN_ROLES, assert_business_access, get_business_by_slug

PIN_ITERATIONS = 240_000
MAX_PIN_FAILURES = 5
PIN_LOCK_MINUTES = 5


def set_owner_pin(client: DbClient, business_id: UUID, user_id: UUID, payload: OwnerPinSet) -> dict:
    business = assert_business_access(client, business_id, user_id, PIN_ADMIN_ROLES)
    existing_hash = business.get("owner_pin_hash")
    if existing_hash:
        if not payload.current_pin:
            raise HTTPException(status_code=400, detail="Current owner PIN is required to change the PIN.")
        if not verify_pin(payload.current_pin, existing_hash):
            raise HTTPException(status_code=403, detail="Current owner PIN is incorrect.")
    row = client.execute_one(
        """
        update businesses
        set owner_pin_hash = %(pin_hash)s,
            owner_pin_set_at = now(),
            pin_failed_attempts = 0,
            pin_locked_until = null
        where id = %(business_id)s
        returning id, owner_pin_set_at
        """,
        {"business_id": str(business_id), "pin_hash": hash_pin(payload.pin)},
    )
    if not row:
        raise HTTPException(status_code=404, detail="Business not found.")
    return {"pin_configured": True, "owner_pin_set_at": row.get("owner_pin_set_at")}


def verify_owner_pin(client: DbClient, business_slug: str, payload: OwnerPinVerify) -> dict:
    business = get_business_by_slug(client, business_slug)
    if not business.get("owner_pin_hash"):
        raise HTTPException(status_code=409, detail="Owner PIN is not configured.")
    locked_until = _parse_datetime(business.get("pin_locked_until"))
    if locked_until and locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")

    if not verify_pin(payload.pin, business["owner_pin_hash"]):
        attempts = int(business.get("pin_failed_attempts") or 0) + 1
        locked = datetime.now(timezone.utc) + timedelta(minutes=PIN_LOCK_MINUTES) if attempts >= MAX_PIN_FAILURES else None
        client.execute_one(
            """
            update businesses
            set pin_failed_attempts = %(attempts)s,
                pin_locked_until = %(locked_until)s
            where id = %(business_id)s
            returning id
            """,
            {"attempts": attempts, "locked_until": locked, "business_id": business["id"]},
        )
        if attempts >= 3:
            _record_failed_pin_alert(client, business, attempts, bool(locked))
        raise HTTPException(status_code=403, detail="Invalid owner PIN.")

    client.execute_one(
        """
        update businesses
        set pin_failed_attempts = 0,
            pin_locked_until = null
        where id = %(business_id)s
        returning id
        """,
        {"business_id": business["id"]},
    )
    return {"ok": True}


def public_lock_state(business: dict) -> dict:
    settings = business.get("kiosk_lock_settings") or {}
    return {
        **settings,
        "owner_pin_configured": bool(business.get("owner_pin_hash")),
    }


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, PIN_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PIN_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_pin(pin: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _record_failed_pin_alert(client: DbClient, business: dict, attempts: int, locked: bool) -> None:
    try:
        title = "Kiosk owner PIN failures"
        message = (
            f"Kiosk owner PIN was locked after {attempts} failed attempts."
            if locked
            else f"Kiosk owner PIN has {attempts} recent failed attempts."
        )
        client.execute_one(
            """
            insert into alerts (business_id, type, severity, title, message, source, status, dedupe_key, metadata)
            values (%(business_id)s, 'kiosk_pin_failed', %(severity)s, %(title)s, %(message)s, 'kiosk_lock', 'open', %(dedupe_key)s, %(metadata)s)
            on conflict (business_id, dedupe_key) do update
            set message = excluded.message,
                severity = excluded.severity,
                metadata = excluded.metadata,
                updated_at = now()
            where alerts.status <> 'resolved'
            returning id
            """,
            {
                "business_id": str(business["id"]),
                "severity": "critical" if locked else "warning",
                "title": title,
                "message": message,
                "dedupe_key": "kiosk:owner_pin_failed",
                "metadata": Jsonb({"attempts": attempts, "locked": locked}),
            },
        )
    except Exception:
        # PIN validation result must not depend on alert persistence.
        return


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
