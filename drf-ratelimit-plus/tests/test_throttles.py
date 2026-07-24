"""Unit tests for the rate_limit() throttle factory."""

from __future__ import annotations

import fakeredis
import pytest
from rest_framework.test import APIRequestFactory

from drf_ratelimit_plus.exceptions import InvalidAlgorithmError
from drf_ratelimit_plus.throttles import rate_limit

factory = APIRequestFactory()


@pytest.fixture
def redis_client() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis()


class TestRateLimitFactory:
    def test_unknown_algorithm_raises_at_creation_time(self) -> None:
        with pytest.raises(InvalidAlgorithmError):
            rate_limit(algorithm="bogus")

    def test_allows_requests_within_the_limit(self, redis_client: fakeredis.FakeRedis) -> None:
        throttle_cls = rate_limit(
            rate="3/m", algorithm="token_bucket", burst=3, client=redis_client
        )
        throttle = throttle_cls()
        request = factory.get("/x/")
        assert throttle.allow_request(request, None) is True

    def test_denies_requests_beyond_the_limit(self, redis_client: fakeredis.FakeRedis) -> None:
        throttle_cls = rate_limit(
            rate="2/m", algorithm="token_bucket", burst=2, client=redis_client
        )
        request = factory.get("/x/")
        throttle_cls().allow_request(request, None)
        throttle_cls().allow_request(request, None)
        denied = throttle_cls()
        assert denied.allow_request(request, None) is False
        assert denied.wait() is not None
        assert denied.wait() > 0

    def test_wait_is_none_before_any_check(self) -> None:
        throttle_cls = rate_limit(rate="10/m")
        throttle = throttle_cls()
        assert throttle.wait() is None

    def test_wait_is_none_after_a_successful_check(self, redis_client: fakeredis.FakeRedis) -> None:
        throttle_cls = rate_limit(rate="10/m", client=redis_client)
        throttle = throttle_cls()
        request = factory.get("/x/")
        throttle.allow_request(request, None)
        assert throttle.wait() is None

    def test_dynamic_callable_rate(self, redis_client: fakeredis.FakeRedis) -> None:
        throttle_cls = rate_limit(
            rate=lambda request: "2/m", algorithm="fixed_window", client=redis_client
        )
        request = factory.get("/x/")
        throttle_cls().allow_request(request, None)
        throttle_cls().allow_request(request, None)
        assert throttle_cls().allow_request(request, None) is False

    def test_dynamic_callable_cost(self, redis_client: fakeredis.FakeRedis) -> None:
        throttle_cls = rate_limit(
            rate="10/m", algorithm="fixed_window", cost=lambda request: 7, client=redis_client
        )
        request = factory.get("/x/")
        result_ok = throttle_cls()
        assert result_ok.allow_request(request, None) is True
        assert result_ok.last_result is not None
        assert result_ok.last_result.remaining == 3

    def test_different_keys_get_independent_limits(self, redis_client: fakeredis.FakeRedis) -> None:
        throttle_cls = rate_limit(
            rate="1/m", algorithm="token_bucket", burst=1, key="ip", client=redis_client
        )
        req_a = factory.get("/x/", REMOTE_ADDR="1.1.1.1")
        req_b = factory.get("/x/", REMOTE_ADDR="2.2.2.2")
        assert throttle_cls().allow_request(req_a, None) is True
        assert throttle_cls().allow_request(req_b, None) is True

    def test_plan_tiers(self, redis_client: fakeredis.FakeRedis) -> None:
        from unittest.mock import Mock

        throttle_cls = rate_limit(
            rate={"free": "1/m", "pro": "5/m"},
            algorithm="token_bucket",
            key="user",
            client=redis_client,
        )
        free_request = factory.get("/x/")
        free_request.user = Mock(is_authenticated=True, pk=1, plan="free")
        assert throttle_cls().allow_request(free_request, None) is True
        assert throttle_cls().allow_request(free_request, None) is False

        pro_request = factory.get("/x/")
        pro_request.user = Mock(is_authenticated=True, pk=2, plan="pro")
        for _ in range(5):
            assert throttle_cls().allow_request(pro_request, None) is True

    def test_explicit_scope_shares_limit_across_views(
        self, redis_client: fakeredis.FakeRedis
    ) -> None:
        throttle_cls = rate_limit(
            rate="1/m", algorithm="token_bucket", burst=1, scope="shared", client=redis_client
        )
        request = factory.get("/x/")
        assert throttle_cls().allow_request(request, view=object()) is True
        # A different "view" but the same explicit scope shares the bucket.
        assert throttle_cls().allow_request(request, view=object()) is False
