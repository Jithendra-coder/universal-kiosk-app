from uuid import UUID

import pytest
from fastapi import HTTPException

from services import test_runtime_service


PRODUCT_ID = UUID("00000000-0000-0000-0000-000000000001")
SESSION_A = {"id": "session-a", "business_id": "business-a", "created_by": "user-a"}
SESSION_B = {"id": "session-b", "business_id": "business-a", "created_by": "user-a"}


class AvailabilityClient:
    def __init__(self):
        self.products = {str(PRODUCT_ID): {"id": str(PRODUCT_ID), "business_id": "business-a", "name": "Tea", "is_available": True}}
        self.overrides = {}
        self.commands = []

    def fetch_all(self, sql, params):
        if "from products p" not in sql:
            return []
        result = []
        for product in self.products.values():
            override = self.overrides.get((params["test_session_id"], product["id"]))
            result.append({
                "product_id": product["id"], "business_id": product["business_id"], "name": product["name"],
                "base_is_available": product["is_available"], "override_is_available": override,
                "is_available": product["is_available"] if override is None else override,
                "has_override": override is not None,
            })
        return result

    def fetch_one(self, sql, params):
        if "select id,name,is_available from products" in sql or "select id from products" in sql:
            product = self.products.get(params["product_id"])
            return product if product and product["business_id"] == params["business_id"] else None
        if "insert into test_runtime_availability_overrides" in sql:
            key = (params["test_session_id"], params["product_id"])
            self.overrides[key] = params["is_available"]
            return {"test_session_id": key[0], "product_id": key[1], "is_available": params["is_available"]}
        raise AssertionError(sql)

    def execute_command(self, sql, params):
        self.commands.append((sql, params))
        if "delete from test_runtime_availability_overrides" in sql and "product_id" in params:
            self.overrides.pop((params["test_session_id"], params["product_id"]), None)
        return 1


def use_session(monkeypatch, session):
    monkeypatch.setattr(test_runtime_service.test_session_service, "runtime_context", lambda *_args: {**session, "app_type": "kitchen"})


def test_test_override_changes_only_current_session_effective_availability(monkeypatch):
    client = AvailabilityClient()
    use_session(monkeypatch, SESSION_A)

    test_runtime_service.set_availability(client, "token", PRODUCT_ID, False)
    current = test_runtime_service.availability(client, "token", "kitchen")[0]

    use_session(monkeypatch, SESSION_B)
    other_session = test_runtime_service.availability(client, "token", "kitchen")[0]

    assert current["base_is_available"] is True
    assert current["is_available"] is False
    assert current["has_override"] is True
    assert other_session["is_available"] is True
    assert client.products[str(PRODUCT_ID)]["is_available"] is True


def test_clear_test_override_restores_base_availability(monkeypatch):
    client = AvailabilityClient()
    use_session(monkeypatch, SESSION_A)
    test_runtime_service.set_availability(client, "token", PRODUCT_ID, False)
    test_runtime_service.clear_availability(client, "token", PRODUCT_ID)

    result = test_runtime_service.availability(client, "token", "kitchen")[0]
    assert result["is_available"] is True
    assert result["has_override"] is False


def test_test_availability_rejects_product_from_another_business(monkeypatch):
    client = AvailabilityClient()
    use_session(monkeypatch, {**SESSION_A, "business_id": "business-b"})

    with pytest.raises(HTTPException) as exc:
        test_runtime_service.set_availability(client, "token", PRODUCT_ID, False)
    assert exc.value.status_code == 404
