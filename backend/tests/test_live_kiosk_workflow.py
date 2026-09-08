import os
import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from database import db_context
from main import app
from services import cache_service, payment_service


pytestmark = pytest.mark.live_db


def _cleanup_user(email: str) -> None:
    with db_context() as client:
        client.execute_one("delete from app_users where email = %(email)s returning id", {"email": email})


def _business_row_counts(business_id: str) -> dict[str, int]:
    tables = ["orders", "order_items", "kitchen_events", "payments"]
    with db_context() as db:
        counts = {}
        for table in tables:
            row = db.execute_one(
                f"select count(*) as count from {table} where business_id = %(business_id)s",
                {"business_id": business_id},
            )
            counts[table] = int(row["count"] if row else 0)
        return counts


def _product_inventory(product_id: str) -> dict:
    with db_context() as db:
        row = db.execute_one(
            "select stock_quantity, sold_today from products where id = %(product_id)s",
            {"product_id": product_id},
        )
        assert row is not None
        return row


def test_full_kiosk_order_inventory_and_kitchen_flow(monkeypatch):
    if os.getenv("RUN_LIVE_DB_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_DB_TESTS=1 to run the live PostgreSQL workflow test.")

    client = TestClient(app)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    email = f"qa-autotest+{suffix}@example.test"
    password = "QaAutomation123!"
    slug = f"qa-cafe-{suffix.lower()}"

    _cleanup_user(email)
    try:
        signup = client.post(
            "/api/auth/signup",
            json={"email": email, "password": password, "full_name": "QA Autotest"},
        )
        assert signup.status_code == 200, signup.text
        dev_otp = signup.json().get("dev_otp")
        if not dev_otp:
            pytest.skip("Local verification code was not exposed by this environment.")

        verified = client.post("/api/auth/verify-email", json={"email": email, "code": dev_otp})
        assert verified.status_code == 200, verified.text
        headers = {}

        duplicate_signup = client.post(
            "/api/auth/signup",
            json={"email": email, "password": password, "full_name": "QA Autotest"},
        )
        assert duplicate_signup.status_code == 409

        injection_login = client.post(
            "/api/auth/login",
            json={"email": "' OR '1'='1@example.test", "password": "NotThePassword1!"},
        )
        assert injection_login.status_code == 401

        business = client.post(
            "/api/businesses",
            headers=headers,
            json={
                "name": "QA Automation Cafe",
                "slug": slug,
                "type": "cafe",
                "tax_percent": 5,
                "opening_time": "00:00",
                "closing_time": "23:59",
                "order_modes": ["dine_in", "takeaway"],
                "kiosk_order_settings": {
                    "public_online_ordering_enabled": True,
                    "online_payments": True,
                    "payment_methods": ["stripe"],
                    "default_payment_method": "stripe",
                },
                "onboarding_step": 4,
            },
        )
        assert business.status_code == 200, business.text
        business_data = business.json()["data"]
        business_id = business_data["id"]
        with db_context() as db:
            db.fetch_one(
                """insert into business_payment_accounts
                (business_id, provider, provider_account_id, provider_merchant_id,
                 connection_status, payments_enabled, charges_enabled, is_enabled)
                values (%(business_id)s, 'stripe', 'acct_test', 'merchant_test',
                        'active', true, true, true)
                returning id""",
                {"business_id": business_id},
            )

        category = client.post(
            f"/api/businesses/{business_id}/categories",
            headers=headers,
            json={"name": "QA Drinks", "sort_order": 0},
        )
        assert category.status_code == 200, category.text
        category_id = category.json()["data"]["id"]

        other_business = client.post(
            "/api/businesses",
            headers=headers,
            json={"name": "QA Other Cafe", "slug": f"{slug}-other", "type": "cafe"},
        )
        assert other_business.status_code == 200, other_business.text
        other_business_id = other_business.json()["data"]["id"]
        other_category = client.post(
            f"/api/businesses/{other_business_id}/categories",
            headers=headers,
            json={"name": "Other Category", "sort_order": 0},
        )
        assert other_category.status_code == 200, other_category.text

        cross_tenant_product = client.post(
            f"/api/businesses/{business_id}/products",
            headers=headers,
            json={
                "category_id": other_category.json()["data"]["id"],
                "name": "Bad Category Link",
                "price": 10,
            },
        )
        assert cross_tenant_product.status_code == 400

        product = client.post(
            f"/api/businesses/{business_id}/products",
            headers=headers,
            json={
                "category_id": category_id,
                "name": "QA Masala Tea",
                "description": "Live test item",
                "item_type": "veg",
                "price": 100,
                "track_stock": True,
                "stock_quantity": 2,
                "daily_limit": 5,
                "is_available": True,
            },
        )
        assert product.status_code == 200, product.text
        product_id = product.json()["data"]["id"]

        before_preview_counts = _business_row_counts(business_id)
        before_preview_inventory = _product_inventory(product_id)
        cache_invalidations = []
        with monkeypatch.context() as preview_cache_watch:
            preview_cache_watch.setattr(
                cache_service,
                "invalidate_slug",
                lambda slug: cache_invalidations.append(("slug", slug)),
            )
            preview_cache_watch.setattr(
                cache_service,
                "invalidate_business",
                lambda db, target_business_id: cache_invalidations.append(("business", target_business_id)),
            )

            preview_render = client.post(
                "/api/admin/preview-kiosk/render",
                headers=headers,
                json={
                    "business_id": business_id,
                    "draft": {
                        "name": "QA Preview Cafe",
                        "pin": "1234",
                        "kiosk_lock_settings": {"pin": "1234", "locked": True},
                    },
                },
            )
            assert preview_render.status_code == 200, preview_render.text
            preview_payload = preview_render.json()["preview"]
            assert preview_payload["business"]["name"] == "QA Preview Cafe"
            assert product_id in {item["id"] for item in preview_payload["products"]}
            assert "1234" not in json.dumps(preview_payload).lower()
            assert '"pin"' not in json.dumps(preview_payload).lower()

        assert cache_invalidations == []
        assert _business_row_counts(business_id) == before_preview_counts
        assert _product_inventory(product_id) == before_preview_inventory

        invalid_upload = client.post(
            f"/api/businesses/{business_id}/uploads/product-image",
            headers=headers,
            files={"file": ("not-image.txt", b"plain text", "text/plain")},
        )
        assert invalid_upload.status_code == 400

        def fake_online_checkout(db, _business, _order, payment, _method, _provider):
            db.table("payments").update({"status": "paid"}).eq("id", payment["id"]).execute()
            db.table("orders").update({"status": "pending", "payment_status": "paid"}).eq("id", payment["order_id"]).execute()
            return {"payment": {**payment, "status": "paid"}, "checkout_url": "https://checkout.test/session"}

        monkeypatch.setattr(payment_service, "_create_online_checkout", fake_online_checkout)

        menu = client.get(f"/api/kiosk/{slug}/menu")
        assert menu.status_code == 200, menu.text
        assert any(item["id"] == product_id for item in menu.json()["products"])

        order = client.post(
            f"/api/kiosk/{slug}/orders",
            json={"order_type": "dine_in", "payment_method": "stripe", "items": [{"product_id": product_id, "quantity": 1}]},
        )
        assert order.status_code == 200, order.text
        order_data = order.json()["data"]
        assert order_data["subtotal"] == 100
        assert order_data["tax_amount"] == 5
        assert order_data["total_amount"] == 105

        oversized_order = client.post(
            f"/api/kiosk/{slug}/orders",
            json={"order_type": "dine_in", "items": [{"product_id": product_id, "quantity": 99}]},
        )
        assert oversized_order.status_code == 409

        products = client.get(f"/api/businesses/{business_id}/products", headers=headers)
        assert products.status_code == 200, products.text
        updated_product = next(item for item in products.json()["products"] if item["id"] == product_id)
        assert updated_product["stock_quantity"] == 1
        assert updated_product["sold_today"] == 1

        active_orders = client.get(f"/api/businesses/{business_id}/orders/active", headers=headers)
        assert active_orders.status_code == 200, active_orders.text
        assert any(item["id"] == order_data["id"] for item in active_orders.json()["orders"])

        for status in ["preparing", "ready", "completed"]:
            status_response = client.patch(
                f"/api/orders/{order_data['id']}/status",
                headers=headers,
                json={"business_id": business_id, "status": status},
            )
            assert status_response.status_code == 200, status_response.text

        invalid_transition = client.patch(
            f"/api/orders/{order_data['id']}/status",
            headers=headers,
            json={"business_id": business_id, "status": "pending"},
        )
        assert invalid_transition.status_code == 409
    finally:
        _cleanup_user(email)
