from __future__ import annotations

from uuid import UUID

from psycopg.types.json import Jsonb

from database import DbClient
from schemas import AlertStatusUpdate
from services import device_service
from services.business_service import ADMIN_ROLES, assert_business_access


def list_alerts(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    business = assert_business_access(client, business_id, user_id, ADMIN_ROLES)
    generate_alerts(client, business)
    alerts = (
        client.table("alerts")
        .select("*")
        .eq("business_id", str(business_id))
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return {"alerts": alerts, "summary": summarize(alerts)}


def alert_summary(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    business = assert_business_access(client, business_id, user_id, ADMIN_ROLES)
    generate_alerts(client, business)
    rows = client.table("alerts").select("status,severity").eq("business_id", str(business_id)).execute().data or []
    return summarize(rows)


def update_alert_status(client: DbClient, alert_id: UUID, user_id: UUID, payload: AlertStatusUpdate) -> dict:
    assert_business_access(client, payload.business_id, user_id, ADMIN_ROLES)
    update = {"status": payload.status, "updated_at": "now()"}
    if payload.status == "resolved":
        row = client.execute_one(
            """
            update alerts
            set status = 'resolved',
                resolved_at = now(),
                updated_at = now()
            where id = %(alert_id)s
              and business_id = %(business_id)s
            returning *
            """,
            {"alert_id": str(alert_id), "business_id": str(payload.business_id)},
        )
    else:
        row = client.execute_one(
            """
            update alerts
            set status = %(status)s,
                resolved_at = null,
                updated_at = now()
            where id = %(alert_id)s
              and business_id = %(business_id)s
            returning *
            """,
            {"status": payload.status, "alert_id": str(alert_id), "business_id": str(payload.business_id)},
        )
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Alert not found.")
    return row


def generate_alerts(client: DbClient, business: dict) -> None:
    business_id = UUID(str(business["id"]))
    device_service.refresh_offline_device_alerts(client, business_id)
    _low_stock_alerts(client, business_id)
    _payment_failure_alerts(client, business_id)
    _ordering_blocked_alert(client, business)


def summarize(alerts: list[dict]) -> dict:
    unresolved = [alert for alert in alerts if alert.get("status") != "resolved"]
    return {
        "unresolved_count": len(unresolved),
        "critical_count": sum(1 for alert in unresolved if alert.get("severity") == "critical"),
        "warning_count": sum(1 for alert in unresolved if alert.get("severity") == "warning"),
        "info_count": sum(1 for alert in unresolved if alert.get("severity") == "info"),
    }


def _low_stock_alerts(client: DbClient, business_id: UUID) -> None:
    products = (
        client.table("products")
        .select("*")
        .eq("business_id", str(business_id))
        .eq("track_stock", True)
        .execute()
        .data
        or []
    )
    for product in products:
        stock = product.get("stock_quantity")
        if stock is None:
            continue
        threshold = _low_stock_threshold(product)
        if int(stock) <= threshold:
            _insert_alert(
                client,
                business_id,
                "low_stock",
                "warning",
                "Low stock",
                f"{product.get('name')} has {stock} left.",
                "inventory",
                f"product:{product.get('id')}:low_stock",
                {"product_id": product.get("id"), "stock_quantity": stock, "threshold": threshold},
            )


def _payment_failure_alerts(client: DbClient, business_id: UUID) -> None:
    rows = client.table("payments").select("*").eq("business_id", str(business_id)).in_("status", ["failed", "cancelled", "expired"]).limit(20).execute().data or []
    for payment in rows:
        _insert_alert(
            client,
            business_id,
            "payment_failure",
            "warning",
            "Payment failed",
            f"{payment.get('provider') or 'Payment'} record {payment.get('id')} is {payment.get('status')}.",
            "payments",
            f"payment:{payment.get('id')}:failed",
            {"payment_id": payment.get("id"), "order_id": payment.get("order_id")},
        )


def _ordering_blocked_alert(client: DbClient, business: dict) -> None:
    settings = business.get("kiosk_order_settings") or {}
    schedule = business.get("store_schedule") or {}
    if business.get("is_active", True) and settings.get("checkout_enabled") is not False and settings.get("checkout_mode") != "display" and not schedule.get("emergency_closed"):
        return
    reason = "Kiosk ordering is blocked by settings or emergency closure."
    _insert_alert(
        client,
        UUID(str(business["id"])),
        "ordering_blocked",
        "info",
        "Kiosk ordering blocked",
        reason,
        "kiosk",
        "kiosk:ordering_blocked",
        {"is_active": business.get("is_active"), "checkout_mode": settings.get("checkout_mode"), "emergency_closed": schedule.get("emergency_closed")},
    )


def _insert_alert(
    client: DbClient,
    business_id: UUID,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    source: str,
    dedupe_key: str,
    metadata: dict,
) -> None:
    client.execute_one(
        """
        insert into alerts (business_id, type, severity, title, message, source, status, dedupe_key, metadata)
        values (%(business_id)s, %(type)s, %(severity)s, %(title)s, %(message)s, %(source)s, 'open', %(dedupe_key)s, %(metadata)s)
        on conflict (business_id, dedupe_key) do update
        set message = excluded.message,
            severity = excluded.severity,
            updated_at = now()
        where alerts.status <> 'resolved'
        returning id
        """,
        {
            "business_id": str(business_id),
            "type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "source": source,
            "dedupe_key": dedupe_key,
            "metadata": Jsonb(metadata),
        },
    )


def _low_stock_threshold(product: dict) -> int:
    metadata = product.get("metadata") or {}
    for key in ["low_stock_alert_quantity", "kitchen_remind_at", "reminderPoint"]:
        try:
            value = int(metadata.get(key) or 0)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    return 2
