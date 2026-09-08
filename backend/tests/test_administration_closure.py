import pytest
from fastapi import HTTPException
from uuid import uuid4

from schemas import IntegrationInput
from services.administration_closure_service import PAYMENT_METHODS, PERMISSIONS, _validate_integration_locations, verify_webhook_signature


def test_closure_permission_and_payment_allowlists_are_explicit():
    assert {"card", "upi", "wallet", "cash", "pay_at_counter"} == PAYMENT_METHODS
    assert "security.manage" in PERMISSIONS


def test_webhook_signature_verification_uses_constant_time_comparison():
    import hashlib
    import hmac

    body = b'{"event":"order.completed"}'
    signature = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, "webhook-secret", signature)
    assert not verify_webhook_signature(body, "webhook-secret", "invalid")


def test_integration_location_mappings_are_tenant_scoped():
    business_id = uuid4()
    own_location = uuid4()
    foreign_location = uuid4()

    class Client:
        def fetch_all(self, _query, _params):
            return [{"id": str(own_location)}]

    payload = IntegrationInput(
        name="Orders",
        integration_type="orders",
        location_ids=[own_location],
        hardware_mappings=[{"hardware_type": "kitchen", "external_reference": "k1", "location_id": str(foreign_location)}],
    )
    with pytest.raises(HTTPException) as exc:
        _validate_integration_locations(Client(), business_id, payload)

    assert exc.value.status_code == 422
