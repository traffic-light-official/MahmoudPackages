"""Double-submit-cookie CSRF protection for refresh/logout endpoints.

The refresh token lives in an httpOnly cookie, which the browser sends
automatically on any request to the right host/path - including one
triggered by a malicious third-party page (a classic CSRF setup). Since
JavaScript cannot read an httpOnly cookie, a legitimate same-origin page
can still prove a request is not forged by reading a second, non-httpOnly
cookie (:func:`~drf_jwt_auth_kit.cookies.set_csrf_cookie`) and echoing its
value back in a request header; a cross-site attacker's page cannot read
that cookie to forge the header (same-origin policy), even though the
browser still attaches the httpOnly refresh cookie automatically.
"""

from __future__ import annotations

import hmac
from typing import TYPE_CHECKING

from drf_jwt_auth_kit.exceptions import InvalidCSRFTokenError
from drf_jwt_auth_kit.settings import get_setting

if TYPE_CHECKING:
    from django.http import HttpRequest


def validate_csrf(request: HttpRequest) -> None:
    """Raise :class:`InvalidCSRFTokenError` unless the CSRF cookie and header match.

    Args:
        request: The current request.

    Raises:
        InvalidCSRFTokenError: If the CSRF cookie is missing, the header
            is missing, or their values do not match.
    """
    cookie_value = request.COOKIES.get(get_setting("CSRF_COOKIE_NAME"))
    header_name = _meta_header_name(get_setting("CSRF_HEADER_NAME"))
    header_value = request.META.get(header_name)

    if not cookie_value or not header_value:
        raise InvalidCSRFTokenError("Missing CSRF cookie or header.")
    if not hmac.compare_digest(cookie_value, header_value):
        raise InvalidCSRFTokenError("CSRF cookie and header do not match.")


def _meta_header_name(header_name: str) -> str:
    return "HTTP_" + header_name.upper().replace("-", "_")
