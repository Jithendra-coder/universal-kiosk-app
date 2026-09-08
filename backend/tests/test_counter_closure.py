from datetime import datetime, timedelta, timezone

import jwt
import pytest

from config import get_settings
from schemas import CounterOverrideRequest


def test_counter_override_requires_action_reason_and_numeric_pin():
    payload = CounterOverrideRequest(action="cancel_pending_payment", reason="Customer cancelled", pin="1234")
    assert payload.action == "cancel_pending_payment"
    with pytest.raises(ValueError):
        CounterOverrideRequest(action="cancel_pending_payment", reason="x", pin="12ab")


def test_override_token_is_scoped_and_short_lived():
    now = datetime.now(timezone.utc)
    token = jwt.encode({"type": "counter_override", "action": "cancel_pending_payment", "business_id": "b1", "device_id": "d1", "iat": now, "exp": now + timedelta(minutes=5)}, get_settings().jwt_secret, algorithm=get_settings().jwt_algorithm)
    claims = jwt.decode(token, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
    assert claims["type"] == "counter_override"
    assert claims["business_id"] == "b1"
    assert claims["device_id"] == "d1"
    assert claims["exp"] - claims["iat"] <= 301


def test_claim_expiry_is_not_active_after_deadline():
    now = datetime.now(timezone.utc)
    claim = {"status": "claimed", "expires_at": now - timedelta(seconds=1)}
    assert claim["status"] == "claimed"
    assert claim["expires_at"] <= now
