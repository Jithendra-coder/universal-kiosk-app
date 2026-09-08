"""Preview kiosk sandbox service.

This file is preview sandbox only. It must not call real kiosk/order/payment/PIN/kitchen/cache APIs.
"""

from datetime import datetime, timezone
from uuid import UUID

from database import DbClient
from schemas_preview_kiosk import PreviewKioskRenderRequest
from services import business_service
from services.product_service import list_categories, list_products


SAFE_BUSINESS_DRAFT_KEYS = {
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
    "kiosk_theme",
    "kiosk_layout",
    "kiosk_screen_orientation",
    "kiosk_screen_size",
    "kiosk_cart_mode",
    "kiosk_start_screen_enabled",
    "kiosk_start_text_position",
    "kiosk_touch_to_start",
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
    "address_line1",
    "city",
    "state",
    "postal_code",
    "country",
    "timezone",
    "opening_time",
    "closing_time",
    "order_modes",
    "store_schedule",
    "receipt_settings",
    "kiosk_order_settings",
}


def render_preview_kiosk(client: DbClient, user_id: UUID, payload: PreviewKioskRenderRequest) -> dict:
    business = business_service.assert_business_access(
        client,
        payload.business_id,
        user_id,
        business_service.ADMIN_ROLES,
    )
    business_id = UUID(business["id"])
    preview_business = _strip_pin_like_values({**business, **_safe_preview_draft(payload.draft)})
    categories = [category for category in list_categories(client, business_id) if category.get("is_active")]
    products = [
        product
        for product in list_products(client, business_id, include_unavailable=True)
        if product.get("is_available")
    ]
    return {
        "business": preview_business,
        "categories": categories,
        "products": products,
        "source": "preview_sandbox",
        "generated_at": _now_iso(),
    }



def _safe_preview_draft(draft: dict) -> dict:
    safe = {}
    for key, value in (draft or {}).items():
        if key not in SAFE_BUSINESS_DRAFT_KEYS:
            continue
        safe[key] = _strip_pin_like_values(value)
    return safe


def _strip_pin_like_values(value):
    if isinstance(value, dict):
        return {
            key: _strip_pin_like_values(child)
            for key, child in value.items()
            if "pin" not in str(key).lower()
        }
    if isinstance(value, list):
        return [_strip_pin_like_values(child) for child in value]
    return value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
