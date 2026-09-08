from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, status

from config import get_settings
from database import DbClient
from schemas import AuthLogin, AuthSignup, ReauthenticateRequest, ResetPasswordRequest, ResendVerificationRequest, SignupEmailComplete, VerifyEmailRequest
from services import mail_service

PASSWORD_ITERATIONS = 310_000
SESSION_COOKIE_NAME = "menutap_admin_session"
SIGNUP_SESSION_COOKIE_NAME = "menutap_signup_session"
INTERNAL_SESSION_TOKEN_FIELD = "_session_token"
INTERNAL_SIGNUP_TOKEN_FIELD = "_signup_token"


def signup(client: DbClient, payload: AuthSignup) -> dict:
    email = _normalize_email(payload.email)
    existing = client.execute_one(
        "select id, email, full_name, is_active, created_at from app_users where email = %(email)s limit 1",
        {"email": email},
    )
    if existing and existing.get("is_active"):
        raise HTTPException(status_code=409, detail="An account already exists for this email.")

    if existing:
        user = client.execute_one(
            """
            update app_users
            set password_hash = %(password_hash)s,
                full_name = %(full_name)s,
                is_active = false
            where id = %(id)s
            returning id, email, full_name, is_active, created_at
            """,
            {
                "id": existing["id"],
                "password_hash": hash_password(payload.password),
                "full_name": payload.full_name,
            },
        )
    else:
        user = client.execute_one(
            """
            insert into app_users (email, password_hash, full_name, is_active)
            values (%(email)s, %(password_hash)s, %(full_name)s, false)
            returning id, email, full_name, is_active, created_at
            """,
            {
                "email": email,
                "password_hash": hash_password(payload.password),
                "full_name": payload.full_name,
            },
        )
    client.table("profiles").upsert({"id": user["id"], "email": email, "full_name": payload.full_name}).execute()
    return _send_verification_code(client, user["id"], email)


def start_staged_signup(client: DbClient, email_value: str) -> dict:
    email = _normalize_email(email_value)
    existing = client.execute_one(
        "select id, email, is_active from app_users where email = %(email)s limit 1",
        {"email": email},
    )
    if existing and existing.get("is_active"):
        raise HTTPException(status_code=409, detail="An account already exists for this email.")

    if existing:
        user_id = existing["id"]
    else:
        user = client.execute_one(
            """
            insert into app_users (email, password_hash, is_active)
            values (%(email)s, %(password_hash)s, false)
            returning id, email, is_active
            """,
            {"email": email, "password_hash": hash_password(secrets.token_urlsafe(32))},
        )
        user_id = user["id"]
        client.table("profiles").upsert({"id": user_id, "email": email}).execute()
    return _send_verification_code(client, user_id, email)


def verify_staged_signup(client: DbClient, payload: VerifyEmailRequest) -> dict:
    user = _consume_verification_code(client, payload)
    return {
        "email": user["email"],
        "message": "Email verified. Create your password to finish.",
        INTERNAL_SIGNUP_TOKEN_FIELD: create_signup_completion_token(UUID(str(user["id"])), user["email"]),
    }


def complete_staged_signup(client: DbClient, user_id: UUID, payload: SignupEmailComplete) -> dict:
    user = client.execute_one(
        """
        update app_users
        set password_hash = %(password_hash)s,
            full_name = %(full_name)s,
            is_active = true,
            last_login_at = now()
        where id = %(id)s and is_active = false
        returning id, email, full_name, is_active, created_at
        """,
        {
            "id": str(user_id),
            "password_hash": hash_password(payload.password),
            "full_name": payload.full_name,
        },
    )
    if not user:
        raise HTTPException(status_code=409, detail="This signup session is no longer valid.")
    client.table("profiles").upsert({"id": user["id"], "email": user["email"], "full_name": payload.full_name}).execute()
    mail_service.send_welcome_email(user["email"])
    return create_session(user, client)


