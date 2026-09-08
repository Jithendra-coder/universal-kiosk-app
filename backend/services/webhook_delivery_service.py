from __future__ import annotations

import hashlib
import http.client
import hmac
import ipaddress
import json
import secrets
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from config import get_settings
from database import DbClient
from services.administration_closure_service import unseal_webhook_secret

MAX_ATTEMPTS = 5
RETRY_DELAYS_SECONDS = (60, 300, 1800, 7200)
TRANSIENT_STATUSES = {408, 425, 429, 500, 502, 503, 504}
WEBHOOK_CONNECT_TIMEOUT_SECONDS = 5
WEBHOOK_READ_TIMEOUT_SECONDS = 10
WEBHOOK_RESPONSE_BYTES = 8192


def _now() -> datetime:
    return datetime.now(timezone.utc)


def validate_endpoint_url(url: str) -> str:
    return resolve_endpoint(url).url


class _Endpoint:
    def __init__(self, url: str, target: str, hostname: str, port: int, addresses: tuple[ipaddress.IPv4Address | ipaddress.IPv6Address, ...]):
        self.url = url
        self.target = target
        self.hostname = hostname
        self.port = port
        self.addresses = addresses


def resolve_endpoint(url: str) -> _Endpoint:
    parsed = urlparse((url or "").strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise HTTPException(status_code=422, detail="Webhook endpoints must use HTTPS without embedded credentials.")
    try:
        port = parsed.port or 443
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Webhook endpoint port is invalid.") from exc
    if port != 443:
        raise HTTPException(status_code=422, detail="Webhook endpoints must use the standard HTTPS port.")

    hostname = parsed.hostname.rstrip(".").lower()
    target = (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else "")
    try:
        addresses = [ipaddress.ip_address(hostname)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)]
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Webhook endpoint host could not be resolved safely.") from exc

    if not addresses or any(not _is_public_address(address) for address in addresses):
        raise HTTPException(status_code=422, detail="Webhook endpoints cannot target private or local network addresses.")
    return _Endpoint(parsed.geturl(), target, hostname, port, tuple(dict.fromkeys(addresses)))


