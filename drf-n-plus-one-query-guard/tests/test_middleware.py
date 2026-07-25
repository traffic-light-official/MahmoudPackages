"""Tests for :mod:`drf_n_plus_one_query_guard.middleware`."""

from __future__ import annotations

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, override_settings

from drf_n_plus_one_query_guard.exceptions import NPlusOneDetectedError
from drf_n_plus_one_query_guard.middleware import NPlusOneGuardMiddleware
from tests.test_app.models import Article

pytestmark = pytest.mark.django_db


def _n_plus_one_response(request: HttpRequest) -> HttpResponse:
    for article in Article.objects.all():
        _ = article.author.name
    return HttpResponse("ok")


def _clean_response(request: HttpRequest) -> HttpResponse:
    list(Article.objects.select_related("author").all())
    return HttpResponse("ok")


class TestNPlusOneGuardMiddlewareDebugHeader:
    def test_adds_header_when_debug_and_violation_found(self, several_articles) -> None:
        middleware = NPlusOneGuardMiddleware(_n_plus_one_response)
        request = RequestFactory().get("/articles/")

        with override_settings(DEBUG=True, N_PLUS_ONE_GUARD={"MODE": "report", "THRESHOLD": 2}):
            response = middleware(request)

        assert "X-N-Plus-One-Warnings" in response

    def test_no_header_when_no_violation(self, make_article) -> None:
        middleware = NPlusOneGuardMiddleware(_clean_response)
        request = RequestFactory().get("/articles/")

        with override_settings(DEBUG=True, N_PLUS_ONE_GUARD={"MODE": "report"}):
            response = middleware(request)

        assert "X-N-Plus-One-Warnings" not in response

    def test_no_header_when_debug_is_false(self, several_articles) -> None:
        middleware = NPlusOneGuardMiddleware(_n_plus_one_response)
        request = RequestFactory().get("/articles/")

        with override_settings(DEBUG=False, N_PLUS_ONE_GUARD={"MODE": "report", "THRESHOLD": 2}):
            response = middleware(request)

        assert "X-N-Plus-One-Warnings" not in response

    def test_custom_header_name_is_respected(self, several_articles) -> None:
        middleware = NPlusOneGuardMiddleware(_n_plus_one_response)
        request = RequestFactory().get("/articles/")

        with override_settings(
            DEBUG=True,
            N_PLUS_ONE_GUARD={"MODE": "report", "THRESHOLD": 2, "RESPONSE_HEADER": "X-Custom"},
        ):
            response = middleware(request)

        assert "X-Custom" in response
        assert "X-N-Plus-One-Warnings" not in response


class TestNPlusOneGuardMiddlewareRaiseMode:
    def test_propagates_the_exception_in_raise_mode(self, several_articles) -> None:
        middleware = NPlusOneGuardMiddleware(_n_plus_one_response)
        request = RequestFactory().get("/articles/")

        with (
            override_settings(N_PLUS_ONE_GUARD={"MODE": "raise", "THRESHOLD": 2}),
            pytest.raises(NPlusOneDetectedError),
        ):
            middleware(request)

    def test_no_exception_when_query_pattern_is_fine(self, make_article) -> None:
        middleware = NPlusOneGuardMiddleware(_clean_response)
        request = RequestFactory().get("/articles/")

        with override_settings(N_PLUS_ONE_GUARD={"MODE": "raise"}):
            response = middleware(request)

        assert response.status_code == 200
