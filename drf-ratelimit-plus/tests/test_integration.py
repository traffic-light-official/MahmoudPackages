"""End-to-end HTTP tests through the DRF test client."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


class TestTokenBucketView:
    def test_allows_requests_within_burst(self, client: APIClient) -> None:
        for _ in range(5):
            response = client.get("/token-bucket/")
            assert response.status_code == status.HTTP_200_OK

    def test_denies_beyond_burst(self, client: APIClient) -> None:
        for _ in range(5):
            client.get("/token-bucket/")
        response = client.get("/token-bucket/")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_429_includes_retry_after(self, client: APIClient) -> None:
        for _ in range(5):
            client.get("/token-bucket/")
        response = client.get("/token-bucket/")
        assert "Retry-After" in response.headers

    def test_headers_present_on_success(self, client: APIClient) -> None:
        response = client.get("/token-bucket/")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["RateLimit-Limit"] == "5"
        assert response.headers["RateLimit-Remaining"] == "4"
        assert "RateLimit-Reset" in response.headers

    def test_remaining_decreases_across_requests(self, client: APIClient) -> None:
        first = client.get("/token-bucket/")
        second = client.get("/token-bucket/")
        assert int(first.headers["RateLimit-Remaining"]) > int(
            second.headers["RateLimit-Remaining"]
        )


class TestFixedWindowView:
    def test_allows_then_denies(self, client: APIClient) -> None:
        for _ in range(5):
            assert client.get("/fixed-window/").status_code == status.HTTP_200_OK
        assert client.get("/fixed-window/").status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestSlidingWindowView:
    def test_allows_then_denies(self, client: APIClient) -> None:
        for _ in range(5):
            assert client.get("/sliding-window/").status_code == status.HTTP_200_OK
        assert client.get("/sliding-window/").status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestWeightedCostView:
    def test_cost_of_three_allows_only_three_requests_for_limit_ten(
        self, client: APIClient
    ) -> None:
        # capacity=10, cost=3 per request -> floor(10/3) = 3 successful requests
        results = [client.get("/weighted-cost/").status_code for _ in range(4)]
        assert results.count(status.HTTP_200_OK) == 3
        assert results.count(status.HTTP_429_TOO_MANY_REQUESTS) == 1


class TestPerUserView:
    def test_different_users_have_independent_limits(self, client: APIClient) -> None:
        from django.contrib.auth.models import User

        alice = User.objects.create_user(username="alice", password="x")
        bob = User.objects.create_user(username="bob", password="x")

        client.force_authenticate(alice)
        for _ in range(5):
            assert client.get("/per-user/").status_code == status.HTTP_200_OK
        assert client.get("/per-user/").status_code == status.HTTP_429_TOO_MANY_REQUESTS

        client.force_authenticate(bob)
        assert client.get("/per-user/").status_code == status.HTTP_200_OK


class TestTierView:
    def test_free_tier_gets_a_lower_limit(self, client: APIClient) -> None:
        from django.contrib.auth.models import User

        user = User.objects.create_user(username="freeuser", password="x")
        user.plan = "free"
        client.force_authenticate(user)
        assert client.get("/tier/").status_code == status.HTTP_200_OK
        assert client.get("/tier/").status_code == status.HTTP_200_OK
        assert client.get("/tier/").status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestDecoratedView:
    def test_allows_then_denies(self, client: APIClient) -> None:
        for _ in range(3):
            assert client.get("/decorated/").status_code == status.HTTP_200_OK
        response = client.get("/decorated/")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response.headers

    def test_headers_present_on_decorated_success(self, client: APIClient) -> None:
        response = client.get("/decorated/")
        assert response.headers["RateLimit-Limit"] == "3"
        assert response.headers["RateLimit-Remaining"] == "2"
