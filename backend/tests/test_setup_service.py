from copy import deepcopy
from pathlib import Path

import pytest
from fastapi import HTTPException

from schemas import KioskExperienceTestOrderCreate, KioskSetupUpdate
from services import setup_service


class CanonicalClient:
    def __init__(self, rows):
        self.rows = rows

    def fetch_all(self, sql, _params):
        for key, rows in self.rows.items():
            if f"from {key} " in " ".join(sql.split()):
                return deepcopy(rows)
        return []


def business():
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "Demo", "slug": "demo", "type": "restaurant", "is_active": True,
        "kiosk_theme": "left_category:premium_light", "kiosk_layout": "wide_16_9",
        "kiosk_screen_orientation": "portrait", "kiosk_screen_size": "43", "kiosk_cart_mode": "page",
        "kiosk_start_screen_enabled": True, "kiosk_start_screen_settings": {"configured": True},
        "kiosk_order_settings": {"display_configured": True, "setup": {"version": 2, "revision": 3}},
        "tax_percent": 5,
    }


def rows():
    return {
        "categories": [{"id": "c1", "business_id": "b1", "name": "Food", "image_path": "/c.jpg", "is_active": True, "sort_order": 0, "updated_at": "yesterday"}],
        "products": [{"id": "p1", "business_id": "b1", "category_id": "c1", "name": "Soup", "description": "Hot", "price": 10, "discount_type": "none", "discount_value": 0, "primary_image_path": "/p.jpg", "is_available": True, "menu_status": "shown", "sort_order": 0, "metadata": {"portion": "large"}, "updated_at": "yesterday"}],
        "product_modifier_groups": [{"id": "g1", "business_id": "b1", "product_id": "p1", "name": "Size", "min_select": 1, "max_select": 1, "sort_order": 0}],
        "product_modifier_options": [{"id": "o1", "group_id": "g1", "name": "Large", "price_delta": 2, "is_available": True, "sort_order": 0}],
        "menu_combos": [{"id": "m1", "business_id": "b1", "name": "Meal", "price": 20, "status": "shown", "sort_order": 0}],
        "combo_sections": [{"id": "s1", "combo_id": "m1", "title": "Main", "min_select": 1, "max_select": 1, "sort_order": 0}],
        "combo_options": [{"id": "co1", "combo_id": "m1", "section_id": "s1", "existing_item_id": "p1", "quantity": 1, "price_impact": 0, "sort_order": 0}],
    }


def test_canonical_hash_is_stable_and_excludes_setup_and_timestamps():
    data = rows()
    first, snapshot = setup_service.canonical_configuration(CanonicalClient(data), business())
    data["products"][0]["updated_at"] = "today"
    changed_setup = business()
    changed_setup["kiosk_order_settings"]["setup"]["revision"] = 99
    second, second_snapshot = setup_service.canonical_configuration(CanonicalClient(data), changed_setup)
    assert first == second
    assert snapshot == second_snapshot
    assert "setup" not in snapshot["business"]["kiosk_order_settings"]


@pytest.mark.parametrize("table, field, value", [
    ("categories", "image_path", "/new-category.jpg"),
    ("products", "description", "Cold"),
    ("product_modifier_options", "price_delta", 4),
    ("combo_options", "quantity", 2),
])
def test_canonical_hash_changes_for_kiosk_visible_and_order_affecting_data(table, field, value):
    data = rows()
    original, _ = setup_service.canonical_configuration(CanonicalClient(data), business())
    data[table][0][field] = value
    changed, _ = setup_service.canonical_configuration(CanonicalClient(data), business())
    assert changed != original


def test_revision_conflict_is_a_409_and_preserves_server_state():
    state = {"version": 2, "revision": 4, "currentStep": "menu"}
    with pytest.raises(HTTPException) as exc:
        setup_service._assert_revision(state, 3)
    assert exc.value.status_code == 409
    assert exc.value.detail["setup"] == state


def test_test_order_storage_is_isolated_from_production_tables():
    source = Path(setup_service.__file__).read_text(encoding="utf-8")
    assert "insert into kiosk_test_orders" in source
    assert "insert into kiosk_setup_attestations" in source
    assert "operational_mode, is_test, confirmation_reached" in source
    assert "'test', true, true" in source
    assert "successful_result" in source
    assert "insert into orders" not in source
    assert "insert into payments" not in source


def test_setup_schema_records_explicit_test_and_confirmation_markers():
    schema = (Path(setup_service.__file__).parents[1] / "postgres_schema.sql").read_text(encoding="utf-8")
    assert "is_test boolean not null default true" in schema
    assert "confirmation_reached boolean not null default true" in schema
    assert "operational_mode text not null default 'test'" in schema
    assert "completed_at timestamptz not null default now()" in schema


class RevisionClient:
    def __init__(self):
        self.mutated = False

    def fetch_one(self, sql, _params):
        if "select * from businesses" in sql:
            return business()
        self.mutated = True
        raise AssertionError(f"stale setup must not mutate: {sql}")

    def fetch_all(self, _sql, _params=None):
        return []

    def execute_command(self, _sql, _params=None):
        self.mutated = True
        raise AssertionError("stale setup must not execute a command")


