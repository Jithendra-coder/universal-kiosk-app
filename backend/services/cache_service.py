from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from config import get_settings
from database import DbClient


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _redis_client():
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        from redis import Redis
    except ImportError:
        return None
    return Redis.from_url(settings.redis_url, decode_responses=True)


def _menu_key(slug: str) -> str:
    return f"kiosk:menu:{slug}"


def _cache_warning(operation: str, exc: Exception) -> None:
    logger.warning(
        "Redis menu cache %s failed (%s); continuing without cache.",
        operation,
        type(exc).__name__,
    )


def _delete(client, key: str) -> None:
    try:
        client.delete(key)
    except Exception as exc:
        _cache_warning("delete", exc)


def get_menu(slug: str) -> dict[str, Any] | None:
    client = _redis_client()
    if not client:
        return None
    key = _menu_key(slug)
    try:
        cached = client.get(key)
    except Exception as exc:
        _cache_warning("get", exc)
        return None
    if not cached:
        return None
    try:
        return json.loads(cached)
    except json.JSONDecodeError:
        _delete(client, key)
        return None


def set_menu(slug: str, payload: dict[str, Any]) -> None:
    client = _redis_client()
    if not client:
        return
    settings = get_settings()
    serialized = json.dumps(payload)
    try:
        client.setex(_menu_key(slug), settings.redis_menu_ttl_seconds, serialized)
    except Exception as exc:
        _cache_warning("set", exc)


def invalidate_slug(slug: str | None) -> None:
    if not slug:
        return
    client = _redis_client()
    if client:
        _delete(client, _menu_key(slug))


def invalidate_business(client: DbClient, business_id: str) -> None:
    row = client.execute_one(
        "select slug from businesses where id = %(business_id)s limit 1",
        {"business_id": str(business_id)},
    )
    if row:
        invalidate_slug(row.get("slug"))
