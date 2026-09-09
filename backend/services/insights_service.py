from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from database import DbClient
from schemas import OrderStatus
from services.analytics_service import (
    ANALYTICS_ORDER_COLUMNS,
    FAILED_PAYMENT_STATUSES,
    _aware,
    _is_completed_order,
    _parse_dt,
    dashboard_stats,
)


def compute_comprehensive_insights(
    client: DbClient,
    business_id: UUID,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    location_id: Optional[UUID] = None,
    comparison: str = "previous",
) -> Dict[str, Any]:
    # 1. Primary stats
    primary_stats = dashboard_stats(
        client, business_id, start=start, end=end, location_id=location_id
    )

    # 2. Previous period stats if requested
    previous_stats = None
    if comparison == "previous":
        now = datetime.now(timezone.utc)
        p_end = _aware(end or now)
        p_start = _aware(start) if start else p_end - timedelta(days=6)
        duration = p_end - p_start
        prev_end = p_start - timedelta(seconds=1)
        prev_start = prev_end - duration
        previous_stats = dashboard_stats(
            client, business_id, start=prev_start, end=prev_end, location_id=location_id
        )

    # 3. Time-window orders query
    now = datetime.now(timezone.utc)
    period_end = _aware(end or now)
    today_start = period_end.replace(hour=0, minute=0, second=0, microsecond=0)
    period_start = _aware(start) if start else today_start - timedelta(days=6)

    order_query = (
        client.table("orders")
        .select(
            "id, order_number, public_token, status, payment_status, total_amount, order_type, payment_method, location_id, placed_at"
        )
        .eq("business_id", str(business_id))
        .gte("placed_at", period_start.isoformat())
        .lte("placed_at", period_end.isoformat())
        .order("placed_at", desc=True)
    )
    if location_id:
        order_query = order_query.eq("location_id", str(location_id))

    orders_data = order_query.execute().data or []
    for o in orders_data:
        o["_placed_at"] = _parse_dt(o.get("placed_at"))

    completed_orders = [o for o in orders_data if _is_completed_order(o)]

    # 4. Hourly / Peak Times Aggregation
    hourly_counts = defaultdict(int)
    for o in completed_orders:
        hour = o["_placed_at"].hour
        hourly_counts[hour] += 1

    peak_times = [
        {"hour": f"{h}:00", "orders": count}
        for h, count in sorted(hourly_counts.items())
    ]
    busiest_hour = (
        max(hourly_counts.items(), key=lambda x: x[1])[0]
        if hourly_counts
        else None
    )
    busiest_label = f"{busiest_hour}:00" if busiest_hour is not None else "Not enough data"

    # 5. Location breakdown
    location_totals = defaultdict(lambda: {"orders": 0, "sales": 0.0})
    for o in completed_orders:
        loc_id = str(o.get("location_id") or "all")
        location_totals[loc_id]["orders"] += 1
        location_totals[loc_id]["sales"] += float(o.get("total_amount") or 0)

    location_performance = [
        {
            "location_id": loc_id,
            "orders": data["orders"],
            "sales": round(data["sales"], 2),
            "average_order": (
                round(data["sales"] / data["orders"], 2) if data["orders"] else 0.0
            ),
        }
        for loc_id, data in location_totals.items()
    ]

    # 6. Category breakdown
    order_ids = [o["id"] for o in completed_orders[:150]]
    category_summary = []
    if order_ids:
        categories_resp = (
            client.table("categories")
            .select("id, name")
            .eq("business_id", str(business_id))
            .execute()
        )
        categories = {
            str(c["id"]): c["name"] for c in (categories_resp.data or [])
        }

        products_resp = (
            client.table("products")
            .select("id, name, category_id, price")
            .eq("business_id", str(business_id))
            .execute()
        )
        product_cat_map = {
            str(p["id"]): str(p.get("category_id") or "")
            for p in (products_resp.data or [])
        }

        cat_totals = defaultdict(lambda: {"items_sold": 0, "sales": 0.0})
        item_rows = (
            client.table("order_items")
            .select("product_id, quantity, total_price")
            .eq("business_id", str(business_id))
            .in_("order_id", order_ids)
            .execute()
            .data
            or []
        )
        for row in item_rows:
            p_id = str(row.get("product_id") or "")
            cat_id = product_cat_map.get(p_id, "uncategorized")
            cat_totals[cat_id]["items_sold"] += int(row.get("quantity") or 0)
            cat_totals[cat_id]["sales"] += float(row.get("total_price") or 0)

        for cat_id, stats in cat_totals.items():
            cat_name = categories.get(cat_id, "Uncategorized")
            category_summary.append(
                {
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "items_sold": stats["items_sold"],
                    "sales": round(stats["sales"], 2),
                }
            )
        category_summary.sort(key=lambda x: -x["sales"])

    # 7. Recent orders formatted subset
    clean_orders = [
        {
            "id": o["id"],
            "order_number": o.get("order_number"),
            "public_token": o.get("public_token"),
            "status": o.get("status"),
            "total_amount": float(o.get("total_amount") or 0),
            "order_type": o.get("order_type"),
            "location_id": o.get("location_id"),
            "placed_at": o.get("placed_at"),
        }
        for o in orders_data[:25]
    ]

    return {
        "stats": primary_stats,
        "previous": previous_stats,
        "peak_times": peak_times,
        "busiest_hour": busiest_label,
        "location_performance": location_performance,
        "category_performance": category_summary,
        "recent_orders": clean_orders,
        "completed_count": len(completed_orders),
    }
