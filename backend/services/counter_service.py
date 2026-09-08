from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from config import get_settings
from database import DbClient
from schemas import CounterOverrideRequest, CounterOverrideUse, OrderCreate, OwnerPinVerify
from services import device_service, order_service, pin_service
from services.business_service import serialize_business_for_response


def _counter(client: DbClient, device_session: str | None) -> tuple[dict, dict]:
    return device_service.business_for_device_session(client, device_session, expected_type="counter")


def menu(client: DbClient, device_session: str | None) -> dict:
    from services import kiosk_service
    business, device = _counter(client, device_session)
    return {**kiosk_service.get_kiosk_payload(client, business["slug"]), "device": device}


def create_order(client: DbClient, device_session: str | None, payload: OrderCreate, idempotency_key: str | None) -> dict:
    business, device = _counter(client, device_session)
    return order_service.create_kiosk_order(client, business["slug"], payload, source="counter_entry", idempotency_key=idempotency_key)


def kitchen_orders(client: DbClient, device_session: str | None, status: str = "active") -> dict:
    business, device = _counter(client, device_session)
    return {"business": serialize_business_for_response(business), "device": device, "orders": order_service.list_orders(client, UUID(str(business["id"])), status_filter=status, limit=250)}


def pending_payments(client: DbClient, device_session: str | None) -> dict:
    business, device = _counter(client, device_session)
    _expire_claims(client, UUID(str(business["id"])))
    rows = client.table("payments").select("*").eq("business_id", str(business["id"])).eq("provider", "pay_at_counter").in_("status", ["pay_at_counter_pending", "pending", "failed"]).order("created_at", desc=True).limit(100).execute().data or []
    for row in rows:
        if row.get("order_id"):
            row["order"] = order_service.get_order(client, UUID(str(row["order_id"])), UUID(str(business["id"])))
        row["claim"] = client.execute_one("select id,device_id,status,claimed_at,expires_at from counter_payment_claims where business_id=%(business_id)s and payment_id=%(payment_id)s and status='claimed' and expires_at > now() limit 1", {"business_id": str(business["id"]), "payment_id": str(row["id"])})
        row["item_count"] = sum(int(item.get("quantity") or 0) for item in ((row.get("order") or {}).get("items") or []))
    return {"business": serialize_business_for_response(business), "device": device, "payments": rows}


CLAIM_MINUTES = 5


def _expire_claims(client: DbClient, business_id: UUID) -> None:
    client.execute_command("update counter_payment_claims set status='expired', released_at=now() where business_id=%(business_id)s and status='claimed' and expires_at <= now()", {"business_id": str(business_id)})


def claim_payment(client: DbClient, device_session: str | None, payment_id: UUID) -> dict:
    business, device = _counter(client, device_session)
    business_id = UUID(str(business["id"]))
    _expire_claims(client, business_id)
    payment = client.execute_one("select * from payments where id=%(payment_id)s and business_id=%(business_id)s and provider='pay_at_counter' for update", {"payment_id": str(payment_id), "business_id": str(business_id)})
    if not payment:
        raise HTTPException(status_code=404, detail="Counter payment not found.")
    if payment.get("status") not in {"pending", "pay_at_counter_pending", "failed"}:
        raise HTTPException(status_code=409, detail="This payment is no longer available for collection.")
    active = client.execute_one("select * from counter_payment_claims where business_id=%(business_id)s and payment_id=%(payment_id)s and status='claimed' and expires_at > now() for update", {"business_id": str(business_id), "payment_id": str(payment_id)})
    if active and str(active.get("device_id")) != str(device["id"]):
        raise HTTPException(status_code=409, detail="This payment is being handled by another Counter device.")
    if not active:
        active = client.execute_one("insert into counter_payment_claims (business_id,payment_id,order_id,device_id,expires_at) values (%(business_id)s,%(payment_id)s,%(order_id)s,%(device_id)s,now() + (%(minutes)s || ' minutes')::interval) returning *", {"business_id": str(business_id), "payment_id": str(payment_id), "order_id": str(payment["order_id"]), "device_id": str(device["id"]), "minutes": CLAIM_MINUTES})
    _audit(client, business_id, "counter_payment_claimed", "payments", payment_id, device, {"claim_id": str(active["id"])})
    return {"payment": payment, "claim": active}


def release_payment(client: DbClient, device_session: str | None, payment_id: UUID) -> dict:
    business, device = _counter(client, device_session)
    row = client.execute_one("update counter_payment_claims set status='released',released_at=now() where business_id=%(business_id)s and payment_id=%(payment_id)s and device_id=%(device_id)s and status='claimed' returning *", {"business_id": str(business["id"]), "payment_id": str(payment_id), "device_id": str(device["id"])})
    if not row:
        raise HTTPException(status_code=404, detail="Active payment claim not found.")
    _audit(client, UUID(str(business["id"])), "counter_payment_released", "payments", payment_id, device, {})
    return row


