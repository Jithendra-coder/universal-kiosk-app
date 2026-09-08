from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from config import get_settings
from database import DbClient
from schemas import KitchenActionRequest, KitchenAvailabilityUpdate, KitchenHoldRequest, KitchenItemCompletion, KitchenOverrideRequest, KitchenPreferenceUpdate, OwnerPinVerify
from services import device_service, order_service, pin_service
from services.business_service import serialize_business_for_response
from services.cache_service import invalidate_business
from utils import timestamps_for_status


def _kitchen(client: DbClient, session: str | None) -> tuple[dict, dict]:
    return device_service.business_for_device_session(client, session, expected_type="kitchen")


def board(client: DbClient, session: str | None, completed: bool = False) -> dict:
    business, device = _kitchen(client, session)
    orders = order_service.list_orders(client, UUID(str(business["id"])), "completed" if completed else "active", limit=250)
    order_ids = [str(order["id"]) for order in orders]
    states_by_order: dict[str, dict] = {}
    item_states_by_order: dict[str, dict[str, dict]] = defaultdict(dict)
    if order_ids:
        states_by_order = {
            str(row["order_id"]): row
            for row in client.fetch_all(
                "select order_id,stage,is_held,hold_reason,held_at,updated_at from kitchen_order_states where business_id=%(business_id)s and order_id = any(%(order_ids)s)",
                {"business_id": str(business["id"]), "order_ids": order_ids},
            )
        }
        for row in client.fetch_all(
            "select order_id,order_item_id,completed_quantity,updated_at from kitchen_item_states where business_id=%(business_id)s and order_id = any(%(order_ids)s)",
            {"business_id": str(business["id"]), "order_ids": order_ids},
        ):
            item_states_by_order[str(row["order_id"])][str(row["order_item_id"])] = row
    return {
        "business": serialize_business_for_response(business),
        "device": device,
        "orders": [
            _ticket(
                client,
                business,
                order,
                states_by_order.get(str(order["id"]), {"stage": order["status"], "is_held": False}),
                item_states_by_order[str(order["id"])],
            )
            for order in orders
        ],
    }


def _ticket(client: DbClient, business: dict, order: dict, state: dict | None = None, item_states: dict[str, dict] | None = None) -> dict:
    if state is None:
        state = client.execute_one(
            "select stage,is_held,hold_reason,held_at,updated_at from kitchen_order_states where order_id=%(order_id)s and business_id=%(business_id)s",
            {"order_id": str(order["id"]), "business_id": str(business["id"])},
        ) or {"stage": order["status"], "is_held": False}
    items = order.get("items") or order.get("order_items") or []
    if item_states is None:
        item_states = {str(row["order_item_id"]): row for row in client.fetch_all("select order_item_id,completed_quantity,updated_at from kitchen_item_states where order_id=%(order_id)s", {"order_id": str(order["id"])})}
    for item in items:
        progress = item_states.get(str(item.get("id")), {})
        item["completed_quantity"] = int(progress.get("completed_quantity") or 0)
        item["kitchen_status"] = "completed" if item["completed_quantity"] >= int(item.get("quantity") or 0) else "pending"
    threshold = (business.get("kiosk_order_settings") or {}).get("kitchen_delay_minutes")
    delayed = bool(threshold and order.get("placed_at") and datetime.now(timezone.utc) > _dt(order["placed_at"]) + timedelta(minutes=int(threshold)))
    return {**order, "source": order.get("source") or "kiosk", "kitchen": {**state, "delayed": delayed, "delay_minutes": threshold}, "items": items, "sync_state": "confirmed"}


