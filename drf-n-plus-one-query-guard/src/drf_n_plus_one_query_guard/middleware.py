"""Django middleware: guards every request for suspected N+1 queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings as django_settings

from drf_n_plus_one_query_guard.guard import NPlusOneGuard
from drf_n_plus_one_query_guard.settings import get_setting

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


class NPlusOneGuardMiddleware:
    """Wraps every request in an :class:`~drf_n_plus_one_query_guard.guard.NPlusOneGuard`.

    With ``MODE="raise"`` (see the ``N_PLUS_ONE_GUARD`` setting), a
    suspected N+1 becomes an
    :class:`~drf_n_plus_one_query_guard.exceptions.NPlusOneDetectedError`
    propagating out of this middleware like any other unhandled
    exception - typically a 500 response, via Django's normal exception
    handling. Only enable ``MODE="raise"`` for this middleware in
    development/CI/staging, never production - see
    ``docs/security.md``.

    With ``MODE="warn"``/``MODE="report"``, the request completes
    normally; when ``settings.DEBUG`` is ``True``, a summary of any
    violations is added to the response via the ``RESPONSE_HEADER``
    setting (never added when ``DEBUG`` is ``False``, regardless of
    ``MODE``).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        with NPlusOneGuard() as guard:
            response = self.get_response(request)

        if django_settings.DEBUG and guard.violations:
            header_name = get_setting("RESPONSE_HEADER")
            response[header_name] = "; ".join(
                f"{violation.count}x {violation.fingerprint} (at {violation.call_site})"
                for violation in guard.violations
            )
        return response
