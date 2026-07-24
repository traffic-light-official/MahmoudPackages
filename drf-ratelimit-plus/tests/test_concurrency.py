"""Genuine multi-threaded tests proving each algorithm's atomicity.

Each algorithm's Redis Lua script executes atomically server-side, so
concurrent callers from multiple Python threads must never collectively
exceed the configured limit - these tests use real
:class:`concurrent.futures.ThreadPoolExecutor` workers against a shared
``fakeredis`` instance to verify that directly, not just simulate it
sequentially.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import fakeredis

from drf_ratelimit_plus.algorithms import (
    fixed_window_check,
    sliding_window_check,
    token_bucket_check,
)
from drf_ratelimit_plus.rates import parse_rate


class TestFixedWindowConcurrency:
    def test_exactly_the_limit_succeeds_under_concurrency(self) -> None:
        client = fakeredis.FakeRedis()
        rate = parse_rate("10/m")

        def attempt(_: int) -> bool:
            return fixed_window_check(client, "shared", rate).allowed

        with ThreadPoolExecutor(max_workers=30) as executor:
            results = list(executor.map(attempt, range(30)))

        assert sum(results) == 10


class TestSlidingWindowConcurrency:
    def test_exactly_the_limit_succeeds_under_concurrency(self) -> None:
        client = fakeredis.FakeRedis()
        rate = parse_rate("10/m")

        def attempt(_: int) -> bool:
            return sliding_window_check(client, "shared", rate, now=0.0).allowed

        with ThreadPoolExecutor(max_workers=30) as executor:
            results = list(executor.map(attempt, range(30)))

        assert sum(results) == 10


class TestTokenBucketConcurrency:
    def test_exactly_capacity_succeeds_under_concurrency(self) -> None:
        client = fakeredis.FakeRedis()
        rate = parse_rate("10/m")

        def attempt(_: int) -> bool:
            return token_bucket_check(client, "shared", rate, burst=10, now=0.0).allowed

        with ThreadPoolExecutor(max_workers=30) as executor:
            results = list(executor.map(attempt, range(30)))

        assert sum(results) == 10
