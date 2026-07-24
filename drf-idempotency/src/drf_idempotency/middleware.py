"""Project-wide idempotency handling via Django middleware.

Add ``"drf_idempotency.middleware.IdempotencyMiddleware"`` to
``MIDDLEWARE`` to apply idempotency-key handling to every request using a
method listed in the ``METHODS`` setting, across your entire project,
without touching individual views.
"""

from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from drf_idempotency.core import applies_to, build_error_response, process_idempotent_request
from drf_idempotency.exceptions import IdempotencyError


class IdempotencyMiddleware:
    """Applies idempotency-key handling to every matching request.

    Args:
        get_response: The next middleware/view in the chain, provided by
            Django's middleware machinery.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process one request.

        Args:
            request: The incoming request.

        Returns:
            The response — either freshly produced or replayed from a
            prior identical request. Requests whose method isn't in the
            configured ``METHODS`` setting pass through untouched.
            Idempotency-specific errors (invalid/missing key, key reuse,
            a concurrent request in progress) are returned as a JSON
            error response with the appropriate status code, rather than
            propagating as raw exceptions — plain Django middleware has
            no equivalent of DRF's own exception handling to do this
            automatically.
        """
        if not applies_to(request):
            return self.get_response(request)
        try:
            return process_idempotent_request(request, lambda: self.get_response(request))
        except IdempotencyError as exc:
            return build_error_response(exc)
