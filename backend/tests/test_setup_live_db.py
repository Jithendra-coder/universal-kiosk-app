from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from database import db_context
from deps import require_user_id
from main import app


pytestmark = pytest.mark.live_db


def _require_live_db() -> None:
    if os.getenv("RUN_LIVE_DB_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_DB_TESTS=1 to run live PostgreSQL setup tests.")


def _seed_setup_business() -> dict[str, str]:
    suffix = uuid4().hex
    user_id = str(uuid4())
    business_id = str(uuid4())
    category_id = str(uuid4())
    product_id = str(uuid4())
    setup = {
        "version": 2,
        "revision": 0,
        "currentStep": "menu",
        "introPending": False,
        "active": True,
    }
    with db_context() as db:
        db.fetch_one(
            "insert into app_users (id, email, password_hash, full_name) values (%(id)s, %(email)s, 'test-only', 'Setup QA') returning id",
            {"id": user_id, "email": f"setup-live-{suffix}@example.test"},
        )
        db.fetch_one(
            """insert into businesses
            (id, owner_id, name, slug, type, kiosk_theme, kiosk_layout,
             kiosk_screen_orientation, kiosk_screen_size, kiosk_start_screen_settings,
             kiosk_order_settings, onboarding_completed)
            values (%(id)s, %(owner_id)s, 'Setup Live QA', %(slug)s, 'restaurant',
                    'left_category:premium_light', 'wide_16_9', 'landscape', '32',
                    %(welcome)s, %(order_settings)s, true)
            returning id""",
            {
                "id": business_id,
                "owner_id": user_id,
                "slug": f"setup-live-{suffix}",
                "welcome": Jsonb({"configured": True}),
                "order_settings": Jsonb({"display_configured": True, "setup": setup}),
            },
        )
        db.fetch_one(
            "insert into business_staff (business_id, user_id, role) values (%(business_id)s, %(user_id)s, 'owner') returning id",
            {"business_id": business_id, "user_id": user_id},
        )
        db.fetch_one(
            "insert into categories (id, business_id, name, is_active) values (%(id)s, %(business_id)s, 'Drinks', true) returning id",
            {"id": category_id, "business_id": business_id},
        )
        db.fetch_one(
            """insert into products
            (id, business_id, category_id, name, description, price, is_available, menu_status)
            values (%(id)s, %(business_id)s, %(category_id)s, 'Masala Tea', 'Hot', 100, true, 'shown')
            returning id""",
            {"id": product_id, "business_id": business_id, "category_id": category_id},
        )
    return {
        "user_id": user_id,
        "business_id": business_id,
        "category_id": category_id,
        "product_id": product_id,
    }


def _production_counts(business_id: str) -> dict[str, int]:
    with db_context() as db:
        result = {}
        for table in ("orders", "order_items", "payments", "kitchen_events"):
            row = db.fetch_one(
                f"select count(*) as count from {table} where business_id = %(business_id)s",
                {"business_id": business_id},
            )
            result[table] = int(row["count"])
        return result


def test_dashboard_and_order_routes_match_live_schema() -> None:
    _require_live_db()
    seeded = _seed_setup_business()
    app.dependency_overrides[require_user_id] = lambda: seeded["user_id"]

    try:
        with TestClient(app) as client:
            for path in (
                f"/api/businesses/{seeded['business_id']}/dashboard",
                f"/api/businesses/{seeded['business_id']}/dashboard?start=2026-08-01T00:00:00Z&end=2026-08-10T23:59:59Z",
                f"/api/businesses/{seeded['business_id']}/orders",
                f"/api/businesses/{seeded['business_id']}/orders/active",
                f"/api/businesses/{seeded['business_id']}/categories",
                f"/api/businesses/{seeded['business_id']}/products?include_unavailable=true",
            ):
                response = client.get(path)
                assert response.status_code == 200, response.text
    finally:
        app.dependency_overrides.pop(require_user_id, None)
        with db_context() as db:
            db.fetch_one("delete from businesses where id = %(id)s returning id", {"id": seeded["business_id"]})
            db.fetch_one("delete from app_users where id = %(id)s returning id", {"id": seeded["user_id"]})


