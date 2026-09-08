from uuid import UUID

import pytest

from schemas import BusinessCreate, BusinessUpdate
from services import business_service


USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class CompletionClient:
    def __init__(self):
        self.writes = 0

    def fetch_one(self, sql, _params):
        assert "set onboarding_completed = true, onboarding_step = 6" in sql
        self.writes += 1
        return {"onboarding_completed": True, "onboarding_step": 6}


def status_for(monkeypatch, business):
    client = CompletionClient()
    monkeypatch.setattr(business_service, "get_primary_business_for_user", lambda *_args: business)
    return client, business_service.onboarding_status(client, USER_ID)


@pytest.mark.parametrize(
    ("step", "route"),
    [
        (0, "/setup/business-type"),
        (1, "/setup/business-details"),
        (2, "/setup/menu-items"),
        (3, "/setup/kiosk-layout"),
        (4, "/setup/welcome-screen"),
        (5, "/setup/test-kiosk"),
    ],
)
def test_incomplete_onboarding_uses_the_backend_step_route(monkeypatch, step, route):
    business = {
        "id": "business-id",
        "name": "New business",
        "type": "restaurant",
        "is_active": True,
        "onboarding_step": step,
        "onboarding_completed": False,
        "kiosk_order_settings": {"setup": {"version": 2, "active": True}},
    }
    client, status = status_for(monkeypatch, business)

    assert status["next_route"] == route
    assert status["onboarding_completed"] is False
    assert client.writes == 0


def test_completed_onboarding_routes_to_dashboard_without_a_write(monkeypatch):
    business = {
        "id": "business-id",
        "onboarding_step": 6,
        "onboarding_completed": True,
        "kiosk_order_settings": {"setup": {"version": 2, "completedAt": "2026-08-08T00:00:00Z"}},
    }
    client, status = status_for(monkeypatch, business)

    assert status["next_route"] == "/dashboard"
    assert client.writes == 0


@pytest.mark.parametrize(
    "business",
    [
        {
            "id": "published-v2",
            "name": "Published",
            "type": "restaurant",
            "is_active": True,
            "onboarding_step": 5,
            "onboarding_completed": False,
            "kiosk_order_settings": {"setup": {"version": 2, "publishedSignature": "signature"}},
        },
        {
            "id": "legacy-business",
            "name": "Legacy",
            "type": "restaurant",
            "is_active": True,
            "onboarding_step": 0,
            "onboarding_completed": False,
            "kiosk_order_settings": {},
        },
    ],
)
def test_durable_completion_evidence_is_reconciled_once(monkeypatch, business):
    client, status = status_for(monkeypatch, business)

    assert status["onboarding_completed"] is True
    assert status["onboarding_step"] == 6
    assert status["next_route"] == "/dashboard"
    assert client.writes == 1


def test_general_business_patch_cannot_set_completion_or_skip_the_final_step():
    with pytest.raises(ValueError):
        BusinessUpdate.model_validate({"onboarding_completed": True})
    with pytest.raises(ValueError):
        BusinessUpdate(onboarding_step=6)
    with pytest.raises(ValueError):
        BusinessCreate(name="Invalid", onboarding_step=6)


@pytest.mark.parametrize("step", [-1, 6, 99])
def test_invalid_incomplete_step_never_falls_through_to_dashboard(step):
    assert business_service._setup_route(step).startswith("/setup/")
