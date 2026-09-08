import asyncio
from contextlib import contextmanager
from types import SimpleNamespace
from uuid import uuid4

from starlette.requests import Request

from routers import devices, kiosk, maintenance, media, payments, uploads


def request(body=b""):
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request({"type": "http", "method": "POST", "path": "/", "headers": [], "client": ("192.0.2.10", 1234)}, receive)


def capture_limit(monkeypatch, module):
    calls = []
    monkeypatch.setattr(module, "assert_rate_limit", lambda _request, rule, identity_parts=(): calls.append((rule, list(identity_parts))))
    return calls


def test_upload_and_media_limits_use_authenticated_identity(monkeypatch):
    upload_calls = capture_limit(monkeypatch, uploads)
    monkeypatch.setattr(uploads, "assert_business_access", lambda *_args: None)

    async def fake_upload(*_args, **_kwargs):
        return {"url": "/uploads/test.png"}

    monkeypatch.setattr(uploads, "upload_asset", fake_upload)
    business_id, user_id = uuid4(), uuid4()
    asyncio.run(uploads.upload_product_image(business_id, request(), object(), user_id, object()))
    assert upload_calls == [(uploads.UPLOAD_LIMIT, [str(user_id), str(business_id), "product"])]

    media_calls = capture_limit(monkeypatch, media)
    monkeypatch.setattr(media.pexels_service, "search_photos", lambda q, per_page: {"q": q, "per_page": per_page})
    assert media.search_pexels_images(request(), "coffee", 12, user_id) == {"q": "coffee", "per_page": 12}
    assert media_calls == [(media.PEXELS_SEARCH_LIMIT, [str(user_id)])]


def test_maintenance_limit_runs_before_secret_validation(monkeypatch):
    calls = capture_limit(monkeypatch, maintenance)
    settings = SimpleNamespace(payment_expiry_cron_secret="maintenance-secret", payment_expiry_minutes=30)
    monkeypatch.setattr(maintenance.payment_service, "expire_abandoned_pending_online_payments", lambda *_args, **_kwargs: {"expired": 0})
    assert maintenance.expire_pending_payments(request(), "maintenance-secret", settings, object()) == {"expired": 0}
    assert calls == [(maintenance.EXPIRE_PAYMENTS_LIMIT, ["maintenance-secret"])]


def test_payment_webhooks_have_separate_retry_friendly_limits(monkeypatch):
    calls = capture_limit(monkeypatch, payments)
    monkeypatch.setattr(payments.payment_service, "process_stripe_webhook", lambda _client, _body, signature: {"provider": "stripe", "signature": signature})
    monkeypatch.setattr(payments.payment_service, "process_razorpay_webhook", lambda _client, _body, signature: {"provider": "razorpay", "signature": signature})
    monkeypatch.setattr(payments.payment_service, "process_paytm_webhook", lambda _client, _body, signature: {"provider": "paytm", "signature": signature})

    asyncio.run(payments.stripe_webhook(request(b"{}"), "stripe-signature", object()))
    asyncio.run(payments.razorpay_webhook(request(b"{}"), "razorpay-signature", object()))
    asyncio.run(payments.paytm_webhook(request(b"{}"), None, "paytm-checksum", object()))

    assert calls == [
        (payments.STRIPE_WEBHOOK_LIMIT, ["stripe-signature"]),
        (payments.RAZORPAY_WEBHOOK_LIMIT, ["razorpay-signature"]),
        (payments.PAYTM_WEBHOOK_LIMIT, ["paytm-checksum"]),
    ]
    assert all(rule.max_requests == 300 and rule.window_seconds == 60 for rule, _identity in calls)


def test_device_session_limit_uses_session_value(monkeypatch):
    calls = capture_limit(monkeypatch, devices)
    monkeypatch.setattr(devices.device_service, "live_device_session_context", lambda *_args, **_kwargs: {"device": "ok"})
    result = devices.live_device_session_context(request(), "kitchen", "session-token", object())
    assert result == {"device": "ok"}
    assert calls == [(devices.SESSION_CONTEXT_LIMIT, ["session-token", "kitchen"])]


def test_public_kiosk_menu_reads_are_rate_limited(monkeypatch):
    calls = capture_limit(monkeypatch, kiosk)
    @contextmanager
    def context():
        yield object()

    monkeypatch.setattr(kiosk, "db_context", context)
    monkeypatch.setattr(kiosk.kiosk_service, "get_kiosk_payload", lambda *_args, **_kwargs: {"business": {}, "categories": [], "products": []})
    assert kiosk.get_kiosk("demo", request()) == {"business": {}, "categories": [], "products": []}
    assert calls == [(kiosk.PUBLIC_MENU_LIMIT, ["demo"])]
