from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from psycopg.errors import UndefinedColumn, UniqueViolation

from database import DbClient
from schemas import BusinessCreate, BusinessUpdate, StaffRole
from services import cache_service
from utils import clean_payload, slugify


FULL_ACCESS_ROLES = {StaffRole.OWNER, StaffRole.ADMIN}
ADMIN_ROLES = {StaffRole.OWNER, StaffRole.ADMIN, StaffRole.MANAGER}
PAYMENT_CONFIG_ROLES = FULL_ACCESS_ROLES
DEVICE_ADMIN_ROLES = FULL_ACCESS_ROLES
PIN_ADMIN_ROLES = FULL_ACCESS_ROLES
ORDER_VIEW_ROLES = {StaffRole.MANAGER, StaffRole.KITCHEN, StaffRole.CASHIER, StaffRole.SALON_STAFF, StaffRole.KIOSK, StaffRole.VIEWER}
ORDER_ROLES = ORDER_VIEW_ROLES
KITCHEN_ROLES = {StaffRole.KITCHEN, StaffRole.SALON_STAFF}
COUNTER_ROLES = {StaffRole.CASHIER, StaffRole.SALON_STAFF}
PAYMENT_VIEW_ROLES = {StaffRole.MANAGER, StaffRole.CASHIER, StaffRole.SALON_STAFF}
CATALOG_READ_ROLES = {StaffRole.MANAGER, StaffRole.KITCHEN, StaffRole.CASHIER, StaffRole.SALON_STAFF, StaffRole.KIOSK, StaffRole.VIEWER}
LEGACY_LAYOUTS = {
    "left_category": "side-navigation",
    "top_category": "top-navigation",
    "category_gate": "category-first",
}
CANONICAL_LAYOUTS = {value: key for key, value in LEGACY_LAYOUTS.items()}


def _slug_candidates(base_slug: str, start: int = 2, count: int = 10) -> list[str]:
    base = slugify(base_slug or "store") or "store"
    if start <= 2:
        return [base, f"{base}-store", *[f"{base}-{index}" for index in range(2, 12)]]
    return [f"{base}-{index}" for index in range(start, start + count)]


def _taken_slugs(client: DbClient, candidates: list[str], current_business_id: UUID | str | None = None) -> set[str]:
    response = client.table("businesses").select("id,slug").in_("slug", candidates).execute()
    current = str(current_business_id) if current_business_id else None
    return {
        row["slug"]
        for row in response.data or []
        if not current or str(row["id"]) != current
    }


def _next_available_slug(client: DbClient, requested_slug: str, current_business_id: UUID | str | None = None) -> str:
    base = slugify(requested_slug or "store") or "store"
    start = 2
    for _ in range(50):
        candidates = _slug_candidates(base, start=start)
        taken = _taken_slugs(client, candidates, current_business_id)
        for candidate in candidates:
            if candidate not in taken:
                return candidate
        start += 10
    raise HTTPException(status_code=409, detail="Could not allocate an available kiosk path.")


def ensure_profile(client: DbClient, user_id: UUID, email: str | None = None) -> None:
    payload = {"id": str(user_id)}
    if email:
        payload["email"] = email
    client.table("profiles").upsert(payload).execute()


def get_business_by_id(client: DbClient, business_id: UUID) -> dict:
    response = client.table("businesses").select("*").eq("id", str(business_id)).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Business not found.")
    return response.data[0]