def _dt(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _lock(client: DbClient, order_id: UUID) -> None:
    client.execute_one("select pg_advisory_xact_lock(hashtextextended(%(key)s, 0))", {"key": f"kitchen:{order_id}"})


def _seen(client: DbClient, business: dict, device: dict, event_id: UUID) -> bool:
    return bool(client.execute_one("select event_id from kitchen_offline_events where event_id=%(event_id)s and business_id=%(business_id)s and device_id=%(device_id)s", {"event_id": str(event_id), "business_id": str(business["id"]), "device_id": str(device["id"])}))


def _record(client: DbClient, business: dict, device: dict, event_id: UUID, action: str, order_id: UUID, payload: dict) -> None:
    client.table("kitchen_offline_events").insert({"event_id": str(event_id), "business_id": str(business["id"]), "device_id": str(device["id"]), "order_id": str(order_id), "action": action, "payload": Jsonb(payload)}).execute()


def _audit(client: DbClient, business: dict, device: dict, action: str, entity: str, entity_id: UUID, metadata: dict) -> None:
    client.table("audit_logs").insert({"business_id": str(business["id"]), "user_id": None, "action": action, "entity": entity, "entity_id": str(entity_id), "metadata": Jsonb({**metadata, "device_id": str(device["id"]), "actor_type": "kitchen_device"})}).execute()


def _state(client: DbClient, business: dict, order: dict) -> dict:
    return client.execute_one("select * from kitchen_order_states where order_id=%(order_id)s", {"order_id": str(order["id"])}) or {"stage": order["status"], "is_held": False}


def _set_stage(client: DbClient, business: dict, device: dict, order: dict, stage: str, event_id: UUID, action: str, reason: str | None = None) -> dict:
    _lock(client, UUID(str(order["id"])))
    if _seen(client, business, device, event_id):
        return _ticket(client, business, order_service.get_order(client, UUID(str(order["id"])), UUID(str(business["id"]))))
    current = order_service.get_order(client, UUID(str(order["id"])), UUID(str(business["id"])))
    if current["status"] == stage:
        _record(client, business, device, event_id, action, UUID(str(order["id"])), {"idempotent": True})
        return _ticket(client, business, current)
    allowed = {"pending": {"preparing"}, "preparing": {"ready"}, "ready": {"preparing"}}
    if stage not in allowed.get(current["status"], set()):
        raise HTTPException(status_code=409, detail=f"Cannot move order from {current['status']} to {stage}.")
    client.table("orders").update({"status": stage, **timestamps_for_status(stage)}).eq("id", str(order["id"])).eq("business_id", str(business["id"])).execute()
    client.execute_one("insert into kitchen_order_states (order_id,business_id,stage,is_held,updated_at) values (%(order_id)s,%(business_id)s,%(stage)s,false,now()) on conflict (order_id) do update set stage=excluded.stage,is_held=false,hold_reason=null,held_at=null,updated_at=now() returning order_id", {"order_id": str(order["id"]), "business_id": str(business["id"]), "stage": stage})
    client.table("kitchen_events").insert({"business_id": str(business["id"]), "order_id": str(order["id"]), "old_status": current["status"], "new_status": stage, "changed_by": None}).execute()
    _record(client, business, device, event_id, action, UUID(str(order["id"])), {"previous": current["status"], "next": stage, "reason": reason})
    _audit(client, business, device, action, "orders", UUID(str(order["id"])), {"previous": current["status"], "next": stage, "reason": reason})
    return _ticket(client, business, order_service.get_order(client, UUID(str(order["id"])), UUID(str(business["id"]))))


def start(client: DbClient, session: str | None, order_id: UUID, payload: KitchenActionRequest) -> dict:
    business, device = _kitchen(client, session)
    return _set_stage(client, business, device, order_service.get_order(client, order_id, UUID(str(business["id"]))), "preparing", payload.event_id, "kitchen_order_started")


def hold(client: DbClient, session: str | None, order_id: UUID, payload: KitchenHoldRequest) -> dict:
    business, device = _kitchen(client, session); order = order_service.get_order(client, order_id, UUID(str(business["id"]))); _lock(client, order_id)
    if _seen(client, business, device, payload.event_id): return _ticket(client, business, order)
    if order["status"] not in {"pending", "preparing"}: raise HTTPException(status_code=409, detail="Only New or Preparing orders can be held.")
    client.execute_one("insert into kitchen_order_states (order_id,business_id,stage,is_held,hold_reason,held_at,updated_at) values (%(order_id)s,%(business_id)s,%(stage)s,true,%(reason)s,now(),now()) on conflict (order_id) do update set stage=excluded.stage,is_held=true,hold_reason=excluded.hold_reason,held_at=now(),updated_at=now() returning order_id", {"order_id": str(order_id), "business_id": str(business["id"]), "stage": order["status"], "reason": payload.reason.strip()})
    _record(client, business, device, payload.event_id, "kitchen_order_held", order_id, {"reason": payload.reason.strip()}); _audit(client, business, device, "kitchen_order_held", "orders", order_id, {"reason": payload.reason.strip()})
    return _ticket(client, business, order)


def resume(client: DbClient, session: str | None, order_id: UUID, payload: KitchenActionRequest) -> dict:
    business, device = _kitchen(client, session); order = order_service.get_order(client, order_id, UUID(str(business["id"]))); _lock(client, order_id)
    if _seen(client, business, device, payload.event_id): return _ticket(client, business, order)
    row = client.execute_one("update kitchen_order_states set is_held=false,updated_at=now() where order_id=%(order_id)s and business_id=%(business_id)s and is_held=true returning order_id", {"order_id": str(order_id), "business_id": str(business["id"])})
    if not row: raise HTTPException(status_code=409, detail="Order is not held.")
    _record(client, business, device, payload.event_id, "kitchen_order_resumed", order_id, {}); _audit(client, business, device, "kitchen_order_resumed", "orders", order_id, {})
    return _ticket(client, business, order)


def complete_item(client: DbClient, session: str | None, order_id: UUID, item_id: UUID, payload: KitchenItemCompletion) -> dict:
    business, device = _kitchen(client, session); order = order_service.get_order(client, order_id, UUID(str(business["id"]))); _lock(client, order_id)
    if _seen(client, business, device, payload.event_id): return _ticket(client, business, order)
    item = next((row for row in (order.get("items") or order.get("order_items") or []) if str(row.get("id")) == str(item_id)), None)
    if not item: raise HTTPException(status_code=404, detail="Order item not found.")
    if payload.completed_quantity > int(item["quantity"]): raise HTTPException(status_code=422, detail="Completed quantity cannot exceed ordered quantity.")
    client.execute_one("insert into kitchen_item_states (order_item_id,order_id,business_id,completed_quantity,updated_at) values (%(item_id)s,%(order_id)s,%(business_id)s,%(quantity)s,now()) on conflict (order_item_id) do update set completed_quantity=excluded.completed_quantity,updated_at=now() returning order_item_id", {"item_id": str(item_id), "order_id": str(order_id), "business_id": str(business["id"]), "quantity": payload.completed_quantity})
    _record(client, business, device, payload.event_id, "kitchen_item_completion", order_id, {"item_id": str(item_id), "completed_quantity": payload.completed_quantity}); _audit(client, business, device, "kitchen_item_completion", "order_items", item_id, {"order_id": str(order_id), "completed_quantity": payload.completed_quantity})
    return _ticket(client, business, order_service.get_order(client, order_id, UUID(str(business["id"]))))


def _override(client: DbClient, business: dict, device: dict, token: str | None, action: str) -> None:
    try: claims = jwt.decode(token or "", get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
    except jwt.PyJWTError as exc: raise HTTPException(status_code=403, detail="A current manager override is required.") from exc
    if claims.get("type") != "kitchen_override" or claims.get("action") != action or claims.get("business_id") != str(business["id"]) or claims.get("device_id") != str(device["id"]): raise HTTPException(status_code=403, detail="Override does not authorize this Kitchen action.")


def override(client: DbClient, session: str | None, payload: KitchenOverrideRequest) -> dict:
    business, device = _kitchen(client, session); pin_service.verify_owner_pin(client, business["slug"], OwnerPinVerify(pin=payload.pin)); now = datetime.now(timezone.utc)
    token = jwt.encode({"type": "kitchen_override", "action": payload.action, "business_id": str(business["id"]), "device_id": str(device["id"]), "iat": now, "exp": now + timedelta(minutes=5)}, get_settings().jwt_secret, algorithm=get_settings().jwt_algorithm)
    _audit(client, business, device, "kitchen_manager_override_authorized", "devices", UUID(str(device["id"])), {"action": payload.action, "reason": payload.reason, "actor_type": "owner_pin"})
    return {"override_token": token, "expires_at": (now + timedelta(minutes=5)).isoformat()}


def ready(client: DbClient, session: str | None, order_id: UUID, payload: KitchenActionRequest) -> dict:
    business, device = _kitchen(client, session); order = order_service.get_order(client, order_id, UUID(str(business["id"]))); items = order.get("items") or order.get("order_items") or []
    states = {str(row["order_item_id"]): int(row["completed_quantity"]) for row in client.fetch_all("select order_item_id,completed_quantity from kitchen_item_states where order_id=%(order_id)s", {"order_id": str(order_id)})}
    incomplete = [item for item in items if states.get(str(item.get("id")), 0) < int(item.get("quantity") or 0)]
    if incomplete: _override(client, business, device, payload.override_token, "ready_incomplete")
    return _set_stage(client, business, device, order, "ready", payload.event_id, "kitchen_order_ready", payload.reason)


def recall(client: DbClient, session: str | None, order_id: UUID, payload: KitchenActionRequest) -> dict:
    business, device = _kitchen(client, session); _override(client, business, device, payload.override_token, "recall")
    return _set_stage(client, business, device, order_service.get_order(client, order_id, UUID(str(business["id"]))), "preparing", payload.event_id, "kitchen_order_recalled", payload.reason)


def all_day(client: DbClient, session: str | None) -> dict:
    data = board(client, session); totals: dict[str, dict] = {}
    for order in data["orders"]:
        if order["status"] not in {"pending", "preparing", "ready"}: continue
        stage = order["kitchen"].get("stage") or order["status"]
        for item in order.get("items") or []:
            row = totals.setdefault(str(item.get("product_id") or item.get("product_name")), {"item": item.get("product_name"), "total_required": 0, "new_quantity": 0, "preparing_quantity": 0, "held_quantity": 0, "completed_quantity": 0})
            quantity = int(item.get("quantity") or 0); row["total_required"] += quantity; row["completed_quantity"] += int(item.get("completed_quantity") or 0)
            if order["kitchen"].get("is_held"): row["held_quantity"] += quantity
            elif stage == "pending": row["new_quantity"] += quantity
            elif stage == "preparing": row["preparing_quantity"] += quantity
    return {"items": list(totals.values())}


def availability(client: DbClient, session: str | None) -> dict:
    business, device = _kitchen(client, session)
    rows = client.table("products").select("*").eq("business_id", str(business["id"])).order("name").limit(500).execute().data or []
    return {"products": rows, "device": device}


def set_availability(client: DbClient, session: str | None, product_id: UUID, payload: KitchenAvailabilityUpdate) -> dict:
    business, device = _kitchen(client, session); _lock(client, product_id)
    if _seen(client, business, device, payload.event_id): return client.table("products").select("*").eq("id", str(product_id)).eq("business_id", str(business["id"])).limit(1).execute().data[0]
    product = client.table("products").select("*").eq("id", str(product_id)).eq("business_id", str(business["id"])).limit(1).execute().data
    if not product: raise HTTPException(status_code=404, detail="Product not found.")
    available = payload.status == "available"; update = {"is_available": available, "menu_status": "shown" if available else "hidden"}
    row = client.table("products").update(update).eq("id", str(product_id)).eq("business_id", str(business["id"])).execute().data[0]
    _record(client, business, device, payload.event_id, "kitchen_availability_updated", product_id, {"status": payload.status}); _audit(client, business, device, "kitchen_availability_updated", "product", product_id, {"status": payload.status}); invalidate_business(client, str(business["id"]))
    return row


def preferences(client: DbClient, session: str | None, payload: KitchenPreferenceUpdate | None = None) -> dict:
    business, device = _kitchen(client, session)
    if payload:
        data = payload.model_dump(exclude_none=True); data["device_id"] = str(device["id"]); data["updated_at"] = datetime.now(timezone.utc).isoformat()
        row = client.execute_one("insert into kitchen_device_preferences (device_id,sound_enabled,sound_volume,updated_at) values (%(device_id)s,coalesce(%(sound_enabled)s,true),coalesce(%(sound_volume)s,70),%(updated_at)s) on conflict (device_id) do update set sound_enabled=coalesce(%(sound_enabled)s,kitchen_device_preferences.sound_enabled),sound_volume=coalesce(%(sound_volume)s,kitchen_device_preferences.sound_volume),updated_at=excluded.updated_at returning *", {**{"sound_enabled": None, "sound_volume": None}, **data})
        return row or {}
    return client.execute_one("select * from kitchen_device_preferences where device_id=%(device_id)s", {"device_id": str(device["id"])}) or {"sound_enabled": True, "sound_volume": 70}