def test_setup_command_rollback_concurrency_and_publish_lifecycle() -> None:
    _require_live_db()
    seeded = _seed_setup_business()
    user_id = seeded["user_id"]
    business_id = seeded["business_id"]
    product_id = seeded["product_id"]
    marker = f"rollback-{uuid4().hex}"
    app.dependency_overrides[require_user_id] = lambda: user_id

    try:
        # Commands do not fetch rows, including PostgreSQL table locks.
        with db_context() as db:
            assert db.fetch_one("select 1 as ok") == {"ok": 1}
            assert db.execute_command("lock table categories in share mode") == -1

        # A failed transaction is rolled back rather than partially committed.
        with pytest.raises(RuntimeError, match="force rollback"):
            with db_context() as db:
                db.fetch_one(
                    "insert into categories (business_id, name) values (%(business_id)s, %(name)s) returning id",
                    {"business_id": business_id, "name": marker},
                )
                raise RuntimeError("force rollback")
        with db_context() as db:
            assert db.fetch_one(
                "select id from categories where business_id = %(business_id)s and name = %(name)s",
                {"business_id": business_id, "name": marker},
            ) is None

        # Two writers using the same revision serialize; exactly one wins.
        def patch_setup() -> int:
            with TestClient(app) as client:
                response = client.patch(
                    f"/api/businesses/{business_id}/setup",
                    json={"expected_revision": 0, "intro_pending": False},
                )
                return response.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = sorted(pool.map(lambda _index: patch_setup(), range(2)))
        assert statuses == [200, 409]

        with TestClient(app) as client:
            initial = client.get(f"/api/businesses/{business_id}/setup")
            assert initial.status_code == 200, initial.text
            initial_data = initial.json()
            assert initial_data["setup"]["revision"] == 1
            assert initial_data["status"]["menuComplete"] is True
            assert initial_data["status"]["previewComplete"] is False
            before = _production_counts(business_id)

            preview = client.post(
                f"/api/businesses/{business_id}/setup/preview-attestations",
                json={"event_version": 1},
            )
            assert preview.status_code == 200, preview.text
            signature = preview.json()["signature"]
            assert preview.json()["status"]["previewComplete"] is True

            test_order = client.post(
                f"/api/businesses/{business_id}/setup/test-orders",
                json={
                    "event_version": 1,
                    "order_type": "dine_in",
                    "items": [{"product_id": product_id, "quantity": 1}],
                },
            )
            assert test_order.status_code == 200, test_order.text
            assert test_order.json()["test_order"]["operational_mode"] == "test"
            assert test_order.json()["test_order"]["confirmation_reached"] is True
            assert test_order.json()["status"]["publishable"] is True
            assert _production_counts(business_id) == before

            published = client.post(
                f"/api/businesses/{business_id}/setup/publish",
                json={"expected_revision": 1},
            )
            assert published.status_code == 200, published.text
            assert published.json()["status"]["published"] is True
            assert published.json()["setup"]["revision"] == 2

            with db_context() as db:
                stored = db.fetch_one(
                    "select config_signature from kiosk_published_configs where business_id = %(business_id)s",
                    {"business_id": business_id},
                )
                assert stored == {"config_signature": signature}
                db.fetch_one(
                    "update products set description = 'Changed after review' where id = %(id)s returning id",
                    {"id": product_id},
                )

            changed = client.get(f"/api/businesses/{business_id}/setup")
            assert changed.status_code == 200, changed.text
            assert changed.json()["signature"] != signature
            assert changed.json()["status"]["previewStale"] is True
            assert changed.json()["status"]["testStale"] is True
            assert changed.json()["status"]["publishable"] is False

            stale_publish = client.post(
                f"/api/businesses/{business_id}/setup/publish",
                json={"expected_revision": 2},
            )
            assert stale_publish.status_code == 409

            revision_conflict = client.patch(
                f"/api/businesses/{business_id}/setup",
                json={"expected_revision": 1, "current_step": "review-publish"},
            )
            assert revision_conflict.status_code == 409
    finally:
        app.dependency_overrides.pop(require_user_id, None)
        with db_context() as db:
            db.fetch_one("delete from businesses where id = %(id)s returning id", {"id": business_id})
            db.fetch_one("delete from app_users where id = %(id)s returning id", {"id": user_id})
