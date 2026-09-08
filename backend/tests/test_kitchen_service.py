from datetime import datetime, timedelta, timezone

import jwt
import pytest

from config import get_settings
from schemas import KitchenAvailabilityUpdate, KitchenHoldRequest, KitchenItemCompletion
from services.order_service import VALID_TRANSITIONS


def test_kitchen_lifecycle_keeps_ready_separate_from_handover():
    assert VALID_TRANSITIONS["pending"] == {"preparing", "cancelled"}
    assert VALID_TRANSITIONS["preparing"] == {"ready", "cancelled"}
    assert "completed" not in VALID_TRANSITIONS["preparing"]


def test_kitchen_item_completion_and_hold_validation():
    assert KitchenItemCompletion(completed_quantity=2, event_id="00000000-0000-0000-0000-000000000001").completed_quantity == 2
    assert KitchenHoldRequest(reason="Awaiting fresh batch", event_id="00000000-0000-0000-0000-000000000001").reason
    with pytest.raises(ValueError):
        KitchenAvailabilityUpdate(status="available", event_id="not-a-uuid")


def test_kitchen_override_token_is_device_and_action_scoped():
    now = datetime.now(timezone.utc)
    token = jwt.encode({"type": "kitchen_override", "action": "recall", "business_id": "business", "device_id": "device", "iat": now, "exp": now + timedelta(minutes=5)}, get_settings().jwt_secret, algorithm=get_settings().jwt_algorithm)
    claims = jwt.decode(token, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
    assert (claims["type"], claims["action"], claims["device_id"]) == ("kitchen_override", "recall", "device")
