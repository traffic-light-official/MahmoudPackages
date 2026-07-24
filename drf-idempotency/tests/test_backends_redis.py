"""Tests for the Redis-backed idempotency storage, using fakeredis.

A small number of tests are marked ``@pytest.mark.redis`` and additionally
run against a real Redis server when ``REDIS_URL`` is set in the
environment (e.g. in CI, where a Redis service container is available);
they're skipped automatically otherwise.
"""

from __future__ import annotations

import os
import time
from datetime import timedelta

import fakeredis
import pytest

from drf_idempotency.backends.redis import RedisBackend


@pytest.fixture
def backend() -> RedisBackend:
    return RedisBackend(client=fakeredis.FakeRedis())


class TestAcquireOrGet:
    def test_first_acquisition_succeeds(self, backend: RedisBackend) -> None:
        result = backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        assert result.acquired is True
        assert result.existing is None

    def test_second_acquisition_with_active_lock_fails(self, backend: RedisBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        result = backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        assert result.acquired is False
        assert result.existing is not None
        assert result.existing.status == "in_progress"

    def test_lock_expires_naturally_via_ttl(self, backend: RedisBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=1))
        time.sleep(1.2)
        result = backend.acquire_or_get("key-1", "fp-2", lock_ttl=timedelta(seconds=30))
        assert result.acquired is True


class TestComplete:
    def test_stores_response_for_replay(self, backend: RedisBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        backend.complete(
            "key-1",
            status_code=201,
            headers={"X-Foo": "bar"},
            body=b'{"ok": true}',
            ttl=timedelta(seconds=60),
        )
        record = backend.get("key-1")
        assert record is not None
        assert record.status == "completed"
        assert record.response_status_code == 201
        assert record.response_body == b'{"ok": true}'
        assert record.response_headers == {"X-Foo": "bar"}
        assert record.fingerprint == "fp-1"


class TestFail:
    def test_deletes_the_key(self, backend: RedisBackend) -> None:
        backend.acquire_or_get("key-1", "fp-1", lock_ttl=timedelta(seconds=30))
        backend.fail("key-1")
        assert backend.get("key-1") is None

    def test_is_a_no_op_for_unknown_key(self, backend: RedisBackend) -> None:
        backend.fail("does-not-exist")  # must not raise


class TestGet:
    def test_returns_none_for_unknown_key(self, backend: RedisBackend) -> None:
        assert backend.get("does-not-exist") is None


class TestCleanupExpired:
    def test_always_returns_zero(self, backend: RedisBackend) -> None:
        assert backend.cleanup_expired() == 0


class TestKeyPrefixing:
    def test_records_are_namespaced_by_prefix(self) -> None:
        client = fakeredis.FakeRedis()
        backend_a = RedisBackend(client=client, key_prefix="app-a:")
        backend_b = RedisBackend(client=client, key_prefix="app-b:")
        backend_a.acquire_or_get("shared-key", "fp", lock_ttl=timedelta(seconds=30))
        result = backend_b.acquire_or_get("shared-key", "fp", lock_ttl=timedelta(seconds=30))
        assert result.acquired is True  # different prefix, no collision


class TestMissingRedisDependency:
    def test_clear_error_when_redis_package_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import importlib
        import sys

        monkeypatch.setitem(sys.modules, "redis", None)
        sys.modules.pop("drf_idempotency.backends.redis", None)
        try:
            with pytest.raises(ImportError) as exc_info:
                importlib.import_module("drf_idempotency.backends.redis")
            assert "drf-idempotency[redis]" in str(exc_info.value)
        finally:
            sys.modules.pop("drf_idempotency.backends.redis", None)
            monkeypatch.undo()
            importlib.import_module("drf_idempotency.backends.redis")


@pytest.mark.redis
class TestRealRedis:
    """Runs against a real Redis server when REDIS_URL is set; skipped otherwise."""

    @pytest.fixture(autouse=True)
    def _skip_without_real_redis(self) -> None:
        url = os.environ.get("REDIS_URL")
        if not url:
            pytest.skip("REDIS_URL not set; skipping real-Redis test")
        import redis as redis_lib

        client = redis_lib.Redis.from_url(url)
        try:
            client.ping()
        except Exception:
            pytest.skip("Redis server not reachable; skipping real-Redis test")
        self.client = client
        self.client.flushdb()

    def test_acquire_and_complete_round_trip(self) -> None:
        backend = RedisBackend(client=self.client, key_prefix="drf-idempotency-test:")
        result = backend.acquire_or_get("real-key", "fp", lock_ttl=timedelta(seconds=30))
        assert result.acquired is True
        backend.complete(
            "real-key", status_code=200, headers={}, body=b"ok", ttl=timedelta(seconds=30)
        )
        record = backend.get("real-key")
        assert record is not None
        assert record.response_body == b"ok"