def create_override(client: DbClient, device_session: str | None, payload: CounterOverrideRequest) -> dict:
    business, device = _counter(client, device_session)
    pin_service.verify_owner_pin(client, business["slug"], OwnerPinVerify(pin=payload.pin))
    now = datetime.now(timezone.utc)
    token = jwt.encode({"type": "counter_override", "action": payload.action, "business_id": str(business["id"]), "device_id": str(device["id"]), "exp": now + timedelta(minutes=5), "iat": now, "jti": str(uuid4())}, get_settings().jwt_secret, algorithm=get_settings().jwt_algorithm)
    _audit(client, UUID(str(business["id"])), "counter_manager_override_authorized", "devices", UUID(str(device["id"])), device, {"action": payload.action, "reason": payload.reason, "actor_type": "owner_pin"})
    return {"override_token": token, "expires_at": (now + timedelta(minutes=5)).isoformat(), "action": payload.action}


def cancel_pending_payment(client: DbClient, device_session: str | None, payment_id: UUID, payload: CounterOverrideUse) -> dict:
    business, device = _counter(client, device_session)
    try:
        claims = jwt.decode(payload.override_token, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Override authorization expired or invalid.") from exc
    if claims.get("type") != "counter_override" or claims.get("action") != "cancel_pending_payment" or claims.get("business_id") != str(business["id"]) or claims.get("device_id") != str(device["id"]):
        raise HTTPException(status_code=403, detail="Override authorization does not match this Counter action.")
    payment = client.execute_one("select * from payments where id=%(payment_id)s and business_id=%(business_id)s and provider='pay_at_counter' for update", {"payment_id": str(payment_id), "business_id": str(business["id"])})
    if not payment:
        raise HTTPException(status_code=404, detail="Counter payment not found.")
    if payment.get("status") not in {"pending", "pay_at_counter_pending", "failed"}:
        raise HTTPException(status_code=409, detail="Only unpaid counter payments can be cancelled.")
    client.execute_command("update payments set status='cancelled',updated_at=now() where id=%(payment_id)s and business_id=%(business_id)s", {"payment_id": str(payment_id), "business_id": str(business["id"])})
    client.execute_command("update orders set status='cancelled',payment_status='cancelled',cancel_reason=%(reason)s,updated_at=now() where id=%(order_id)s and business_id=%(business_id)s", {"order_id": str(payment["order_id"]), "business_id": str(business["id"]), "reason": payload.reason.strip()})
    client.execute_command("update counter_payment_claims set status='released',released_at=now() where payment_id=%(payment_id)s and business_id=%(business_id)s and status='claimed'", {"payment_id": str(payment_id), "business_id": str(business["id"])})
    _audit(client, UUID(str(business["id"])), "counter_payment_cancelled_by_manager", "payments", payment_id, device, {"reason": payload.reason.strip(), "action": claims.get("action")})
    return {"cancelled": True, "payment_id": str(payment_id)}


def _audit(client: DbClient, business_id: UUID, action: str, entity: str, entity_id: UUID, device: dict, metadata: dict) -> None:
    client.table("audit_logs").insert({"business_id": str(business_id), "user_id": None, "action": action, "entity": entity, "entity_id": str(entity_id), "metadata": Jsonb({**metadata, "device_id": str(device.get("id"))})}).execute()


def handover_history(client: DbClient, device_session: str | None, start: datetime | None = None, end: datetime | None = None) -> dict:
    business, device = _counter(client, device_session)
    return {"business": serialize_business_for_response(business), "device": device, "orders": order_service.list_orders(client, UUID(str(business["id"])), status_filter="completed", start=start, end=end, limit=250)}


def hold_order(client: DbClient, device_session: str | None, payload: OrderCreate, reference: str | None = None) -> dict:
    business, device = _counter(client, device_session)
    row = client.execute_one("insert into counter_held_orders (business_id,device_id,order_reference,payload) values (%(business_id)s,%(device_id)s,%(reference)s,%(payload)s) returning *", {"business_id": str(business["id"]), "device_id": str(device["id"]), "reference": (reference or "").strip() or None, "payload": Jsonb(payload.model_dump(mode="json"))})
    return row or {}


def held_orders(client: DbClient, device_session: str | None) -> list[dict]:
    _business, device = _counter(client, device_session)
    client.execute_command("update counter_held_orders set status='expired',updated_at=now() where device_id=%(device_id)s and status='held' and expires_at<=now()", {"device_id": str(device["id"])})
    return client.fetch_all("select * from counter_held_orders where device_id=%(device_id)s and status='held' order by created_at desc", {"device_id": str(device["id"])})


def resume_order(client: DbClient, device_session: str | None, held_id: UUID) -> dict:
    business, device = _counter(client, device_session)
    row = client.execute_one("update counter_held_orders set status='resumed',updated_at=now() where id=%(id)s and business_id=%(business_id)s and device_id=%(device_id)s and status='held' returning *", {"id": str(held_id), "business_id": str(business["id"]), "device_id": str(device["id"])})
    if not row: raise HTTPException(status_code=404, detail="Held order not found or already resumed.")
    return row


def cancel_held_order(client: DbClient, device_session: str | None, held_id: UUID) -> None:
    business, device = _counter(client, device_session)
    if not client.execute_command("update counter_held_orders set status='cancelled',updated_at=now() where id=%(id)s and business_id=%(business_id)s and device_id=%(device_id)s and status='held'", {"id": str(held_id), "business_id": str(business["id"]), "device_id": str(device["id"])}): raise HTTPException(status_code=404, detail="Held order not found.")
