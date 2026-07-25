"""Tests for :mod:`drf_jwt_auth_kit.cookies`."""

from __future__ import annotations

from django.http import HttpResponse
from django.test import override_settings

from drf_jwt_auth_kit.cookies import (
    clear_csrf_cookie,
    clear_refresh_cookie,
    set_csrf_cookie,
    set_refresh_cookie,
)


class TestSetRefreshCookie:
    def test_sets_httponly_secure_cookie(self) -> None:
        response = HttpResponse()

        set_refresh_cookie(response, "the-refresh-token")

        cookie = response.cookies["refresh_token"]
        assert cookie.value == "the-refresh-token"
        assert cookie["httponly"] is True
        assert cookie["samesite"] == "Lax"

    def test_uses_configured_cookie_name(self) -> None:
        with override_settings(JWT_AUTH_KIT={"REFRESH_COOKIE_NAME": "my_refresh"}):
            response = HttpResponse()
            set_refresh_cookie(response, "token")

        assert "my_refresh" in response.cookies


class TestClearRefreshCookie:
    def test_expires_the_cookie(self) -> None:
        response = HttpResponse()

        clear_refresh_cookie(response)

        cookie = response.cookies["refresh_token"]
        assert cookie["max-age"] == 0


class TestSetCsrfCookie:
    def test_sets_a_non_httponly_cookie_and_returns_its_value(self) -> None:
        response = HttpResponse()

        token = set_csrf_cookie(response)

        cookie = response.cookies["refresh_csrftoken"]
        assert cookie.value == token
        assert cookie["httponly"] == ""

    def test_generates_a_new_value_each_call(self) -> None:
        response = HttpResponse()

        first = set_csrf_cookie(response)
        second = set_csrf_cookie(response)

        assert first != second


class TestClearCsrfCookie:
    def test_expires_the_cookie(self) -> None:
        response = HttpResponse()

        clear_csrf_cookie(response)

        cookie = response.cookies["refresh_csrftoken"]
        assert cookie["max-age"] == 0
