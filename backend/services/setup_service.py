from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from database import DbClient
from schemas import KioskExperienceTestOrderCreate, KioskSetupUpdate, KioskTestOrderCreate
from services import availability_service, business_service, cache_service


SETUP_VERSION = 2
VOLATILE_KEYS = {"created_at", "updated_at", "started_at", "completed_at", "published_at"}
BUSINESS_CONFIG_KEYS = (
    "id", "name", "slug", "type", "business_subtype", "contact_phone", "tagline",
    "logo_path", "logo_shape", "logo_scale", "logo_position_x", "logo_position_y",
    "brand_color", "kiosk_layout_id", "kiosk_theme", "kiosk_layout", "kiosk_screen_orientation",
    "kiosk_screen_size", "kiosk_cart_mode", "kiosk_start_screen_enabled",
    "kiosk_start_text_position", "kiosk_touch_to_start", "welcome_screen", "kiosk_start_screen_settings",
    "display_show_tagline", "display_show_category_images", "display_show_item_descriptions",
    "display_show_prices", "display_show_unavailable", "idle_timeout_seconds",
    "order_reset_seconds", "default_language", "sound_effects_enabled", "offer_enabled",
    "offer_title", "offer_subtitle", "offer_badge", "offer_cta", "offer_image_path",
    "offer_background", "currency_code", "currency_symbol", "tax_percent", "order_modes",
    "store_schedule", "opening_time", "closing_time", "timezone", "address_line1",
    "city", "state", "postal_code", "country",
)