def login(client: DbClient, payload: AuthLogin) -> dict:
    email = _normalize_email(payload.email)
    user = client.execute_one(
        "select * from app_users where email = %(email)s limit 1",
        {"email": email},
    )
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Please verify your email before signing in.")

    client.execute_one(
        "update app_users set last_login_at = now() where id = %(id)s returning id",
        {"id": user["id"]},
    )
    return create_session(user, client)


def verify_email(client: DbClient, payload: VerifyEmailRequest) -> dict:
    user = _consume_verification_code(client, payload, allow_active=True)
    if user.get("is_active"):
        return create_session(user, client)
    activated = client.execute_one(
        """
        update app_users
        set is_active = true,
            last_login_at = now()
        where id = %(id)s
        returning id, email, full_name, is_active, created_at
        """,
        {"id": user["id"]},
    )
    mail_service.send_welcome_email(user["email"])
    return create_session(activated, client)


def _consume_verification_code(
    client: DbClient,
    payload: VerifyEmailRequest,
    *,
    allow_active: bool = False,
) -> dict:
    email = _normalize_email(payload.email)
    user = client.execute_one(
        "select id, email, full_name, is_active, created_at from app_users where email = %(email)s limit 1",
        {"email": email},
    )
    if not user:
        raise HTTPException(status_code=400, detail="Verification code is invalid or expired.")
    if user.get("is_active"):
        if allow_active:
            return user
        raise HTTPException(status_code=409, detail="This account is already verified. Sign in instead.")
    row = client.execute_one(
        """
        select id, code_hash, attempt_count
        from email_verification_codes
        where user_id = %(user_id)s
          and used_at is null
          and expires_at > now()
        order by created_at desc
        limit 1
        """,
        {"user_id": user["id"]},
    )
    if not row:
        raise HTTPException(status_code=400, detail="Verification code is invalid or expired.")
    if int(row.get("attempt_count") or 0) >= 5:
        raise HTTPException(status_code=429, detail="Too many attempts. Request a new verification code.")

    accepts_test_code = get_settings().environment.lower() not in {"prod", "production"} and payload.code == "123456"
    if not accepts_test_code and not hmac.compare_digest(row["code_hash"], hash_verification_code(payload.code)):
        client.execute_one(
            "update email_verification_codes set attempt_count = attempt_count + 1 where id = %(id)s returning id",
            {"id": row["id"]},
        )
        raise HTTPException(status_code=400, detail="Verification code is incorrect.")

    client.execute_one(
        "update email_verification_codes set used_at = now() where id = %(id)s returning id",
        {"id": row["id"]},
    )
    return user


def resend_verification(client: DbClient, payload: ResendVerificationRequest) -> dict:
    email = _normalize_email(payload.email)
    user = client.execute_one(
        "select id, email, is_active from app_users where email = %(email)s limit 1",
        {"email": email},
    )
    if not user:
        return {
            "requires_verification": True,
            "email": email,
            "message": "If that account exists, a verification code has been sent.",
            "dev_otp": None,
        }
    if user.get("is_active"):
        raise HTTPException(status_code=409, detail="This account is already verified. Sign in instead.")
    return _send_verification_code(client, user["id"], email)


def create_session(user: dict, client: DbClient | None = None) -> dict:
    session_id = uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=get_settings().jwt_access_token_minutes)
    if client:
        policy = client.execute_one("select p.session_duration_minutes from business_security_policies p join businesses b on b.id=p.business_id where b.owner_id=%(user_id)s or exists (select 1 from business_staff s where s.business_id=p.business_id and s.user_id=%(user_id)s) order by p.session_duration_minutes asc limit 1", {"user_id": str(user["id"])})
        if policy and policy.get("session_duration_minutes"): expires_at = datetime.now(timezone.utc) + timedelta(minutes=int(policy["session_duration_minutes"]))
    token = create_access_token(UUID(str(user["id"])), user["email"], session_id=session_id, expires_at=expires_at)
    if client:
        client.execute_command("insert into auth_sessions (id,user_id,token_hash,expires_at,reauthenticated_at) values (%(id)s,%(user_id)s,%(hash)s,%(expires_at)s,now())", {"id": str(session_id), "user_id": str(user["id"]), "hash": hashlib.sha256(token.encode()).hexdigest(), "expires_at": expires_at})
    return {
        "access_token": None,
        "token_type": "bearer",
        "user": public_user(user),
        INTERNAL_SESSION_TOKEN_FIELD: token,
    }


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name"),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at"),
    }


