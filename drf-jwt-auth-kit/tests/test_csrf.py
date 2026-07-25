"""Tests for :mod:`drf_jwt_auth_kit.csrf`."""

from __future__ import annotations

import pytest
from rest_framework.test import APIRequestFactory

from drf_jwt_auth_kit.csrf import validate_csrf
from drf_jwt_auth_kit.exceptions import InvalidCSRFTokenError


class TestValidateCsrf:
    def test_passes_when_cookie_and_header_match(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.post(
            "/auth/refresh/",
            HTTP_X_REFRESH_CSRFTOKEN="matching-value",
            HTTP_COOKIE="refresh_csrftoken=matching-value",
        )

        validate_csrf(request)  # does not raise

    def test_raises_when_header_is_missing(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.post("/auth/refresh/", HTTP_COOKIE="refresh_csrftoken=matching-value")

        with pytest.raises(InvalidCSRFTokenError):
            validate_csrf(request)

    def test_raises_when_cookie_is_missing(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.post("/auth/refresh/", HTTP_X_REFRESH_CSRFTOKEN="some-value")

        with pytest.raises(InvalidCSRFTokenError):
            validate_csrf(request)

    def test_raises_when_values_differ(self, api_rf: APIRequestFactory) -> None:
        request = api_rf.post(
            "/auth/refresh/",
            HTTP_X_REFRESH_CSRFTOKEN="header-value",
            HTTP_COOKIE="refresh_csrftoken=cookie-value",
        )

        with pytest.raises(InvalidCSRFTokenError):
            validate_csrf(request)
