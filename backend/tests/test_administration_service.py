from uuid import uuid4

from services.administration_service import _safe_event


def test_activity_log_masks_sensitive_metadata_without_hiding_safe_fields():
    event = _safe_event({"metadata": {"provider_key": "secret", "request_token": "secret", "location": "Main"}})

    assert event["metadata"]["provider_key"] == "••••••••"
    assert event["metadata"]["request_token"] == "••••••••"
    assert event["metadata"]["location"] == "Main"