def assert_workspace_access(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    return business_service.assert_business_access(client, business_id, user_id, business_service.FULL_ACCESS_ROLES)


def setup_overview(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    business = assert_workspace_access(client, business_id, user_id)
    _ensure_legacy_live_baseline(client, business, user_id)
    return _overview(client, business)


def update_setup(client: DbClient, business_id: UUID, user_id: UUID, payload: KioskSetupUpdate) -> dict:
    assert_workspace_access(client, business_id, user_id)
    business = _locked_business(client, business_id)
    setup = _setup_state(business)
    _assert_revision(setup, payload.expected_revision)
    if payload.current_step is not None:
        setup["currentStep"] = payload.current_step
    if payload.intro_pending is not None:
        setup["introPending"] = payload.intro_pending
    if payload.active is not None:
        setup["active"] = payload.active
    setup["revision"] = payload.expected_revision + 1
    return _overview(client, _save_setup(client, business, setup))


def attest_preview(client: DbClient, business_id: UUID, user_id: UUID, event_version: int) -> dict:
    assert_workspace_access(client, business_id, user_id)
    business = _locked_business(client, business_id)
    _lock_configuration_tables(client)
    signature, _ = canonical_configuration(client, business)
    row = client.fetch_one(
        """insert into kiosk_setup_attestations
        (business_id, kiosk_id, kind, operational_mode, config_signature, event_version, confirmation_reached, successful_result, created_by)
        values (%(business_id)s, %(kiosk_id)s, 'preview', 'preview', %(signature)s, %(event_version)s, false, null, %(user_id)s) returning *""",
        {"business_id": str(business_id), "kiosk_id": business["slug"], "signature": signature, "event_version": event_version, "user_id": str(user_id)},
    )
    return {"attestation": row, **_overview(client, business)}


def create_test_order(client: DbClient, business_id: UUID, user_id: UUID, payload: KioskTestOrderCreate) -> dict:
    assert_workspace_access(client, business_id, user_id)
    business = _locked_business(client, business_id)
    _lock_configuration_tables(client)
    signature, configuration = canonical_configuration(client, business)
    product_ids = [str(item.product_id) for item in payload.items]
    products = client.table("products").select("*").eq("business_id", str(business_id)).in_("id", product_ids).execute().data
    by_id = {row["id"]: row for row in products}
    lines: list[dict[str, Any]] = []
    subtotal = Decimal("0")
    for requested in payload.items:
        product = by_id.get(str(requested.product_id))
        if not product or not _active_product(product) or not availability_service.resolve_product(product, business, configuration.get("availability_rules", []))["available"]:
            raise HTTPException(status_code=409, detail="The draft changed. One or more test items are no longer orderable.")
        unit_price = _effective_price(product)
        option_total, options = _validated_options(client, business_id, product, requested.customizations)
        line_total = (unit_price + option_total) * requested.quantity
        subtotal += line_total
        lines.append({"product_id": product["id"], "name": product["name"], "quantity": requested.quantity, "unit_price": float(unit_price), "customizations": options, "line_total": float(line_total)})
    tax = (subtotal * Decimal(str(business.get("tax_percent") or 0)) / Decimal("100")).quantize(Decimal("0.01"))
    total = subtotal + tax
    test_order = client.fetch_one(
        """insert into kiosk_test_orders
        (business_id, kiosk_id, config_signature, operational_mode, is_test, confirmation_reached, status, payment_method, test_payment_result, order_type, items, subtotal, tax_amount, total_amount, created_by, completed_at)
        values (%(business_id)s, %(kiosk_id)s, %(signature)s, 'test', true, true, 'succeeded', 'test_payment', 'succeeded', %(order_type)s,
        %(items)s, %(subtotal)s, %(tax)s, %(total)s, %(user_id)s, now()) returning *""",
        {"business_id": str(business_id), "kiosk_id": business["slug"], "signature": signature, "order_type": payload.order_type.value, "items": Jsonb(lines), "subtotal": subtotal, "tax": tax, "total": total, "user_id": str(user_id)},
    )
    attestation = client.fetch_one(
        """insert into kiosk_setup_attestations
        (business_id, kiosk_id, kind, operational_mode, config_signature, event_version, test_order_id, confirmation_reached, successful_result, created_by)
        values (%(business_id)s, %(kiosk_id)s, 'test', 'test', %(signature)s, %(event_version)s, %(test_order_id)s, true, true, %(user_id)s) returning *""",
        {"business_id": str(business_id), "kiosk_id": business["slug"], "signature": signature, "event_version": payload.event_version, "test_order_id": test_order["id"], "user_id": str(user_id)},
    )
    result = {"test_order": test_order, "attestation": attestation}
    if ((business.get("kiosk_order_settings") or {}).get("setup") or {}).get("version") == SETUP_VERSION:
        result.update(_overview(client, business))
    return result


def complete_test_experience(client: DbClient, business_id: UUID, user_id: UUID, payload: KioskExperienceTestOrderCreate) -> dict:
    assert_workspace_access(client, business_id, user_id)
    business = _locked_business(client, business_id)
    _lock_configuration_tables(client)
    signature, _ = canonical_configuration(client, business)
    lines = [{"preset_id": item.preset_id, "name": item.name, "quantity": item.quantity} for item in payload.items]
    test_order = client.fetch_one(
        """insert into kiosk_test_orders
        (business_id, kiosk_id, config_signature, operational_mode, is_test, confirmation_reached, status, payment_method, test_payment_result, order_type, items, subtotal, tax_amount, total_amount, created_by, completed_at)
        values (%(business_id)s, %(kiosk_id)s, %(signature)s, 'test', true, true, 'succeeded', 'test_payment', 'succeeded', %(order_type)s,
        %(items)s, 0, 0, 0, %(user_id)s, now()) returning *""",
        {"business_id": str(business_id), "kiosk_id": business["slug"], "signature": signature, "order_type": payload.order_type.value, "items": Jsonb(lines), "user_id": str(user_id)},
    )
    attestation = client.fetch_one(
        """insert into kiosk_setup_attestations
        (business_id, kiosk_id, kind, operational_mode, config_signature, event_version, test_order_id, confirmation_reached, successful_result, created_by)
        values (%(business_id)s, %(kiosk_id)s, 'test', 'test', %(signature)s, %(event_version)s, %(test_order_id)s, true, true, %(user_id)s) returning *""",
        {"business_id": str(business_id), "kiosk_id": business["slug"], "signature": signature, "event_version": payload.event_version, "test_order_id": test_order["id"], "user_id": str(user_id)},
    )
    saved_business = business
    if not business.get("onboarding_completed") and int(business.get("onboarding_step") or 0) >= 5:
        saved_business = _save_setup(
            client,
            business,
            _setup_state(business),
            onboarding_completed=True,
        )
        cache_service.invalidate_slug(saved_business.get("slug") or business.get("slug"))
    return {"test_order": test_order, "attestation": attestation, **_overview(client, saved_business)}


def publish(client: DbClient, business_id: UUID, user_id: UUID, expected_revision: int, allow_untested: bool = False) -> dict:
    assert_workspace_access(client, business_id, user_id)
    business = _locked_business(client, business_id)
    setup = _setup_state(business)
    _assert_revision(setup, expected_revision)
    _lock_configuration_tables(client)
    overview = _overview(client, business)
    core_complete = all(overview["status"][key] for key in ("businessComplete", "menuComplete", "kioskSettingsComplete", "welcomeScreenComplete"))
    onboarding = setup.get("eligible") is not False and not setup.get("completedAt") and not setup.get("publishedSignature")
    tested = overview["status"]["publishable"] if onboarding else overview["status"]["successfulTestComplete"]
    if not core_complete or (not allow_untested and not tested):
        raise HTTPException(status_code=409, detail={"message": "Publishing requirements changed.", "requirements": overview["requirements"]})
    signature, snapshot = canonical_configuration(client, business)
    if signature != overview["signature"]:
        raise HTTPException(status_code=409, detail="The kiosk draft changed during publishing. Review it again.")
    now = datetime.now(timezone.utc).isoformat()
    next_version = client.fetch_one("select coalesce(max(version_number), 0) + 1 as version_number from kiosk_published_versions where business_id = %(business_id)s", {"business_id": str(business_id)})
    version_number = int((next_version or {}).get("version_number") or 1)
    client.fetch_one("""insert into kiosk_published_versions (business_id, version_number, config_signature, snapshot, published_by, source_draft_id)
        values (%(business_id)s, %(version_number)s, %(signature)s, %(snapshot)s, %(user_id)s, %(source_draft_id)s)
        returning id""",
        {"business_id": str(business_id), "version_number": version_number, "signature": signature, "snapshot": Jsonb(snapshot), "user_id": str(user_id), "source_draft_id": ((setup.get("draftId") or None))})
    client.fetch_one(
        """insert into kiosk_published_configs (business_id, config_signature, snapshot, published_by, published_at)
        values (%(business_id)s, %(signature)s, %(snapshot)s, %(user_id)s, now())
        on conflict (business_id) do update set config_signature = excluded.config_signature,
        snapshot = excluded.snapshot, published_by = excluded.published_by, published_at = excluded.published_at
        returning business_id""",
        {"business_id": str(business_id), "signature": signature, "snapshot": Jsonb(snapshot), "user_id": str(user_id)},
    )
    setup.update({"active": False, "completedAt": now, "publishedSignature": signature, "currentStep": "review-publish", "revision": expected_revision + 1, "draftId": None, "restoredSnapshot": None})
    saved = _save_setup(client, business, setup, is_active=True, onboarding_completed=True)
    cache_service.invalidate_slug(saved.get("slug"))
    return _overview(client, saved)


def live_configuration(client: DbClient, business: dict) -> dict:
    published = client.fetch_one("select snapshot from kiosk_published_configs where business_id = %(id)s", {"id": business["id"]})
    if published and isinstance(published.get("snapshot"), dict):
        return published["snapshot"]
    return canonical_configuration(client, business)[1]


def _ensure_legacy_live_baseline(client: DbClient, business: dict, user_id: UUID) -> None:
    state = (business.get("kiosk_order_settings") or {}).get("setup") or {}
    if state.get("version") == SETUP_VERSION and not state.get("completedAt") and not state.get("publishedSignature"):
        return
    if client.fetch_one("select business_id from kiosk_published_configs where business_id = %(id)s", {"id": business["id"]}):
        return
    signature, snapshot = canonical_configuration(client, business)
    client.fetch_one(
        """insert into kiosk_published_configs (business_id, config_signature, snapshot, published_by, published_at)
        values (%(business_id)s, %(signature)s, %(snapshot)s, %(user_id)s, now()) returning business_id""",
        {"business_id": business["id"], "signature": signature, "snapshot": Jsonb(snapshot), "user_id": str(user_id)},
    )
    cache_service.invalidate_slug(business.get("slug"))


def canonical_configuration(client: DbClient, business: dict) -> tuple[str, dict]:
    restored = ((business.get("kiosk_order_settings") or {}).get("setup") or {}).get("restoredSnapshot")
    if isinstance(restored, dict) and restored:
        stable = _stable(restored)
        encoded = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest(), stable
    business_id = str(business["id"])
    order_settings = dict(business.get("kiosk_order_settings") or {})
    order_settings.pop("setup", None)
    snapshot = {
        "business": {**{key: business.get(key) for key in BUSINESS_CONFIG_KEYS}, "kiosk_order_settings": order_settings},
        "categories": _rows(client, "categories", business_id),
        "products": _rows(client, "products", business_id),
        "modifier_groups": _rows(client, "product_modifier_groups", business_id),
        "modifier_options": _related_rows(client, "product_modifier_options", "group_id", "product_modifier_groups", business_id),
        "combos": _rows(client, "menu_combos", business_id),
        "combo_sections": _related_rows(client, "combo_sections", "combo_id", "menu_combos", business_id),
        "combo_options": _related_rows(client, "combo_options", "combo_id", "menu_combos", business_id),
        "availability_rules": client.fetch_all("select * from availability_rules where business_id = %(id)s order by created_at, id", {"id": business_id}),
    }
    stable = _stable(snapshot)
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), stable


def _overview(client: DbClient, business: dict) -> dict:
    setup = _setup_state(business)
    signature, snapshot = canonical_configuration(client, business)
    preview = _latest_attestation(client, business["id"], "preview")
    test = _latest_attestation(client, business["id"], "test")
    published = client.fetch_one("select config_signature, snapshot, published_at from kiosk_published_configs where business_id = %(id)s", {"id": business["id"]})
    categories = client.table("categories").select("*").eq("business_id", business["id"]).execute().data
    products = client.table("products").select("*").eq("business_id", business["id"]).execute().data
    active_categories = {row["id"] for row in categories if row.get("is_active")}
    status = {
        "businessComplete": bool(str(business.get("name") or "").strip() and business.get("type")),
        "menuComplete": any(_active_product(row) and row.get("category_id") in active_categories for row in products),
        "kioskSettingsComplete": bool((business.get("kiosk_order_settings") or {}).get("display_configured") is True and business.get("kiosk_theme") and business.get("kiosk_layout") and business.get("kiosk_screen_orientation") and business.get("kiosk_screen_size")),
        "welcomeScreenComplete": (business.get("kiosk_start_screen_settings") or {}).get("configured") is True,
        "previewComplete": bool(preview and preview["config_signature"] == signature),
        "successfulTestComplete": bool(test and test["config_signature"] == signature),
        "published": bool((published and published["config_signature"] == signature) or (not published and business.get("is_active"))),
        "previewStale": bool(preview and preview["config_signature"] != signature),
        "testStale": bool(test and test["config_signature"] != signature),
    }
    status["publishable"] = all(status[key] for key in ("businessComplete", "menuComplete", "kioskSettingsComplete", "welcomeScreenComplete", "previewComplete", "successfulTestComplete"))
    requirements = [
        {"key": "business", "label": "Complete business details", "complete": status["businessComplete"], "href": "/admin/settings"},
        {"key": "menu", "label": "Add one active menu item in a category", "complete": status["menuComplete"], "href": "/admin/menu/items/new"},
        {"key": "kiosk", "label": "Save required kiosk settings and dimensions", "complete": status["kioskSettingsComplete"], "href": "/admin/kiosk"},
        {"key": "welcome", "label": "Save the welcome-screen choice", "complete": status["welcomeScreenComplete"], "href": "/admin/welcome-screen"},
        {"key": "preview", "label": "Preview the current configuration", "complete": status["previewComplete"], "href": "/admin/preview"},
        {"key": "test", "label": "Complete a successful test order", "complete": status["successfulTestComplete"], "href": "/admin/preview#test"},
    ]
    change_summary = _configuration_changes(snapshot=snapshot, published_snapshot=published.get("snapshot") if published else None, legacy_live=not published and setup.get("eligible") is False)
    return {
        "setup": setup,
        "status": status,
        "requirements": requirements,
        "signature": signature,
        "lastPreviewedAt": preview.get("created_at") if preview else None,
        "lastSuccessfulTestAt": test.get("created_at") if test else None,
        "lastPublishedAt": published.get("published_at") if published else None,
        "lastSavedAt": business.get("updated_at"),
        "unpublishedChanges": sum(item["count"] for item in change_summary),
        "changeSummary": change_summary,
    }


def _setup_state(business: dict) -> dict:
    setup = dict((business.get("kiosk_order_settings") or {}).get("setup") or {})
    if setup.get("version") != SETUP_VERSION:
        return {
            "version": SETUP_VERSION,
            "currentStep": "menu",
            "startedAt": str(business.get("created_at") or datetime.now(timezone.utc).isoformat()),
            "completedAt": str(business.get("updated_at") or business.get("created_at") or datetime.now(timezone.utc).isoformat()),
            "revision": 0,
            "active": False,
            "eligible": False,
        }
    setup.setdefault("revision", 0)
    setup.setdefault("active", True)
    setup.setdefault("eligible", True)
    return setup


def _locked_business(client: DbClient, business_id: UUID) -> dict:
    business = client.fetch_one("select * from businesses where id = %(id)s for update", {"id": str(business_id)})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found.")
    return business


def _assert_revision(setup: dict, expected: int) -> None:
    if int(setup.get("revision") or 0) != expected:
        raise HTTPException(status_code=409, detail={"message": "Setup was updated in another session.", "setup": setup})


def _save_setup(
    client: DbClient,
    business: dict,
    setup: dict,
    is_active: bool | None = None,
    onboarding_completed: bool | None = None,
) -> dict:
    settings = {**(business.get("kiosk_order_settings") or {}), "setup": setup}
    sql = "update businesses set kiosk_order_settings = %(settings)s"
    if is_active is not None:
        sql += ", is_active = %(is_active)s"
    if onboarding_completed is not None:
        sql += ", onboarding_completed = %(onboarding_completed)s, onboarding_step = 6"
    sql += " where id = %(id)s returning *"
    return client.fetch_one(
        sql,
        {
            "settings": Jsonb(settings),
            "is_active": is_active,
            "onboarding_completed": onboarding_completed,
            "id": business["id"],
        },
    )


def _latest_attestation(client: DbClient, business_id: str, kind: str) -> dict | None:
    return client.fetch_one("select * from kiosk_setup_attestations where business_id = %(id)s and kind = %(kind)s order by created_at desc, id desc limit 1", {"id": business_id, "kind": kind})


def _lock_configuration_tables(client: DbClient) -> None:
    client.execute_command("lock table categories, products, product_modifier_groups, product_modifier_options, menu_combos, combo_sections, combo_options, availability_rules in share mode")


def _rows(client: DbClient, table: str, business_id: str) -> list[dict]:
    return client.fetch_all(f"select * from {table} where business_id = %(id)s order by sort_order, id", {"id": business_id})


def _related_rows(client: DbClient, table: str, foreign_key: str, owner_table: str, business_id: str) -> list[dict]:
    return client.fetch_all(f"select child.* from {table} child join {owner_table} owner on owner.id = child.{foreign_key} where owner.business_id = %(id)s order by child.sort_order, child.id", {"id": business_id})


def _active_product(product: dict) -> bool:
    return bool(str(product.get("name") or "").strip() and Decimal(str(product.get("price") or 0)) > 0 and product.get("is_available") and product.get("menu_status") == "shown")


def _effective_price(product: dict) -> Decimal:
    price = Decimal(str(product.get("price") or 0))
    value = Decimal(str(product.get("discount_value") or 0))
    if product.get("discount_type") == "percentage":
        return max(Decimal("0"), price * (Decimal("1") - value / Decimal("100")))
    if product.get("discount_type") == "fixed":
        return max(Decimal("0"), price - value)
    return price


def _validated_options(client: DbClient, business_id: UUID, product: dict, requested: list[dict]) -> tuple[Decimal, list[dict]]:
    if not requested:
        return Decimal("0"), []
    option_ids = [str(row.get("option_id") or "") for row in requested]
    rows = client.fetch_all("""select o.*, g.product_id, g.name as group_name
        from product_modifier_options o join product_modifier_groups g on g.id = o.group_id
        where g.business_id = %(business_id)s and g.product_id = %(product_id)s and o.id::text = any(%(option_ids)s)""",
        {"business_id": str(business_id), "product_id": product["id"], "option_ids": option_ids})
    if len(rows) != len(set(option_ids)) or any(not row.get("is_available") for row in rows):
        raise HTTPException(status_code=409, detail="The draft changed. One or more test options are unavailable.")
    total = sum((Decimal(str(row.get("price_delta") or 0)) for row in rows), Decimal("0"))
    return total, [{"group_id": row["group_id"], "group_name": row["group_name"], "option_id": row["id"], "name": row["name"], "price_delta": float(row["price_delta"])} for row in rows]


def _stable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable(child) for key, child in sorted(value.items()) if key not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [_stable(child) for child in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _configuration_changes(snapshot: dict, published_snapshot: dict | None, legacy_live: bool = False) -> list[dict]:
    if legacy_live:
        return []
    if not published_snapshot:
        return [{"key": "initial", "label": "Initial kiosk configuration", "count": 1}]
    labels = {
        "business": "Business and kiosk settings",
        "categories": "Categories",
        "products": "Menu items",
        "modifier_groups": "Add-on groups",
        "modifier_options": "Add-ons",
        "combos": "Combos",
        "combo_sections": "Combo sections",
        "combo_options": "Combo options",
        "availability_rules": "Availability rules",
    }
    changes = []
    for key, label in labels.items():
        current = snapshot.get(key)
        live = published_snapshot.get(key)
        if key == "business":
            count = int(current != live)
        else:
            current_rows = {str(row.get("id")): row for row in (current or [])}
            live_rows = {str(row.get("id")): row for row in (live or [])}
            count = sum(current_rows.get(row_id) != live_rows.get(row_id) for row_id in current_rows.keys() | live_rows.keys())
        if count:
            changes.append({"key": key, "label": label, "count": count})
    return changes
