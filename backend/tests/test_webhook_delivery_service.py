import hashlib
import hmac
from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.webhook_delivery_service import MAX_ATTEMPTS, RETRY_DELAYS_SECONDS, _classify, _signature, canonical_event, resolve_endpoint, validate_endpoint_url


def test_event_envelope_and_stable_id():
    business_id = uuid4()
    event = canonical_event(business_id, "order.completed", {"order_id": "o-1"}, event_id="evt-1")
    assert event["id"] == "evt-1"
    assert event["business_id"] == str(business_id)
    assert event["version"] == 1


def test_signature_is_deterministic_over_timestamp_and_exact_body():
    body = b'{"id":"evt-1"}'
    expected = "sha256=" + hmac.new(b"secret", b"1700000000." + body, hashlib.sha256).hexdigest()
    assert _signature("secret", "1700000000", body) == expected


def test_retry_classification_and_backoff_are_bounded():
    assert all(_classify(status, None) for status in (408, 429, 500, 503))
    assert not _classify(400, None)
    assert _classify(None, TimeoutError())
    assert len(RETRY_DELAYS_SECONDS) == MAX_ATTEMPTS - 1


@pytest.mark.parametrize("url", ["http://example.com/hook", "https://user:password@example.com/hook", "https://10.0.0.8/hook"])
def test_webhook_endpoint_rejects_unsafe_destinations(url):
    with pytest.raises(HTTPException) as exc:
        validate_endpoint_url(url)

    assert exc.value.status_code == 422


def test_webhook_endpoint_accepts_public_https_destination():
    assert validate_endpoint_url("https://8.8.8.8/hook") == "https://8.8.8.8/hook"


@pytest.mark.parametrize("url", ["https://[::1]/hook", "https://169.254.169.254/hook", "https://example.com:8443/hook", "https://example.com/hook#fragment"])
def test_webhook_endpoint_rejects_additional_unsafe_destinations(url):
    with pytest.raises(HTTPException) as exc:
        resolve_endpoint(url)
    assert exc.value.status_code == 422


def test_webhook_endpoint_rejects_mixed_dns_answers(monkeypatch):
    monkeypatch.setattr("services.webhook_delivery_service.socket.getaddrinfo", lambda *_args, **_kwargs: [(None, None, None, None, ("8.8.8.8", 443)), (None, None, None, None, ("10.0.0.8", 443))])
    with pytest.raises(HTTPException) as exc:
        resolve_endpoint("https://webhook.example/hook")
    assert exc.value.status_code == 422
