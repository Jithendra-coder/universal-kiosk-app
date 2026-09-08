from uuid import UUID
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from database import DbClient
from services import availability_service, cache_service, payment_service, pin_service, setup_service
from services.business_service import get_business_by_slug
from services.product_service import list_products


def get_kiosk_payload(client: DbClient, business_slug: str, use_draft: bool = False, location_id: str | None = None) -> dict:
    cached = None if use_draft or location_id else cache_service.get_menu(business_slug)
    if cached:
        return cached

    business = get_business_by_slug(client, business_slug)
    business_id = UUID(business["id"])
    configuration = setup_service.canonical_configuration(client, business)[1] if use_draft else setup_service.live_configuration(client, business)
    configured_business = configuration["business"]
    categories = [row for row in configuration.get("categories", []) if row.get("is_active")]
    show_unavailable = bool(configured_business.get("display_show_unavailable", True))
    current_products = {row["id"]: row for row in list_products(client, business_id, include_unavailable=True)}
    products = []
    availability_rules = configuration.get("availability_rules", [])
    for configured_product in configuration.get("products", []):
        if configured_product.get("menu_status") not in {"shown", "unavailable"}:
            continue
        current = current_products.get(configured_product["id"], {})
        product = {**configured_product, **{key: current.get(key) for key in ("stock_quantity", "sold_today") if key in current}}
        availability = availability_service.resolve_product(product, configured_business, availability_rules, location_id)
        orderable = _is_product_orderable(product, configured_business, availability["available"])
        if orderable or show_unavailable:
            product["is_available"] = orderable
            product["availability_source"] = availability["source"]
            product["availability_reason"] = availability.get("reason")
            product["next_change_at"] = availability.get("next_change_at")
            products.append(product)
    options_by_group: dict[str, list[dict]] = {}
    for option in configuration.get("modifier_options", []):
        options_by_group.setdefault(option["group_id"], []).append(option)
    modifiers: dict[str, list[dict]] = {}
    for group in configuration.get("modifier_groups", []):
        modifiers.setdefault(group["product_id"], []).append({**group, "options": options_by_group.get(group["id"], [])})
    for product in products:
        product["modifier_groups"] = modifiers.get(product["id"], [])
    payload = {
        "business": _public_business(client, configured_business, business),
        "categories": categories,
        "products": products,
    }
    if not use_draft and not location_id:
        cache_service.set_menu(business_slug, payload)
    return payload


def _public_business(client: DbClient, business: dict, operational_business: dict | None = None) -> dict:
    keys = [
        "id",
        "name",
        "slug",
        "type",
        "tagline",
        "business_subtype",
        "contact_phone",
        "logo_path",
        "logo_shape",
        "logo_scale",
        "logo_position_x",
        "logo_position_y",
        "brand_color",
        "kiosk_layout_id",
        "kiosk_theme",
        "kiosk_layout",
        "kiosk_screen_orientation",
        "kiosk_screen_size",
        "kiosk_cart_mode",
        "kiosk_start_screen_enabled",
        "kiosk_start_text_position",
        "kiosk_touch_to_start",
        "welcome_screen",
        "kiosk_lock_settings",
        "kiosk_order_settings",
        "display_show_tagline",
        "display_show_category_images",
        "display_show_item_descriptions",
        "display_show_prices",
        "display_show_unavailable",
        "idle_timeout_seconds",
        "order_reset_seconds",
        "default_language",
        "sound_effects_enabled",
        "offer_enabled",
        "offer_title",
        "offer_subtitle",
        "offer_badge",
        "offer_cta",
        "offer_image_path",
        "offer_background",
        "currency_code",
        "currency_symbol",
        "tax_percent",
        "order_modes",
        "store_schedule",
        "receipt_settings",
        "address_line1",
        "city",
        "opening_time",
        "closing_time",
        "timezone",
        "is_active",
    ]
    public = {key: business.get(key) for key in keys}
    operational = operational_business or business
    public["is_active"] = operational.get("is_active")
    public["kiosk_lock_settings"] = pin_service.public_lock_state(operational)
    public["payment_summary"] = payment_service.public_payment_summary(client, operational)
    return public


def _is_product_orderable(product: dict, business: dict, resolved_available: bool | None = None) -> bool:
    if resolved_available is False or resolved_available is None and not product.get("is_available"):
        return False
    if resolved_available is None and not _within_product_days(product, business):
        return False
    if resolved_available is None and not _within_product_time(product, business):
        return False
    if product.get("track_stock") and product.get("stock_quantity") is not None:
        if int(product.get("stock_quantity") or 0) <= 0:
            return False
    daily_limit = product.get("daily_limit")
    if daily_limit is not None and int(product.get("sold_today") or 0) >= int(daily_limit):
        return False
    return True


def _within_product_days(product: dict, business: dict) -> bool:
    if product.get("availability_type") != "scheduled":
        return True
    days = product.get("available_days") or []
    if not days:
        return True
    try:
        tz = ZoneInfo(business.get("timezone") or "UTC")
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    today = datetime.now(tz).strftime("%A").lower()
    normalized = {str(day).strip().lower() for day in days}
    return today in normalized


def _within_product_time(product: dict, business: dict) -> bool:
    start = product.get("availability_start_time")
    end = product.get("availability_end_time")
    if not start and not end:
        return True

    try:
        tz = ZoneInfo(business.get("timezone") or "UTC")
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")

    now_time = datetime.now(tz).time()
    start_time = _parse_time(start)
    end_time = _parse_time(end)
    if start_time and end_time:
        if start_time <= end_time:
            return start_time <= now_time <= end_time
        return now_time >= start_time or now_time <= end_time
    if start_time:
        return now_time >= start_time
    if end_time:
        return now_time <= end_time
    return True


def _parse_time(value):
    if not value:
        return None
    if hasattr(value, "hour"):
        return value
    try:
        return datetime.strptime(str(value)[:5], "%H:%M").time()
    except ValueError:
        return None
