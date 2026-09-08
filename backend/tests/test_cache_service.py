from types import SimpleNamespace

import pytest

from services import cache_service


class ThrowingRedis:
    def get(self, _key):
        raise ConnectionError("redis unavailable")

    def setex(self, _key, _ttl, _payload):
        raise ConnectionError("redis unavailable")

    def delete(self, _key):
        raise ConnectionError("redis unavailable")


def test_redis_operation_failures_degrade_to_cache_misses(monkeypatch):
    monkeypatch.setattr(cache_service, "_redis_client", lambda: ThrowingRedis())
    monkeypatch.setattr(
        cache_service,
        "get_settings",
        lambda: SimpleNamespace(redis_menu_ttl_seconds=120),
    )

    assert cache_service.get_menu("demo") is None
    cache_service.set_menu("demo", {"items": []})
    cache_service.invalidate_slug("demo")


def test_invalid_cached_json_stays_a_cache_miss_when_delete_fails(monkeypatch):
    client = ThrowingRedis()
    client.get = lambda _key: "not-json"
    monkeypatch.setattr(cache_service, "_redis_client", lambda: client)

    assert cache_service.get_menu("demo") is None


def test_cache_does_not_hide_payload_serialization_errors(monkeypatch):
    monkeypatch.setattr(cache_service, "_redis_client", lambda: ThrowingRedis())
    monkeypatch.setattr(
        cache_service,
        "get_settings",
        lambda: SimpleNamespace(redis_menu_ttl_seconds=120),
    )

    with pytest.raises(TypeError):
        cache_service.set_menu("demo", {"invalid": object()})


def test_cache_does_not_hide_database_errors(monkeypatch):
    class FailingDb:
        def execute_one(self, *_args, **_kwargs):
            raise RuntimeError("database failure")

    monkeypatch.setattr(cache_service, "_redis_client", lambda: ThrowingRedis())

    with pytest.raises(RuntimeError, match="database failure"):
        cache_service.invalidate_business(FailingDb(), "business-id")