def _is_public_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    mapped = getattr(address, "ipv4_mapped", None)
    return address.is_global and (mapped is None or mapped.is_global)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to the validated address while keeping TLS validation on the hostname."""

    def __init__(self, hostname: str, address: ipaddress.IPv4Address | ipaddress.IPv6Address, port: int):
        super().__init__(hostname, port=port, timeout=WEBHOOK_CONNECT_TIMEOUT_SECONDS, context=ssl.create_default_context())
        self._address = str(address)

    def connect(self) -> None:
        sock = socket.create_connection((self._address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_HTTP_OPENER = urllib.request.build_opener(_NoRedirect)


def canonical_event(business_id: UUID, event_type: str, data: dict, location_id: UUID | None = None, event_id: str | None = None) -> dict:
    return {"id": event_id or str(uuid4()), "type": event_type, "version": 1, "created_at": _now().isoformat(), "business_id": str(business_id), "location_id": str(location_id) if location_id else None, "data": data}


def enqueue_event(client: DbClient, business_id: UUID, event_type: str, data: dict, location_id: UUID | None = None, event_id: str | None = None) -> str:
    event = canonical_event(business_id, event_type, data, location_id, event_id)
    event_identifier = event["id"]
    webhooks = client.fetch_all("select id,events from integration_webhooks where business_id=%(business_id)s and is_active=true", {"business_id": str(business_id)})
    for webhook in webhooks:
        if event_type not in (webhook.get("events") or []):
            continue
        client.execute_one("insert into integration_webhook_deliveries (webhook_id,business_id,event_type,event_identifier,payload,attempt_number,status,next_retry_at) values (%(webhook_id)s,%(business_id)s,%(event_type)s,%(event_id)s,%(payload)s,1,'pending',now()) on conflict (webhook_id,event_identifier) do nothing returning id", {"webhook_id": webhook["id"], "business_id": str(business_id), "event_type": event_type, "event_id": event_identifier, "payload": Jsonb(event)})
    return event_identifier


def claim_next(client: DbClient, worker_id: str | None = None, lease_seconds: int = 60) -> dict | None:
    worker_id = worker_id or secrets.token_hex(8)
    return client.execute_one("""with candidate as (select id from integration_webhook_deliveries where (status in ('pending','retry_scheduled') and coalesce(next_retry_at,now())<=now()) or (status='delivering' and claim_expires_at<now()) order by coalesce(next_retry_at,requested_at),created_at for update skip locked limit 1) update integration_webhook_deliveries d set status='delivering',claimed_by=%(worker_id)s,claim_expires_at=now()+(%(lease)s || ' seconds')::interval,last_attempted_at=now() from candidate where d.id=candidate.id returning d.*""", {"worker_id": worker_id, "lease": lease_seconds})


def _signature(secret: str, timestamp: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def _classify(status: int | None, error: Exception | None) -> bool:
    return error is not None or status in TRANSIENT_STATUSES


def _record_activity(client: DbClient, row: dict, action: str, metadata: dict) -> None:
    client.table("audit_logs").insert({"business_id": str(row["business_id"]), "user_id": None, "action": action, "entity": "integration_webhook", "entity_id": str(row["webhook_id"]), "metadata": Jsonb(metadata)}).execute()


def dispatch_claimed(client: DbClient, row: dict) -> dict:
    webhook = client.execute_one("select id,business_id,endpoint_url,is_active,signing_secret_ciphertext from integration_webhooks where id=%(id)s and business_id=%(business_id)s", {"id": row["webhook_id"], "business_id": row["business_id"]})
    if not webhook or not webhook.get("is_active"):
        return _finish(client, row, "failed", None, 0, "Webhook is disabled or endpoint configuration is invalid.", False)
    try:
        endpoint = resolve_endpoint(webhook["endpoint_url"])
    except HTTPException as exc:
        return _finish(client, row, "failed", None, 0, str(exc.detail), False)
    body = json.dumps(row["payload"], separators=(",", ":"), ensure_ascii=False).encode()
    timestamp = str(int(time.time()))
    secret = unseal_webhook_secret(webhook["signing_secret_ciphertext"]) if webhook.get("signing_secret_ciphertext") else None
    if not secret:
        return _finish(client, row, "failed", None, 0, "Webhook signing secret is unavailable.", False)
    request_headers = {"Content-Type": "application/json", "X-MenuTap-Event-Id": str(row["event_identifier"]), "X-MenuTap-Event-Type": row["event_type"], "X-MenuTap-Delivery-Id": str(row["id"]), "X-MenuTap-Timestamp": timestamp, "X-MenuTap-Signature": _signature(secret, timestamp, body)}
    started = time.monotonic(); status = None; error = None
    connection = None
    try:
        connection = _PinnedHTTPSConnection(endpoint.hostname, endpoint.addresses[0], endpoint.port)
        connection.request("POST", endpoint.target, body=body, headers=request_headers)
        assert connection.sock is not None
        connection.sock.settimeout(WEBHOOK_READ_TIMEOUT_SECONDS)
        response = connection.getresponse()
        status = int(response.status)
        response.read(WEBHOOK_RESPONSE_BYTES)
    except (TimeoutError, OSError, ssl.SSLError, http.client.HTTPException) as exc:
        error = exc
    finally:
        if connection:
            connection.close()
    duration = int((time.monotonic() - started) * 1000)
    retryable = _classify(status, error)
    return _finish(client, row, "delivered" if status is not None and 200 <= status < 300 else "retry_scheduled" if retryable and int(row["attempt_number"]) < MAX_ATTEMPTS else "failed", status, duration, str(error)[:500] if error else None, retryable)


def _finish(client: DbClient, row: dict, status: str, response_status: int | None, duration: int, error: str | None, retryable: bool) -> dict:
    attempt = int(row["attempt_number"])
    next_retry = _now() + timedelta(seconds=RETRY_DELAYS_SECONDS[min(attempt - 1, len(RETRY_DELAYS_SECONDS) - 1)]) if status == "retry_scheduled" else None
    client.execute_command("update integration_webhook_deliveries set status=%(status)s,retry_state=%(status)s,response_status=%(response)s,duration_ms=%(duration)s,sanitized_error=%(error)s,next_retry_at=%(next_retry)s,completed_at=case when %(status)s='delivered' then now() else completed_at end,failed_at=case when %(status)s='failed' then now() else failed_at end,claim_expires_at=null where id=%(id)s", {"id": row["id"], "status": status, "response": response_status, "duration": duration, "error": error, "next_retry": next_retry})
    if status == "retry_scheduled":
        client.execute_one("insert into integration_webhook_deliveries (webhook_id,business_id,event_type,event_identifier,payload,attempt_number,status,next_retry_at) values (%(webhook_id)s,%(business_id)s,%(event_type)s,%(event_identifier)s,%(payload)s,%(attempt)s,'retry_scheduled',%(next_retry)s) on conflict (webhook_id,event_identifier,attempt_number) do nothing returning id", {**row, "attempt": attempt + 1, "next_retry": next_retry, "payload": Jsonb(row["payload"])})
    if status in {"delivered", "failed"}:
        _record_activity(client, row, "webhook_delivered" if status == "delivered" else "webhook_delivery_failed", {"event_id": row["event_identifier"], "attempt": attempt, "response_status": response_status, "error": error})
    return {"id": row["id"], "status": status, "attempt_number": attempt, "next_retry_at": next_retry, "response_status": response_status, "duration_ms": duration, "sanitized_error": error}


def retry_delivery(client: DbClient, business_id: UUID, user_id: UUID, delivery_id: UUID) -> dict:
    row = client.execute_one("select * from integration_webhook_deliveries where id=%(id)s and business_id=%(business_id)s", {"id": str(delivery_id), "business_id": str(business_id)})
    if not row: raise HTTPException(status_code=404, detail="Delivery not found.")
    next_attempt = client.execute_one("insert into integration_webhook_deliveries (webhook_id,business_id,event_type,event_identifier,payload,attempt_number,status,next_retry_at) select webhook_id,business_id,event_type,event_identifier,payload,coalesce(max(attempt_number),0)+1,'pending',now() from integration_webhook_deliveries where webhook_id=%(webhook_id)s and event_identifier=%(event_identifier)s group by webhook_id,business_id,event_type,event_identifier,payload on conflict (webhook_id,event_identifier,attempt_number) do nothing returning id,attempt_number", {"webhook_id": row["webhook_id"], "business_id": str(business_id), "event_identifier": row["event_identifier"]})
    if not next_attempt: raise HTTPException(status_code=409, detail="A retry is already queued.")
    client.table("audit_logs").insert({"business_id": str(business_id), "user_id": str(user_id), "action": "webhook_delivery_manual_retry", "entity": "integration_webhook", "entity_id": str(row["webhook_id"]), "metadata": Jsonb({"delivery_id": str(delivery_id), "attempt": next_attempt["attempt_number"]})}).execute()
    return next_attempt


def run_once(client: DbClient, worker_id: str | None = None) -> dict | None:
    row = claim_next(client, worker_id)
    return dispatch_claimed(client, row) if row else None