def get_user(client: DbClient, user_id: UUID) -> dict:
    user = client.execute_one(
        "select id, email, full_name, is_active, created_at from app_users where id = %(id)s limit 1",
        {"id": str(user_id)},
    )
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return public_user(user)


def create_password_reset(client: DbClient, email: str) -> dict:
    normalized = _normalize_email(email)
    user = client.execute_one("select id from app_users where email = %(email)s limit 1", {"email": normalized})
    generic = "If that email exists, a password reset email has been sent."
    if not user:
        return {"message": generic, "reset_url": None}

    reset_url = create_password_reset_url(client, user["id"])
    sent = mail_service.send_password_reset(normalized, reset_url)
    settings = get_settings()
    non_production = settings.environment.lower() not in {"prod", "production"}
    expose_local_link = (
        non_production
        and (settings.dev_expose_reset_links or not mail_service.is_configured() or not sent)
    )
    return {
        "message": generic if sent or not non_production else "Email is not configured locally, so a reset page was prepared.",
        "reset_url": reset_url if expose_local_link else None,
    }


def create_password_reset_url(client: DbClient, user_id: str) -> str:
    raw_token = secrets.token_urlsafe(40)
    token_hash = hash_reset_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    client.execute_one(
        """
        insert into password_reset_tokens (user_id, token_hash, expires_at)
        values (%(user_id)s, %(token_hash)s, %(expires_at)s)
        returning id
        """,
        {"user_id": user_id, "token_hash": token_hash, "expires_at": expires_at},
    )
    base = get_settings().frontend_base_url.rstrip("/")
    return f"{base}/auth/reset-password?token={raw_token}"


def reset_password(client: DbClient, payload: ResetPasswordRequest) -> None:
    token_hash = hash_reset_token(payload.token)
    row = client.execute_one(
        """
        select prt.id, prt.user_id
        from password_reset_tokens prt
        join app_users u on u.id = prt.user_id
        where prt.token_hash = %(token_hash)s
          and prt.used_at is null
          and prt.expires_at > now()
          and u.is_active = true
        limit 1
        """,
        {"token_hash": token_hash},
    )
    if not row:
        raise HTTPException(status_code=400, detail="This reset link is invalid or expired.")

    client.execute_one(
        """
        update app_users
        set password_hash = %(password_hash)s
        where id = %(user_id)s
        returning id
        """,
        {"password_hash": hash_password(payload.password), "user_id": row["user_id"]},
    )
    client.execute_one(
        "update password_reset_tokens set used_at = now() where id = %(id)s returning id",
        {"id": row["id"]},
    )
    client.execute_command(
        "update auth_sessions set revoked_at = coalesce(revoked_at, now()) where user_id = %(user_id)s",
        {"user_id": row["user_id"]},
    )


