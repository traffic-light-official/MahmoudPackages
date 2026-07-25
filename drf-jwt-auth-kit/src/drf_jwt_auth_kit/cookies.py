"""Refresh and CSRF cookie helpers."""

from __future__ import annotations

import secrets

from django.http import HttpResponse

from drf_jwt_auth_kit.settings import get_setting


def set_refresh_cookie(response: HttpResponse, refresh_token: str) -> None:
    """Attach the refresh token as an httpOnly cookie to ``response``.

    Args:
        response: The response to attach the cookie to.
        refresh_token: The raw JWT refresh token.
    """
    response.set_cookie(
        get_setting("REFRESH_COOKIE_NAME"),
        refresh_token,
        httponly=True,
        secure=get_setting("REFRESH_COOKIE_SECURE"),
        samesite=get_setting("REFRESH_COOKIE_SAMESITE"),
        domain=get_setting("REFRESH_COOKIE_DOMAIN"),
        path=get_setting("REFRESH_COOKIE_PATH"),
    )


def clear_refresh_cookie(response: HttpResponse) -> None:
    """Remove the refresh cookie from the client (used on logout).

    Args:
        response: The response to remove the cookie from.
    """
    response.delete_cookie(
        get_setting("REFRESH_COOKIE_NAME"),
        domain=get_setting("REFRESH_COOKIE_DOMAIN"),
        path=get_setting("REFRESH_COOKIE_PATH"),
        samesite=get_setting("REFRESH_COOKIE_SAMESITE"),
    )


def set_csrf_cookie(response: HttpResponse) -> str:
    """Set a fresh double-submit CSRF cookie and return its value.

    The cookie is deliberately **not** httpOnly - the whole point of the
    double-submit pattern is that JavaScript reads this cookie and
    echoes its value back in a request header, proving the request
    originated from a page that can read same-site cookies (which a
    cross-site attacker's page cannot) - see :mod:`drf_jwt_auth_kit.csrf`.

    Args:
        response: The response to attach the cookie to.

    Returns:
        The generated CSRF token value, in case the caller also wants to
        return it in the response body.
    """
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        get_setting("CSRF_COOKIE_NAME"),
        csrf_token,
        httponly=False,
        secure=get_setting("REFRESH_COOKIE_SECURE"),
        samesite=get_setting("REFRESH_COOKIE_SAMESITE"),
        domain=get_setting("REFRESH_COOKIE_DOMAIN"),
        path=get_setting("REFRESH_COOKIE_PATH"),
    )
    return csrf_token


def clear_csrf_cookie(response: HttpResponse) -> None:
    """Remove the CSRF cookie from the client (used on logout).

    Args:
        response: The response to remove the cookie from.
    """
    response.delete_cookie(
        get_setting("CSRF_COOKIE_NAME"),
        domain=get_setting("REFRESH_COOKIE_DOMAIN"),
        path=get_setting("REFRESH_COOKIE_PATH"),
        samesite=get_setting("REFRESH_COOKIE_SAMESITE"),
    )
