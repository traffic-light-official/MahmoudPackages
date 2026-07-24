"""Genuine multi-threaded race-condition tests.

These exercise :class:`~drf_idempotency.backends.redis.RedisBackend`
(backed by ``fakeredis``, which is safe for real concurrent access from
multiple threads within one process) with real
:class:`concurrent.futures.ThreadPoolExecutor` workers, proving that
exactly one of many simultaneous ``acquire_or_get`` calls for the same key
succeeds — not just simulating the race sequentially.

The database backend relies on the same atomicity primitive Django's
``get_or_create`` documents (a unique constraint plus catching the
resulting ``IntegrityError``), which is inherently connection-safe across
processes/threads; see ``tests/test_backends_database.py`` for its
sequential-conflict coverage. Testing it with genuine OS threads would
require a file-based (not in-memory) SQLite database to allow multiple
connections, which is unnecessary complexity for what the same underlying
Django primitive already guarantees.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import fakeredis

from drf_idempotency.backends.redis import RedisBackend


class TestConcurrentAcquisition:
    def test_exactly_one_of_many_concurrent_acquisitions_succeeds(self) -> None:
        backend = RedisBackend(client=fakeredis.FakeRedis())
        worker_count = 20

        def attempt(i: int) -> bool:
            result = backend.acquire_or_get("shared-key", f"fp-{i}", lock_ttl=timedelta(seconds=30))
            return result.acquired

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(attempt, range(worker_count)))

        assert sum(results) == 1

    def test_losers_see_the_winners_fingerprint(self) -> None:
        backend = RedisBackend(client=fakeredis.FakeRedis())
        worker_count = 10

        def attempt(i: int) -> str | None:
            result = backend.acquire_or_get("shared-key", f"fp-{i}", lock_ttl=timedelta(seconds=30))
            if result.acquired:
                return f"fp-{i}"
            assert result.existing is not None
            return result.existing.fingerprint

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(attempt, range(worker_count)))

        # Every worker (winner and losers alike) must agree on exactly one
        # fingerprint - the winner's.
        assert len(set(results)) == 1
