from types import SimpleNamespace

import pytest

from services import auth_service


class AuthClient:
    def execute_one(self, sql: str, _params: dict):
        if "select id from app_users" in sql:
            return {"id": "00000000-0000-0000-0000-000000000001"}
        return {"id": "00000000-0000-0000-0000-000000000002"}


@pytest.mark.parametrize("environment", ["prod", "production"])
def test_production_without_smtp_never_exposes_auth_secrets(monkeypatch, environment):
    settings = SimpleNamespace(
        environment=environment,
        dev_expose_reset_links=True,
        frontend_base_url="https://app.menutap.example",
    )
    monkeypatch.setattr(auth_service, "get_settings", lambda: settings)
    monkeypatch.setattr(auth_service.mail_service, "is_configured", lambda: False)
    monkeypatch.setattr(auth_service.mail_service, "send_email_verification", lambda *_args: False)
    monkeypatch.setattr(auth_service.mail_service, "send_password_reset", lambda *_args: False)

    verification = auth_service._send_verification_code(
        AuthClient(),
        "00000000-0000-0000-0000-000000000001",
        "owner@example.test",
    )
    reset = auth_service.create_password_reset(AuthClient(), "owner@example.test")

    assert verification["dev_otp"] is None
    assert reset["reset_url"] is None
    assert reset["message"] == "If that email exists, a password reset email has been sent."


def test_reset_links_always_use_configured_frontend(monkeypatch):
    settings = SimpleNamespace(
        environment="local",
        dev_expose_reset_links=True,
        frontend_base_url="https://dashboard.menutap.example/base/",
    )
    monkeypatch.setattr(auth_service, "get_settings", lambda: settings)

    url = auth_service.create_password_reset_url(
        AuthClient(),
        "00000000-0000-0000-0000-000000000001",
    )

    assert url.startswith("https://dashboard.menutap.example/base/auth/reset-password?token=")
