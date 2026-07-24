"""Per-view idempotency handling via a decorator.

Use :func:`idempotent` when you want idempotency-key handling on specific
views only, rather than project-wide via
:class:`drf_idempotency.middleware.IdempotencyMiddleware`. Works on
function-based views (``@api_view`` or plain Django views) and on
class-based view *methods* (e.g. ``APIView.post``) alike.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any, TypeVar

from django.http import HttpRequest, HttpResponse

from drf_idempotency.core import applies_to, process_idempotent_request

_F = TypeVar("_F", bound=Callable[..., HttpResponse])


def idempotent(*, methods: Sequence[str] | None = None) -> Callable[[_F], _F]:
    """Apply idempotency-key handling to a single view function or method.

    Args:
        methods: HTTP methods this decorator applies to. Requests using
            any other method pass through untouched. Defaults to the
            ``METHODS`` setting (``["POST", "PUT", "PATCH"]`` by default).

    Returns:
        A decorator that wraps the view, applying the same
        acquire-or-replay logic as
        :class:`~drf_idempotency.middleware.IdempotencyMiddleware`.

    Example:
        .. code-block:: python

            from rest_framework.decorators import api_view
            from drf_idempotency import idempotent


            @api_view(["POST"])
            @idempotent()
            def create_payment(request):
                ...


            class PaymentViewSet(viewsets.ViewSet):
                @idempotent()
                def create(self, request):
                    ...
    """

    def decorator(func: _F) -> _F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> HttpResponse:
            request = _find_request(args)
            allowed_methods = {m.upper() for m in methods} if methods is not None else None
            if allowed_methods is not None and request.method not in allowed_methods:
                return func(*args, **kwargs)
            if allowed_methods is None and not applies_to(request):
                return func(*args, **kwargs)
            return process_idempotent_request(request, lambda: func(*args, **kwargs))

        return wrapper  # type: ignore[return-value]

    return decorator


def _find_request(args: tuple[Any, ...]) -> HttpRequest:
    """Locate the request object among the first two positional arguments.

    Handles both function-based views (``func(request, ...)``) and
    class-based view methods (``method(self, request, ...)``) without
    needing to know which shape the wrapped callable uses.

    Args:
        args: The positional arguments the wrapped callable was called
            with.

    Returns:
        The located request object.

    Raises:
        TypeError: If neither of the first two positional arguments looks
            like a request (has both ``.method`` and ``.headers``).
    """
    for arg in args[:2]:
        if hasattr(arg, "method") and hasattr(arg, "headers"):
            return arg  # type: ignore[no-any-return]
    raise TypeError(
        "@idempotent could not locate the request argument in the first two "
        "positional arguments. It must decorate a function-based view "
        "(request, ...) or a class-based view method (self, request, ...)."
    )
