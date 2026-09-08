from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException

from config import get_settings
from schemas import ReauthenticateRequest, ResetPasswordRequest
from services import auth_service


class ActiveSessionClient:
    def __init__(self, expires_at=None, revoked_at=None): self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(minutes=5); self.revoked_at = revoked_at; self.updated = False
    def execute_one(self, _sql, _params): return {"expires_at": self.expires_at, "revoked_at": self.revoked_at}
    def execute_command(self, _sql, _params): self.updated = True; return 1


def test_valid_active_session_decodes_and_updates_activity():
    user_id, session_id = uuid4(), uuid4(); token = auth_service.create_access_token(user_id, "user@example.com", session_id=session_id)
    client = ActiveSessionClient()
    assert auth_service.decode_access_token(token) == user_id
    assert auth_service.assert_session_active(client, token) == user_id
    assert client.updated is True


@pytest.mark.parametrize("token", ["malformed", jwt.encode({"type": "device_session", "sub": str(uuid4()), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, get_settings().jwt_secret, algorithm=get_settings().jwt_algorithm), jwt.encode({"type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, get_settings().jwt_secret, algorithm=get_settings().jwt_algorithm), jwt.encode({"type": "access", "sub": str(uuid4()), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, get_settings().jwt_secret, algorithm=get_settings().jwt_algorithm)])
def test_invalid_access_tokens_are_controlled_401(token):
    with pytest.raises(HTTPException) as error: auth_service.decode_access_token(token)
    assert error.value.status_code == 401


def test_revoked_and_expired_sessions_are_controlled_401():
    token = auth_service.create_access_token(uuid4(), "user@example.com", session_id=uuid4())
    for client in (ActiveSessionClient(revoked_at=datetime.now(timezone.utc)), ActiveSessionClient(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))):
        with pytest.raises(HTTPException) as error: auth_service.assert_session_active(client, token)
        assert error.value.status_code == 401


def test_logout_revokes_the_server_session():
    user_id, session_id = uuid4(), uuid4()
    token = auth_service.create_access_token(user_id, "user@example.com", session_id=session_id)

    class Client:
        command = None

        def execute_command(self, sql, params):
            self.command = (sql, params)

    client = Client()
    auth_service.revoke_session(client, token)

    assert "set revoked_at" in client.command[0]
    assert client.command[1]["id"] == str(session_id)


def test_password_reset_revokes_all_existing_sessions():
    user_id, reset_id = str(uuid4()), str(uuid4())

    class Client:
        revoked_user_id = None

        def execute_one(self, sql, params):
            if "from password_reset_tokens" in sql:
                return {"id": reset_id, "user_id": user_id}
            return {"id": params.get("id") or params.get("user_id")}

        def execute_command(self, sql, params):
            assert "update auth_sessions set revoked_at" in sql
            self.revoked_user_id = params["user_id"]

    client = Client()
    auth_service.reset_password(client, ResetPasswordRequest(token="x" * 40, password="MenuTapTest1"))

    assert client.revoked_user_id == user_id


def test_recent_auth_rejects_stale_session_and_accepts_current_session():
    business_id, user_id, session_id = uuid4(), uuid4(), uuid4()

    class Client:
        def __init__(self, reauthenticated_at): self.reauthenticated_at = reauthenticated_at

        def execute_one(self, _sql, _params):
            return {"reauthenticated_at": self.reauthenticated_at, "reauthentication_minutes": 15}

    auth_service.require_recent_auth(Client(datetime.now(timezone.utc)), business_id, user_id, session_id)
    with pytest.raises(HTTPException) as error:
        auth_service.require_recent_auth(Client(datetime.now(timezone.utc) - timedelta(minutes=16)), business_id, user_id, session_id)
    assert error.value.status_code == 403


def test_reauthenticate_refreshes_the_current_session():
    user_id, session_id = uuid4(), uuid4()
    token = auth_service.create_access_token(user_id, "user@example.com", session_id=session_id)

    class Client:
        updated = False

        def execute_one(self, sql, _params):
            if "from auth_sessions" in sql:
                return {"expires_at": datetime.now(timezone.utc) + timedelta(minutes=5), "revoked_at": None}
            return {"password_hash": auth_service.hash_password("MenuTapTest1")}

        def execute_command(self, sql, _params):
            self.updated = self.updated or "reauthenticated_at" in sql
            return 1

    client = Client()
    auth_service.reauthenticate(client, user_id, token, ReauthenticateRequest(password="MenuTapTest1"))
    assert client.updated