def test_stale_setup_patch_returns_409_before_mutation(monkeypatch):
    client = RevisionClient()
    monkeypatch.setattr(setup_service.business_service, "assert_business_access", lambda *_args, **_kwargs: business())
    with pytest.raises(HTTPException) as exc:
        setup_service.update_setup(client, business()["id"], business()["id"], KioskSetupUpdate(expected_revision=2, active=False))
    assert exc.value.status_code == 409
    assert client.mutated is False


def test_stale_publish_returns_409_without_partial_publish(monkeypatch):
    client = RevisionClient()
    monkeypatch.setattr(setup_service.business_service, "assert_business_access", lambda *_args, **_kwargs: business())
    with pytest.raises(HTTPException) as exc:
        setup_service.publish(client, business()["id"], business()["id"], expected_revision=2)
    assert exc.value.status_code == 409
    assert client.mutated is False


def test_unpublished_change_count_tracks_changed_and_added_entities():
    live = {"business": {"name": "Demo"}, "products": [{"id": "p1", "name": "Soup"}]}
    draft = {"business": {"name": "New Demo"}, "products": [{"id": "p1", "name": "Cold Soup"}, {"id": "p2", "name": "Tea"}]}
    changes = setup_service._configuration_changes(draft, live)
    assert sum(change["count"] for change in changes) == 3


def test_publish_save_marks_onboarding_complete():
    class SaveClient:
        def fetch_one(self, sql, params):
            assert "onboarding_completed = %(onboarding_completed)s, onboarding_step = 6" in sql
            assert params["onboarding_completed"] is True
            return {"id": params["id"], "onboarding_completed": True, "onboarding_step": 6}

    saved = setup_service._save_setup(
        SaveClient(),
        business(),
        {"version": 2, "revision": 4},
        is_active=True,
        onboarding_completed=True,
    )
    assert saved["onboarding_completed"] is True


class ExperienceClient:
    def __init__(self, onboarding_step: int, onboarding_completed: bool = False):
        self.business = {
            **business(),
            "onboarding_step": onboarding_step,
            "onboarding_completed": onboarding_completed,
        }
        self.completion_writes = []

    def fetch_one(self, sql, params):
        if "select * from businesses" in sql:
            return deepcopy(self.business)
        if "insert into kiosk_test_orders" in sql:
            return {"id": "test-order"}
        if "insert into kiosk_setup_attestations" in sql:
            return {"id": "attestation"}
        if "update businesses set kiosk_order_settings" in sql:
            self.completion_writes.append(params)
            self.business.update({"onboarding_completed": True, "onboarding_step": 6})
            return deepcopy(self.business)
        raise AssertionError(sql)

    def execute_command(self, sql, _params=None):
        assert sql.startswith("lock table")


def complete_test_experience(client, monkeypatch):
    monkeypatch.setattr(setup_service, "assert_workspace_access", lambda *_args: client.business)
    monkeypatch.setattr(setup_service, "canonical_configuration", lambda *_args: ("signature", {}))
    monkeypatch.setattr(setup_service, "_overview", lambda _client, saved: {"saved_business": saved})
    payload = KioskExperienceTestOrderCreate(items=[{"preset_id": "test-item", "name": "Test item", "quantity": 1}])
    return setup_service.complete_test_experience(client, client.business["id"], client.business["id"], payload)


def test_successful_onboarding_experience_persists_completion_atomically(monkeypatch):
    client = ExperienceClient(onboarding_step=5)
    result = complete_test_experience(client, monkeypatch)

    assert len(client.completion_writes) == 1
    assert client.completion_writes[0]["onboarding_completed"] is True
    assert result["saved_business"]["onboarding_completed"] is True
    assert result["saved_business"]["onboarding_step"] == 6


def test_test_experience_before_final_step_cannot_complete_onboarding(monkeypatch):
    client = ExperienceClient(onboarding_step=4)
    result = complete_test_experience(client, monkeypatch)

    assert client.completion_writes == []
    assert result["saved_business"]["onboarding_completed"] is False


def test_completed_test_experience_is_idempotent(monkeypatch):
    client = ExperienceClient(onboarding_step=6, onboarding_completed=True)
    result = complete_test_experience(client, monkeypatch)

    assert client.completion_writes == []
    assert result["saved_business"]["onboarding_completed"] is True


def test_legacy_business_gets_a_live_baseline_before_draft_edits(monkeypatch):
    class BaselineClient(CanonicalClient):
        inserted = None

        def fetch_one(self, sql, params):
            if "select business_id" in sql:
                return None
            if "insert into kiosk_published_configs" in sql:
                self.inserted = params
                return {"business_id": params["business_id"]}
            raise AssertionError(sql)

    client = BaselineClient(rows())
    legacy = {**business(), "kiosk_order_settings": {"display_configured": True}}
    monkeypatch.setattr(setup_service.cache_service, "invalidate_slug", lambda _slug: None)
    setup_service._ensure_legacy_live_baseline(client, legacy, legacy["id"])
    assert client.inserted["business_id"] == legacy["id"]
    assert client.inserted["signature"]
