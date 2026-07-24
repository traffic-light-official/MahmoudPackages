"""Adding ``RateLimit-*`` response headers alongside DRF's throttle lifecycle.

DRF's own throttle machinery already adds ``Retry-After`` on a `429`
response (since :class:`~drf_ratelimit_plus.throttles.RateLimitThrottle`
reports its wait time via ``wait()``, exactly like any other DRF
throttle). This mixin adds the informational headers —
``RateLimit-Limit``, ``RateLimit-Remaining``, ``RateLimit-Reset`` — to
*every* response the throttle was checked against, success or failure, so
clients can see how close they are to their limit even when a request
succeeds.
"""

from __future__ import annotations

from typing import Any

from drf_ratelimit_plus.settings import get_setting
from drf_ratelimit_plus.throttles import RateLimitThrottle


class RateLimitHeadersMixin:
    """Adds ``RateLimit-*`` headers to every response, based on the
    :class:`~drf_ratelimit_plus.throttles.RateLimitThrottle` instances
    checked for the current request.

    Mix into any ``APIView``/``GenericAPIView``/viewset that uses
    :func:`~drf_ratelimit_plus.throttles.rate_limit` in its
    ``throttle_classes``:

    .. code-block:: python

        class ArticleViewSet(RateLimitHeadersMixin, viewsets.ModelViewSet):
            throttle_classes = [rate_limit(rate="100/m")]

    Must come before the DRF base class in the MRO, same as any other
    DRF mixin.
    """

    def get_throttles(self) -> list[Any]:
        """Return (and cache) this request's throttle instances.

        DRF's own ``get_throttles()`` constructs a fresh instance from
        ``throttle_classes`` on every call — calling it more than once
        per request would mean ``check_throttles()`` and
        ``finalize_response()`` each see *different* throttle instances,
        so the ``last_result`` this mixin reads for headers would never
        match what actually decided the request's outcome. Caching on
        ``self`` fixes this: a view instance handles exactly one request
        in DRF, so caching per-instance is exactly "per request".

        Returns:
            The same list of throttle instances for every call during
            this request.
        """
        if not hasattr(self, "_ratelimit_plus_throttles"):
            self._ratelimit_plus_throttles = super().get_throttles()  # type: ignore[misc]
        throttles: list[Any] = self._ratelimit_plus_throttles
        return throttles

    def finalize_response(self, request: Any, response: Any, *args: Any, **kwargs: Any) -> Any:
        """Add ``RateLimit-*`` headers before returning the response.

        Args:
            request: The current request.
            response: The response produced by the view (or by DRF's
                exception handling, for a throttled request).
            *args: Passed through to the next class in the MRO.
            **kwargs: Passed through to the next class in the MRO.

        Returns:
            The response, with ``RateLimit-Limit``, ``RateLimit-Remaining``,
            and ``RateLimit-Reset`` headers added if any configured
            :class:`~drf_ratelimit_plus.throttles.RateLimitThrottle`
            produced a result for this request. If multiple such
            throttles were checked, the one with the *lowest* remaining
            count is reported (the one closest to being exceeded is the
            most informative to the client).
        """
        response = super().finalize_response(request, response, *args, **kwargs)  # type: ignore[misc]
        results = [
            t.last_result
            for t in self.get_throttles()
            if isinstance(t, RateLimitThrottle) and t.last_result is not None
        ]
        if not results:
            return response
        tightest = min(results, key=lambda r: r.remaining)
        response[get_setting("LIMIT_HEADER")] = str(tightest.limit)
        response[get_setting("REMAINING_HEADER")] = str(tightest.remaining)
        response[get_setting("RESET_HEADER")] = str(tightest.reset_seconds)
        return response
