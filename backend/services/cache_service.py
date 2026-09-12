import copy
import json
import logging
import threading
import time
from functools import lru_cache
from typing import Any

from config import get_settings
from database import DbClient


logger = logging.getLogger(__name__)

# Process-local fallback cache for high-speed menu reads before or during Redis deployment
_LOCAL_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_LOCAL_LOCK = threading.RLock()


@lru_cache(maxsize=1)
def _redis_client():
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        from redis import Redis
    except ImportError:
        return None
    try:
        client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
        )
        return client
    except Exception as exc:
        _cache_warning("connect", exc)
        return None


def _menu_key(slug: str) -> str:
    return f"kiosk:menu:{slug}"


def _cache_warning(operation: str, exc: Exception) -> None:
    logger.warning(
        "Redis menu cache %s failed (%s); continuing with local in-memory fallback.",
        operation,
        type(exc).__name__,
    )


def _delete(client, key: str) -> None:
    try:
        client.delete(key)
    except Exception as exc:
        _cache_warning("delete", exc)


def get_menu(slug: str) -> dict[str, Any] | None:
    now = time.monotonic()
    client = _redis_client()
    if client:
        key = _menu_key(slug)
        try:
            cached = client.get(key)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    _delete(client, key)
        except Exception as exc:
            _cache_warning("get", exc)

    # In-memory fallback lookup (sub-millisecond)
    with _LOCAL_LOCK:
        entry = _LOCAL_CACHE.get(slug)
        if entry:
            expires_at, data = entry
            if now < expires_at:
                return copy.deepcopy(data)
            _LOCAL_CACHE.pop(slug, None)
    return None


def set_menu(slug: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    ttl = max(10, settings.redis_menu_ttl_seconds)
    # Serialize first so serialization/type errors surface immediately
    serialized = json.dumps(payload)

    # Always keep local in-memory cache hot
    with _LOCAL_LOCK:
        _LOCAL_CACHE[slug] = (time.monotonic() + ttl, copy.deepcopy(payload))
        # Keep local cache bounded to 500 items
        if len(_LOCAL_CACHE) > 500:
            oldest_key = min(_LOCAL_CACHE, key=lambda k: _LOCAL_CACHE[k][0])
            _LOCAL_CACHE.pop(oldest_key, None)

    # Sync to Redis if available
    client = _redis_client()
    if client:
        try:
            client.setex(_menu_key(slug), ttl, serialized)
        except Exception as exc:
            _cache_warning("set", exc)


def invalidate_slug(slug: str | None) -> None:
    if not slug:
        return
    with _LOCAL_LOCK:
        _LOCAL_CACHE.pop(slug, None)
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

