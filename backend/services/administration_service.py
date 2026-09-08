from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from database import DbClient
from schemas import BusinessLocationCreate, BusinessLocationUpdate
from services.business_service import FULL_ACCESS_ROLES, assert_business_access


def _audit(client: DbClient, business_id: UUID, user_id: UUID, action: str, entity: str, entity_id: UUID | str | None, metadata: dict | None = None) -> None:
    client.table("audit_logs").insert({
        "business_id": str(business_id), "user_id": str(user_id), "action": action,
        "entity": entity, "entity_id": str(entity_id) if entity_id else None, "metadata": metadata or {},
    }).execute()


def list_locations(client: DbClient, business_id: UUID, user_id: UUID, search: str | None = None) -> list[dict]:
    assert_business_access(client, business_id, user_id, FULL_ACCESS_ROLES)
    rows = client.fetch_all(
        """
        select l.*, count(distinct p.id)::int as promotion_count, count(distinct q.id)::int as qr_code_count,
               count(distinct d.id)::int as device_count
        from business_locations l
        left join kiosk_promotion_locations pl on pl.location_id = l.id
        left join kiosk_promotions p on p.id = pl.promotion_id and p.status in ('scheduled', 'active', 'paused')
        left join kiosk_qr_codes q on q.location_id = l.id and q.active = true
        left join devices d on d.business_id = l.business_id and d.location_label = l.name and d.is_active = true
        where l.business_id = %(business_id)s
          and (%(search)s::text is null or l.name ilike %(search_like)s or coalesce(l.city, '') ilike %(search_like)s)
        group by l.id order by l.name asc limit 250
        """,
        {"business_id": str(business_id), "search": search or None, "search_like": f"%{search}%"},
    )
    return rows


def get_location(client: DbClient, business_id: UUID, user_id: UUID, location_id: UUID) -> dict:
    rows = [row for row in list_locations(client, business_id, user_id) if str(row["id"]) == str(location_id)]
    if not rows:
        raise HTTPException(status_code=404, detail="Location not found.")
    return rows[0]


def create_location(client: DbClient, business_id: UUID, user_id: UUID, payload: BusinessLocationCreate) -> dict:
    assert_business_access(client, business_id, user_id, FULL_ACCESS_ROLES)
    data = payload.model_dump(exclude_none=True)
    data.update({"business_id": str(business_id), "created_by": str(user_id), "updated_by": str(user_id)})
    row = client.table("business_locations").insert(data).execute().data
    if not row:
        raise HTTPException(status_code=400, detail="Location could not be created.")
    _audit(client, business_id, user_id, "location_created", "business_location", row[0]["id"], {"name": row[0]["name"]})
    from services.webhook_delivery_service import enqueue_event
    enqueue_event(client, business_id, "location.created", {"location_id": str(row[0]["id"]), "name": row[0]["name"]}, UUID(str(row[0]["id"])))
    return row[0]


def update_location(client: DbClient, business_id: UUID, user_id: UUID, location_id: UUID, payload: BusinessLocationUpdate) -> dict:
    previous = get_location(client, business_id, user_id, location_id)
    data = payload.model_dump(exclude_none=True, exclude={"use_business_defaults"})
    if payload.use_business_defaults:
        data.update({"timezone": None, "currency_code": None, "default_language": None, "tax_region": None, "ordering_settings": {}, "receipt_settings": {}})
    if not data:
        return previous
    data.update({"updated_by": str(user_id)})
    row = client.table("business_locations").update(data).eq("id", str(location_id)).eq("business_id", str(business_id)).execute().data
    if not row:
        raise HTTPException(status_code=404, detail="Location not found.")
    _audit(client, business_id, user_id, "location_updated", "business_location", location_id, {"fields": sorted(data)})
    from services.webhook_delivery_service import enqueue_event
    enqueue_event(client, business_id, "location.updated", {"location_id": str(location_id), "fields": sorted(data)}, location_id)
    return row[0]


