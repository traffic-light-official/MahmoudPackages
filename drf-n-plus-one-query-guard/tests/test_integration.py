"""End-to-end tests: a real APIClient request through the full middleware stack."""

from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from drf_n_plus_one_query_guard.testing import assert_no_n_plus_one

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


class TestArticleListEndToEnd:
    def test_unoptimized_endpoint_triggers_the_guard(
        self, api_client: APIClient, several_articles
    ) -> None:
        with override_settings(DEBUG=True, N_PLUS_ONE_GUARD={"MODE": "report", "THRESHOLD": 2}):
            response = api_client.get("/articles/")

        assert response.status_code == 200
        assert "X-N-Plus-One-Warnings" in response

    def test_optimized_endpoint_does_not_trigger_the_guard(
        self, api_client: APIClient, several_articles
    ) -> None:
        with override_settings(DEBUG=True, N_PLUS_ONE_GUARD={"MODE": "report", "THRESHOLD": 2}):
            response = api_client.get("/optimized-articles/")

        assert response.status_code == 200
        assert "X-N-Plus-One-Warnings" not in response

    def test_unoptimized_endpoint_returns_correct_data_regardless_of_guard_mode(
        self, api_client: APIClient, several_articles
    ) -> None:
        with override_settings(N_PLUS_ONE_GUARD={"MODE": "report"}):
            response = api_client.get("/articles/")

        assert len(response.data) == len(several_articles)

    def test_assert_no_n_plus_one_around_a_real_client_call(
        self, api_client: APIClient, several_articles
    ) -> None:
        with pytest.raises(AssertionError), assert_no_n_plus_one():
            api_client.get("/articles/")

    def test_assert_no_n_plus_one_passes_for_the_optimized_endpoint(
        self, api_client: APIClient, several_articles
    ) -> None:
        with assert_no_n_plus_one():
            api_client.get("/optimized-articles/")
