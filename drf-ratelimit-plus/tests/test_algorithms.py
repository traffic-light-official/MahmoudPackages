"""Direct tests of the Redis Lua-script-based algorithms, against fakeredis."""

from __future__ import annotations

import fakeredis
import pytest

from drf_ratelimit_plus.algorithms import (
    fixed_window_check,
    sliding_window_check,
    token_bucket_check,
)
from drf_ratelimit_plus.rates import parse_rate


@pytest.fixture
def redis_client() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis()


class TestFixedWindow:
    def test_allows_up_to_the_limit(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("3/m")
        results = [fixed_window_check(redis_client, "k1", rate) for _ in range(3)]
        assert all(r.allowed for r in results)

    def test_denies_beyond_the_limit(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("3/m")
        for _ in range(3):
            fixed_window_check(redis_client, "k1", rate)
        result = fixed_window_check(redis_client, "k1", rate)
        assert result.allowed is False
        assert result.retry_after is not None
        assert result.retry_after > 0

    def test_remaining_decreases(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("5/m")
        first = fixed_window_check(redis_client, "k1", rate)
        second = fixed_window_check(redis_client, "k1", rate)
        assert first.remaining == 4
        assert second.remaining == 3

    def test_weighted_cost_consumes_multiple_units(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("10/m")
        result = fixed_window_check(redis_client, "k1", rate, cost=5)
        assert result.allowed is True
        assert result.remaining == 5

    def test_different_keys_are_independent(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("1/m")
        r1 = fixed_window_check(redis_client, "k1", rate)
        r2 = fixed_window_check(redis_client, "k2", rate)
        assert r1.allowed is True
        assert r2.allowed is True

    def test_limit_is_reported_correctly(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("42/m")
        result = fixed_window_check(redis_client, "k1", rate)
        assert result.limit == 42


class TestSlidingWindowClusterSafety:
    def test_current_and_previous_window_keys_share_a_hash_tag(
        self, redis_client: fakeredis.FakeRedis
    ) -> None:
        """Both window keys must hash to the same Redis Cluster slot -
        achieved by wrapping the whole base key in '{...}' so only that
        content (not the differing window-index suffix) affects hashing.
        See docs/architecture.md."""
        rate = parse_rate("3/m")
        sliding_window_check(redis_client, "identity-42", rate, now=0.0)
        keys = {k.decode() if isinstance(k, bytes) else k for k in redis_client.keys("*")}
        assert keys, "expected at least one key to have been written"
        for key in keys:
            assert key.startswith("{identity-42}:"), key


class TestSlidingWindow:
    def test_allows_up_to_the_limit(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("3/m")
        now = 1_000_000.0
        results = [sliding_window_check(redis_client, "k1", rate, now=now) for _ in range(3)]
        assert all(r.allowed for r in results)

    def test_denies_beyond_the_limit(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("3/m")
        now = 1_000_000.0
        for _ in range(3):
            sliding_window_check(redis_client, "k1", rate, now=now)
        result = sliding_window_check(redis_client, "k1", rate, now=now)
        assert result.allowed is False

    def test_previous_window_weight_decays_over_time(
        self, redis_client: fakeredis.FakeRedis
    ) -> None:
        rate = parse_rate("4/m")  # period = 60s
        # Fill the window at t=0 (window index 0).
        for _ in range(4):
            sliding_window_check(redis_client, "k1", rate, now=0.0)
        # Just into the next window (t=61s): previous window's weight is
        # still high (only ~1s elapsed into new window), so it should
        # still be effectively full and deny.
        just_after = sliding_window_check(redis_client, "k1", rate, now=61.0)
        assert just_after.allowed is False
        # Deep into the next window (t=110s, i.e. 50s in): previous
        # window's weight has decayed enough to allow more requests.
        later = sliding_window_check(redis_client, "k1", rate, now=110.0)
        assert later.allowed is True

    def test_weighted_cost(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("10/m")
        result = sliding_window_check(redis_client, "k1", rate, cost=5, now=0.0)
        assert result.allowed is True
        assert result.remaining == 5


class TestTokenBucket:
    def test_allows_up_to_capacity(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("5/m")
        results = [token_bucket_check(redis_client, "k1", rate, burst=5, now=0.0) for _ in range(5)]
        assert all(r.allowed for r in results)

    def test_denies_beyond_capacity(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("5/m")
        for _ in range(5):
            token_bucket_check(redis_client, "k1", rate, burst=5, now=0.0)
        result = token_bucket_check(redis_client, "k1", rate, burst=5, now=0.0)
        assert result.allowed is False
        assert result.retry_after is not None

    def test_refills_over_time(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("60/m")  # 1 token/sec
        for _ in range(60):
            token_bucket_check(redis_client, "k1", rate, burst=60, now=0.0)
        depleted = token_bucket_check(redis_client, "k1", rate, burst=60, now=0.0)
        assert depleted.allowed is False

        # 10 seconds later, ~10 tokens should have refilled.
        refilled = token_bucket_check(redis_client, "k1", rate, burst=60, now=10.0)
        assert refilled.allowed is True

    def test_burst_defaults_to_rate_count(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("3/m")
        results = [token_bucket_check(redis_client, "k1", rate, now=0.0) for _ in range(3)]
        assert all(r.allowed for r in results)
        fourth = token_bucket_check(redis_client, "k1", rate, now=0.0)
        assert fourth.allowed is False

    def test_capacity_never_exceeds_burst_even_after_long_idle(
        self, redis_client: fakeredis.FakeRedis
    ) -> None:
        rate = parse_rate("60/m")
        token_bucket_check(redis_client, "k1", rate, burst=10, now=0.0)
        # A huge amount of idle time shouldn't let tokens exceed capacity.
        result = token_bucket_check(redis_client, "k1", rate, burst=10, cost=10, now=1_000_000.0)
        assert result.allowed is True
        assert result.remaining == 0

    def test_weighted_cost(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("10/m")
        result = token_bucket_check(redis_client, "k1", rate, burst=10, cost=4, now=0.0)
        assert result.allowed is True
        assert result.remaining == 6

    def test_limit_reports_capacity_not_rate_count(self, redis_client: fakeredis.FakeRedis) -> None:
        rate = parse_rate("5/m")
        result = token_bucket_check(redis_client, "k1", rate, burst=20, now=0.0)
        assert result.limit == 20
