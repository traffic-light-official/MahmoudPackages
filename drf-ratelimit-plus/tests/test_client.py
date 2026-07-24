"""Unit tests for Redis client resolution."""

from __future__ import annotations

import fakeredis
from django.test import override_settings

from drf_ratelimit_plus.client import get_redis_client, set_redis_client


class TestGetRedisClient:
    def test_explicit_client_override_is_used(self) -> None:
        fake = fakeredis.FakeRedis()
        set_redis_client(fake)
        assert get_redis_client() is fake
        set_redis_client(None)

    def test_cached_across_calls(self) -> None:
        fake = fakeredis.FakeRedis()
        set_redis_client(fake)
        assert get_redis_client() is get_redis_client()
        set_redis_client(None)

    def test_builds_from_redis_url_when_none_set(self) -> None:
        set_redis_client(None)
        with override_settings(RATELIMIT_PLUS={"REDIS_URL": "redis://localhost:6379/1"}):
            client = get_redis_client()
        assert client is not None
        set_redis_client(None)

    def test_redis_client_setting_resolves_a_dotted_instance(self) -> None:
        set_redis_client(None)
        with override_settings(
            RATELIMIT_PLUS={"REDIS_CLIENT": "tests.test_app.redis_singleton.CLIENT"}
        ):
            client = get_redis_client()
        assert isinstance(client, fakeredis.FakeRedis)
        set_redis_client(None)

    def test_redis_client_setting_resolves_a_dotted_factory_callable(self) -> None:
        set_redis_client(None)
        with override_settings(
            RATELIMIT_PLUS={"REDIS_CLIENT": "tests.test_app.redis_singleton.build_client"}
        ):
            client = get_redis_client()
        assert isinstance(client, fakeredis.FakeRedis)
        set_redis_client(None)

    def test_setting_change_invalidates_cache(self) -> None:
        fake = fakeredis.FakeRedis()
        set_redis_client(fake)
        assert get_redis_client() is fake
        with override_settings(RATELIMIT_PLUS={"REDIS_URL": "redis://localhost:6379/2"}):
            # override_settings itself fires setting_changed, clearing the cache.
            rebuilt = get_redis_client()
        assert rebuilt is not fake
        set_redis_client(None)