def create_access_token(user_id: UUID, email: str, *, session_id: UUID | None = None, expires_at: datetime | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((expires_at or (now + timedelta(minutes=settings.jwt_access_token_minutes))).timestamp()),
        "type": "access",
    }
    if session_id: payload["sid"] = str(session_id)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_signup_completion_token(user_id: UUID, email: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
            "type": "signup_completion",
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_signup_completion_token(token: str) -> UUID:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "signup_completion" or not payload.get("sub"):
            raise ValueError
        return UUID(str(payload["sub"]))
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signup session expired. Verify your email again.") from exc


def decode_access_token(token: str) -> UUID:
    payload = _decode_access_payload(token)
    try:
        return UUID(str(payload["sub"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token.") from exc


def _decode_access_payload(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token.") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token.")
    try:
        UUID(str(payload["sub"]))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token.") from exc
    return payload


def session_id_from_access_token(token: str) -> UUID | None:
    try:
        payload = _decode_access_payload(token)
        return UUID(str(payload["sid"])) if payload.get("sid") else None
    except (HTTPException, ValueError, KeyError):
        return None


def revoke_session(client: DbClient, token: str | None) -> None:
    if not token:
        return
    session_id = session_id_from_access_token(token)
    if session_id:
        client.execute_command(
            "update auth_sessions set revoked_at = coalesce(revoked_at, now()) where id = %(id)s",
            {"id": str(session_id)},
        )


def assert_session_active(client: DbClient, token: str) -> UUID:
    payload = _decode_access_payload(token)
    try:
        session_id = UUID(str(payload["sid"]))
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth session.") from exc
    row = client.execute_one("select expires_at,revoked_at from auth_sessions where id=%(id)s and token_hash=%(hash)s", {"id": str(session_id), "hash": hashlib.sha256(token.encode()).hexdigest()})
    if not row or row.get("revoked_at"): raise HTTPException(status_code=401, detail="Session has been revoked.")
    expires_at = row["expires_at"]
    if isinstance(expires_at, str): expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at <= datetime.now(timezone.utc): raise HTTPException(status_code=401, detail="Session has expired.")
    client.execute_command(
        """update auth_sessions set last_active_at = now()
        where id = %(id)s and (last_active_at is null or last_active_at < now() - interval '1 minute')""",
        {"id": str(session_id)},
    )
    return user_id


def reauthenticate(client: DbClient, user_id: UUID, token: str, payload: ReauthenticateRequest) -> None:
    session_user_id = assert_session_active(client, token)
    if session_user_id != user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = client.execute_one("select password_hash from app_users where id=%(id)s and is_active=true", {"id": str(user_id)})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Password verification failed.")
    session_id = session_id_from_access_token(token)
    if not session_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    client.execute_command("update auth_sessions set reauthenticated_at=now() where id=%(id)s and user_id=%(user_id)s", {"id": str(session_id), "user_id": str(user_id)})


def require_recent_auth(client: DbClient, business_id: UUID, user_id: UUID, session_id: UUID | None) -> None:
    if not session_id:
        raise HTTPException(status_code=401, detail="A current session is required for this action.")
    row = client.execute_one(
        """select s.reauthenticated_at, coalesce(p.reauthentication_minutes, 15) as reauthentication_minutes
        from auth_sessions s left join business_security_policies p on p.business_id=%(business_id)s
        where s.id=%(session_id)s and s.user_id=%(user_id)s and s.revoked_at is null and s.expires_at>now()""",
        {"business_id": str(business_id), "session_id": str(session_id), "user_id": str(user_id)},
    )
    if not row or not row.get("reauthenticated_at"):
        raise HTTPException(status_code=401, detail="Please sign in again before this action.")
    reauthenticated_at = row["reauthenticated_at"]
    if isinstance(reauthenticated_at, str):
        reauthenticated_at = datetime.fromisoformat(reauthenticated_at.replace("Z", "+00:00"))
    if reauthenticated_at + timedelta(minutes=int(row["reauthentication_minutes"])) < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Please re-enter your password before this action.")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _send_verification_code(client: DbClient, user_id: str, email: str) -> dict:
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    client.execute_one(
        """
        update email_verification_codes
        set used_at = coalesce(used_at, now())
        where user_id = %(user_id)s
          and used_at is null
        returning id
        """,
        {"user_id": user_id},
    )
    client.execute_one(
        """
        insert into email_verification_codes (user_id, code_hash, expires_at)
        values (%(user_id)s, %(code_hash)s, %(expires_at)s)
        returning id
        """,
        {"user_id": user_id, "code_hash": hash_verification_code(code), "expires_at": expires_at},
    )
    sent = mail_service.send_email_verification(email, code)
    non_production = get_settings().environment.lower() not in {"prod", "production"}
    expose_local_code = (
        non_production
        and (not mail_service.is_configured() or not sent)
    )
    return {
        "requires_verification": True,
        "email": email,
        "message": "Enter the 6-digit verification code sent to your email.",
        "dev_otp": code if expose_local_code else None,
    }


def _normalize_email(email: str) -> str:
    return email.strip().lower()