def get_business_by_slug(client: DbClient, slug: str) -> dict:
    response = (
        client.table("businesses")
        .select("*")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Kiosk business not found.")
    return response.data[0]


def serialize_business_for_response(business: dict | None) -> dict | None:
    if not business:
        return business
    safe = dict(business)
    pin_configured = bool(safe.get("owner_pin_hash"))
    for key in ["owner_pin_hash", "pin_failed_attempts", "pin_locked_until"]:
        safe.pop(key, None)
    lock_settings = safe.get("kiosk_lock_settings") or {}
    if isinstance(lock_settings, dict):
        safe["kiosk_lock_settings"] = {**lock_settings, "owner_pin_configured": pin_configured}
    return safe


def assert_business_access(
    client: DbClient,
    business_id: UUID,
    user_id: UUID,
    allowed_roles: set[StaffRole] | None = None,
) -> dict:
    business = get_business_by_id(client, business_id)
    if str(business["owner_id"]) == str(user_id):
        return business

    staff_response = (
        client.table("business_staff")
        .select("role")
        .eq("business_id", str(business_id))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )
    if not staff_response.data:
        raise HTTPException(status_code=403, detail="You do not have access to this business.")
    role = StaffRole(staff_response.data[0]["role"])
    if role in FULL_ACCESS_ROLES:
        return business
    if allowed_roles is None and role in ADMIN_ROLES:
        return business
    if allowed_roles and role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Your staff role cannot perform this action.")
    if allowed_roles is None:
        raise HTTPException(status_code=403, detail="Your staff role cannot perform this action.")
    return business


def get_business_role_for_user(client: DbClient, business: dict, user_id: UUID) -> StaffRole:
    if str(business.get("owner_id")) == str(user_id):
        return StaffRole.OWNER
    staff = (
        client.table("business_staff")
        .select("role")
        .eq("business_id", str(business["id"]))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )
    if not staff.data:
        raise HTTPException(status_code=403, detail="You do not have access to this business.")
    return StaffRole(staff.data[0]["role"])


def get_primary_business_for_user(client: DbClient, user_id: UUID) -> dict | None:
    owned = (
        client.table("businesses")
        .select("*")
        .eq("owner_id", str(user_id))
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    if owned.data:
        return owned.data[0]

    staff = (
        client.table("business_staff")
        .select("business_id")
        .eq("user_id", str(user_id))
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    if not staff.data:
        return None
    return get_business_by_id(client, UUID(staff.data[0]["business_id"]))


def onboarding_status(client: DbClient, user_id: UUID) -> dict:
    business = get_primary_business_for_user(client, user_id)
    if not business:
        business_type = get_onboarding_business_type(client, user_id)["business_type"]
        return {
            "has_business": False,
            "business_id": None,
            "onboarding_step": 1 if business_type else 0,
            "onboarding_completed": False,
            "next_route": "/setup/business-details" if business_type else "/setup/business-type",
        }

    completed = bool(business.get("onboarding_completed"))
    if not completed and _has_durable_completion_evidence(business):
        saved = client.fetch_one(
            """update businesses
            set onboarding_completed = true, onboarding_step = 6
            where id = %(id)s and onboarding_completed = false
            returning onboarding_completed, onboarding_step""",
            {"id": business["id"]},
        )
        completed = bool(saved and saved.get("onboarding_completed"))
        if completed:
            business = {**business, **saved}
    return {
        "has_business": True,
        "business_id": business["id"],
        "onboarding_step": business.get("onboarding_step") or 0,
        "onboarding_completed": completed,
        "next_route": "/dashboard" if completed else _setup_route(int(business.get("onboarding_step") or 0)),
    }


def _has_durable_completion_evidence(business: dict) -> bool:
    setup = ((business.get("kiosk_order_settings") or {}).get("setup") or {})
    if setup.get("version") == 2:
        return bool(setup.get("completedAt") or setup.get("publishedSignature"))
    return bool(business.get("is_active") and business.get("name") and business.get("type"))


def get_onboarding_business_type(client: DbClient, user_id: UUID) -> dict:
    ensure_profile(client, user_id)
    row = client.fetch_one(
        "select onboarding_business_type, onboarding_business_description from profiles where id = %(id)s",
        {"id": str(user_id)},
    )
    return {
        "business_type": row.get("onboarding_business_type") if row else None,
        "business_description": row.get("onboarding_business_description") if row else None,
    }


def set_onboarding_business_type(client: DbClient, user_id: UUID, business_type: str, business_description: str | None) -> dict:
    ensure_profile(client, user_id)
    description = business_description.strip() if business_type == "other" and business_description else None
    client.fetch_one(
        """
        update profiles
        set onboarding_business_type = %(business_type)s,
            onboarding_business_description = %(business_description)s
        where id = %(id)s
        returning id
        """,
        {"id": str(user_id), "business_type": business_type, "business_description": description},
    )
    return {"business_type": business_type, "business_description": description}


def _setup_route(step: int) -> str:
    routes = {
        0: "/setup/business-type",
        1: "/setup/business-details",
        2: "/setup/menu-items",
        3: "/setup/kiosk-layout",
        4: "/setup/welcome-screen",
        5: "/setup/test-kiosk",
    }
    return routes.get(step, "/setup/test-kiosk" if step > 5 else "/setup/business-type")


def slug_options(client: DbClient, user_id: UUID, name: str | None = None, slug: str | None = None) -> dict:
    base_slug = slugify(slug or name or "business")
    owned_business = get_primary_business_for_user(client, user_id)
    current_business_id = str(owned_business["id"]) if owned_business else None

    candidates = _slug_candidates(base_slug)
    taken = _taken_slugs(client, candidates, current_business_id)

    available = len(base_slug) >= 2 and base_slug not in taken
    suggestions = [candidate for candidate in candidates[1:] if len(candidate) >= 2 and candidate not in taken][:4]
    if not available and not suggestions:
        suggestions = [_next_available_slug(client, base_slug, current_business_id)]

    return {
        "slug": base_slug,
        "available": available,
        "suggestions": suggestions,
    }


def create_business(client: DbClient, user_id: UUID, payload: BusinessCreate) -> dict:
    ensure_profile(client, user_id)
    data = payload.model_dump(mode="json")
    _normalize_kiosk_configuration(data, {}, payload.model_fields_set)
    order_settings = data.get("kiosk_order_settings") or {}
    order_settings.setdefault(
        "setup",
        {
            "version": 2,
            "currentStep": "business-details",
            "startedAt": datetime.now(timezone.utc).isoformat(),
            "revision": 0,
            "active": True,
            "eligible": True,
        },
    )
    data["kiosk_order_settings"] = order_settings
    data["owner_id"] = str(user_id)
    data["slug"] = _next_available_slug(client, data.get("slug") or data["name"])

    try:
        response = client.table("businesses").insert(data).execute()
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="This kiosk URL slug is already in use. Try a different slug.") from exc
    except UndefinedColumn as exc:
        raise HTTPException(
            status_code=500,
            detail="The local database schema is out of date. Restart FastAPI so the schema compatibility check can run.",
        ) from exc

    if not response.data:
        raise HTTPException(status_code=400, detail="Business could not be created.")
    business = response.data[0]
    client.table("business_staff").upsert(
        {
            "business_id": business["id"],
            "user_id": str(user_id),
            "role": StaffRole.OWNER.value,
        }
    ).execute()
    cache_service.invalidate_slug(business.get("slug"))
    return business


def update_business(
    client: DbClient,
    business_id: UUID,
    user_id: UUID,
    payload: BusinessUpdate,
) -> dict:
    old_business = assert_business_access(client, business_id, user_id, FULL_ACCESS_ROLES)
    if hasattr(client, "execute_one"):
        old_business = client.execute_one("select * from businesses where id = %(id)s for update", {"id": str(business_id)})
    if not old_business:
        raise HTTPException(status_code=404, detail="Business not found.")
    data = clean_payload(payload.model_dump(mode="json"))
    _normalize_kiosk_configuration(data, old_business, payload.model_fields_set)
    owner_pin = data.pop("owner_pin", None)
    if "slug" in data:
        data["slug"] = slugify(data["slug"])
        if data["slug"] != old_business.get("slug"):
            data["slug"] = _next_available_slug(client, data["slug"], business_id)
    if "kiosk_lock_settings" in data:
        _validate_kiosk_lock_settings_change(old_business, data["kiosk_lock_settings"], owner_pin)
    if "kiosk_order_settings" in data:
        current_settings = old_business.get("kiosk_order_settings") or {}
        next_settings = {**current_settings, **(data["kiosk_order_settings"] or {})}
        if (current_settings.get("setup") or {}).get("version") == 2:
            next_settings["setup"] = current_settings["setup"]
        data["kiosk_order_settings"] = next_settings
    if not data:
        return get_business_by_id(client, business_id)

    try:
        response = (
            client.table("businesses")
            .update(data)
            .eq("id", str(business_id))
            .execute()
        )
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="This kiosk URL slug is already in use. Try a different slug.") from exc
    except UndefinedColumn as exc:
        raise HTTPException(
            status_code=500,
            detail="The local database schema is out of date. Restart FastAPI so the schema compatibility check can run.",
        ) from exc
    if not response.data:
        raise HTTPException(status_code=404, detail="Business not found.")
    business = response.data[0]
    client.table("audit_logs").insert({
        "business_id": str(business_id),
        "user_id": str(user_id),
        "action": "business_settings_updated",
        "entity": "business",
        "entity_id": str(business_id),
        "metadata": {"fields": sorted(data)},
    }).execute()
    cache_service.invalidate_slug(old_business.get("slug"))
    cache_service.invalidate_slug(business.get("slug"))
    return business


def _normalize_kiosk_configuration(data: dict, current: dict, fields_set: set[str]) -> None:
    if "kiosk_layout_id" not in fields_set and "kiosk_theme" in fields_set:
        data["kiosk_layout_id"] = LEGACY_LAYOUTS.get(str(data["kiosk_theme"]).split(":", 1)[0], "top-navigation")
    if "kiosk_layout_id" in data:
        legacy_layout = CANONICAL_LAYOUTS[data["kiosk_layout_id"]]
        theme_parts = str(data.get("kiosk_theme") or current.get("kiosk_theme") or "top_category:premium_light").split(":")
        data["kiosk_theme"] = ":".join([legacy_layout, *theme_parts[1:]])
        data["kiosk_order_settings"] = {
            **(data.get("kiosk_order_settings") or {}),
            "display_configured": True,
        }

    if "welcome_screen" not in fields_set and fields_set.intersection(
        {"kiosk_start_screen_enabled", "kiosk_start_text_position", "kiosk_touch_to_start", "kiosk_start_screen_settings"}
    ):
        settings = {**(current.get("kiosk_start_screen_settings") or {}), **(data.get("kiosk_start_screen_settings") or {})}
        data["welcome_screen"] = {
            **(current.get("welcome_screen") or {}),
            "enabled": data.get("kiosk_start_screen_enabled", current.get("kiosk_start_screen_enabled", True)),
            "heading": settings.get("heading", "Welcome"),
            "supporting_text": settings.get("supporting_text", ""),
            "instruction_text": settings.get("instruction_text", "Tap to begin"),
            "start_button_text": settings.get("start_button_text", "Start"),
            "text_position": data.get("kiosk_start_text_position", current.get("kiosk_start_text_position", "middle")),
            "touch_anywhere_to_start": data.get("kiosk_touch_to_start", current.get("kiosk_touch_to_start", False)),
            "show_business_logo": settings.get("show_business_logo", True),
        }
    if "welcome_screen" in data:
        welcome = data["welcome_screen"]
        data["kiosk_start_screen_enabled"] = welcome["enabled"]
        data["kiosk_start_text_position"] = welcome["text_position"]
        data["kiosk_touch_to_start"] = welcome["touch_anywhere_to_start"]
        data["kiosk_start_screen_settings"] = {
            **(current.get("kiosk_start_screen_settings") or {}),
            "heading": welcome["heading"],
            "supporting_text": welcome["supporting_text"],
            "instruction_text": welcome["instruction_text"],
            "start_button_text": welcome["start_button_text"],
            "show_business_logo": welcome["show_business_logo"],
            "configured": True,
        }


def _validate_kiosk_lock_settings_change(old_business: dict, next_settings: dict | None, owner_pin: str | None) -> None:
    if next_settings is None:
        return
    current = old_business.get("kiosk_lock_settings") or {}
    next_lock = next_settings or {}
    pin_hash = old_business.get("owner_pin_hash")

    enabling_lock = bool(next_lock.get("enabled")) and not bool(current.get("enabled"))
    if enabling_lock and not pin_hash:
        raise HTTPException(status_code=409, detail="Create a kiosk PIN before enabling kiosk lock.")

    disabling_lock = bool(current.get("enabled")) and not bool(next_lock.get("enabled"))
    weakening_exit_pin = (
        bool(current.get("enabled"))
        and current.get("require_pin_to_exit", True) is not False
        and next_lock.get("require_pin_to_exit") is False
    )
    if not (disabling_lock or weakening_exit_pin):
        return
    if not pin_hash:
        raise HTTPException(status_code=409, detail="Owner PIN is not configured.")
    if not owner_pin:
        raise HTTPException(status_code=400, detail="Owner PIN is required to disable or weaken kiosk lock.")
    from services import pin_service

    if not pin_service.verify_pin(owner_pin, pin_hash):
        raise HTTPException(status_code=403, detail="Invalid owner PIN.")
