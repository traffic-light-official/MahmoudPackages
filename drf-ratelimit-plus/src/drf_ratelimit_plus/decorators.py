"""Per-view rate limiting via a decorator, for function-based views.

For class-based views/viewsets, prefer setting ``throttle_classes``
directly with :func:`~drf_ratelimit_plus.throttles.rate_limit` — that's
more idiomatic DRF and composes with DRF's own throttle lifecycle exactly
as documented. This decorator exists for function-based views (typically
``@api_view``-wrapped), which have no ``throttle_classes`` attribute to
set.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from rest_framework.exceptions import Throttled

from drf_ratelimit_plus.keys import KeyFunc
from drf_ratelimit_plus.settings import get_setting
from drf_ratelimit_plus.throttles import RateSpec, rate_limit
from drf_ratelimit_plus.tiers import TierResolver, default_tier_resolver

_F = TypeVar("_F", bound=Callable[..., Any])


def ratelimit(
    *,
    rate: RateSpec = "60/m",
    algorithm: str = "token_bucket",
    key: str | KeyFunc = "ip",
    cost: int | Callable[[Any], int] = 1,
    burst: int | None = None,
    scope: str | None = None,
    tier_resolver: TierResolver = default_tier_resolver,
    client: Any = None,
) -> Callable[[_F], _F]:
    """Apply rate limiting to a single function-based view.

    Args:
        rate: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.rate`.
        algorithm: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.algorithm`.
        key: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.key`.
        cost: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.cost`.
        burst: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.burst`.
        scope: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.scope`.
        tier_resolver: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.tier_resolver`.
        client: See :attr:`~drf_ratelimit_plus.throttles.RateLimitThrottle.client`.

    Returns:
        A decorator that enforces the configured limit, raising
        :class:`rest_framework.exceptions.Throttled` (which DRF converts
        to ``429`` with a ``Retry-After`` header) when exceeded, and
        adding ``RateLimit-*`` headers to successful responses.

    Example:
        .. code-block:: python

            from rest_framework.decorators import api_view
            from drf_ratelimit_plus import ratelimit


            @api_view(["POST"])
            @ratelimit(rate="10/m", key="user")
            def expensive_action(request):
                ...
    """
    throttle_class = rate_limit(
        rate=rate,
        algorithm=algorithm,
        key=key,
        cost=cost,
        burst=burst,
        scope=scope,
        tier_resolver=tier_resolver,
        client=client,
    )

    def decorator(view_func: _F) -> _F:
        @wraps(view_func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            throttle = throttle_class()
            if not throttle.allow_request(request, None):
                raise Throttled(wait=throttle.wait())
            response = view_func(request, *args, **kwargs)
            result = throttle.last_result
            if result is not None:
                response[get_setting("LIMIT_HEADER")] = str(result.limit)
                response[get_setting("REMAINING_HEADER")] = str(result.remaining)
                response[get_setting("RESET_HEADER")] = str(result.reset_seconds)
            return response

        return wrapper  # type: ignore[return-value]

    return decorator