def deactivate_location(client: DbClient, business_id: UUID, user_id: UUID, location_id: UUID) -> dict:
    return update_location(client, business_id, user_id, location_id, BusinessLocationUpdate(operating_status="inactive"))


def delete_location(client: DbClient, business_id: UUID, user_id: UUID, location_id: UUID) -> None:
    location = get_location(client, business_id, user_id, location_id)
    if location.get("promotion_count") or location.get("qr_code_count") or location.get("device_count"):
        raise HTTPException(status_code=409, detail="Deactivate this location before removing dependent promotions, QR codes, or devices.")
    client.table("business_locations").delete().eq("id", str(location_id)).eq("business_id", str(business_id)).execute()
    _audit(client, business_id, user_id, "location_deleted", "business_location", location_id, {"name": location["name"]})


def activity_log(client: DbClient, business_id: UUID, user_id: UUID, search: str | None = None, limit: int = 50, offset: int = 0) -> dict:
    assert_business_access(client, business_id, user_id, FULL_ACCESS_ROLES)
    bounded_limit = max(1, min(limit, 100))
    rows = client.fetch_all(
        """
        select a.id, a.business_id, a.user_id, a.action, a.entity, a.entity_id, a.metadata, a.created_at,
               u.full_name as actor_name, u.email as actor_email, bs.role as actor_role
        from audit_logs a
        left join app_users u on u.id = a.user_id
        left join business_staff bs on bs.business_id = a.business_id and bs.user_id = a.user_id
        where a.business_id = %(business_id)s
          and (%(search)s is null or a.action ilike %(search_like)s or coalesce(a.entity, '') ilike %(search_like)s or coalesce(u.email, '') ilike %(search_like)s)
        order by a.created_at desc limit %(limit)s offset %(offset)s
        """,
        {"business_id": str(business_id), "search": search or None, "search_like": f"%{search}%", "limit": bounded_limit, "offset": max(0, offset)},
    )
    return {"events": [_safe_event(row) for row in rows], "has_more": len(rows) == bounded_limit}


def _safe_event(row: dict) -> dict:
    safe = dict(row)
    metadata = dict(safe.get("metadata") or {})
    for key in list(metadata):
        if any(secret in key.lower() for secret in ("secret", "token", "password", "key", "signature", "payload")):
            metadata[key] = "••••••••"
    safe["metadata"] = metadata
    return safe


def overview(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    business = assert_business_access(client, business_id, user_id, FULL_ACCESS_ROLES)
    locations = list_locations(client, business_id, user_id)
    payments = client.table("business_payment_accounts").select("provider,connection_status,is_enabled,is_default").eq("business_id", str(business_id)).execute().data or []
    staff = client.table("business_staff").select("id").eq("business_id", str(business_id)).execute().data or []
    events = activity_log(client, business_id, user_id, limit=10)["events"]
    checks = [
        {"key": "payments", "status": "ready" if any(row.get("connection_status") in {"active", "connected"} and row.get("is_enabled") for row in payments) else "attention", "detail": "A payment provider is connected." if payments else "Connect Stripe, Razorpay, or Paytm."},
        {"key": "locations", "status": "ready" if locations else "attention", "detail": f"{len(locations)} location{'s' if len(locations) != 1 else ''} configured." if locations else "Add the first location."},
        {"key": "team", "status": "ready" if staff else "attention", "detail": f"{len(staff)} team member{'s' if len(staff) != 1 else ''} have access." if staff else "Invite a team member when needed."},
        {"key": "business_settings", "status": "ready" if business.get("timezone") and business.get("currency_code") else "attention", "detail": "Regional defaults are configured." if business.get("timezone") and business.get("currency_code") else "Complete regional defaults."},
        {"key": "integrations", "status": "unavailable", "detail": "No external integration contract is connected."},
    ]
    return {"checks": checks, "recent_activity": events, "updated_at": business.get("updated_at")}
