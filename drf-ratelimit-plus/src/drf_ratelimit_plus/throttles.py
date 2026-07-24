"""DRF throttle classes built on this package's algorithms.

``rate_limit()`` is the main entry point: it returns a
:class:`RateLimitThrottle` subclass configured with your chosen
algorithm, rate, key function, and cost — ready to drop into a view's
``throttle_classes``. Building on DRF's own
:class:`~rest_framework.throttling.BaseThrottle` means the standard
throttle lifecycle (``check_throttles()``, the ``Throttled`` exception,
automatic ``Retry-After`` header) all work exactly as DRF users already
expect — nothing about request dispatch is reimplemented.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from rest_framework.throttling import BaseThrottle

from drf_ratelimit_plus.algorithms import (
    fixed_window_check,
    sliding_window_check,
    token_bucket_check,
)
from drf_ratelimit_plus.client import get_redis_client
from drf_ratelimit_plus.exceptions import InvalidAlgorithmError
from drf_ratelimit_plus.keys import KeyFunc, by_view, resolve_key_func
from drf_ratelimit_plus.rates import Rate, parse_rate
from drf_ratelimit_plus.results import LimitResult
from drf_ratelimit_plus.settings import get_setting
from drf_ratelimit_plus.tiers import TierResolver, default_tier_resolver, resolve_tier_rate

RateSpec = str | Rate | Mapping[str, "str | Rate"] | Callable[[Any], "str | Rate"]

_ALGORITHM_NAMES = ("fixed_window", "sliding_window", "token_bucket")


class RateLimitThrottle(BaseThrottle):
    """A configurable rate-limiting throttle.

    Don't instantiate or subclass this directly for one-off configuration
    — use :func:`rate_limit` instead, which builds a properly configured
    subclass. Subclass this directly only if you want a *reusable* named
    throttle class (the same pattern DRF's own ``UserRateThrottle`` uses).

    Attributes:
        algorithm: One of ``"fixed_window"``, ``"sliding_window"``,
            ``"token_bucket"``.
        rate: A rate string (``"100/m"``), an already-parsed
            :class:`~drf_ratelimit_plus.rates.Rate`, a mapping of tier
            name to rate (for plan-tier support), or a callable taking
            the request and returning any of the above (for fully
            dynamic, e.g. database-driven, configuration).
        key: A built-in key function name (``"ip"``, ``"user"``,
            ``"api_key"``, ``"tenant"``, ``"view"``) or a custom
            callable. See :mod:`drf_ratelimit_plus.keys`.
        cost: How many units a single request consumes — an int, or a
            callable taking the request and returning one, for
            per-request weighted costs.
        burst: Token-bucket capacity (ignored by the other algorithms).
            Defaults to the rate's count when ``None``.
        scope: An explicit scope string grouping requests into the same
            limit regardless of which view handles them. Defaults to the
            handling view's dotted class path (i.e. each view gets an
            independent limit by default).
        tier_resolver: Determines which tier name applies when ``rate``
            is a mapping. Defaults to
            :func:`~drf_ratelimit_plus.tiers.default_tier_resolver`.
        client: An explicit Redis client to use instead of the one
            resolved from settings (see
            :func:`~drf_ratelimit_plus.client.get_redis_client`).

    Note:
        If you subclass this directly (rather than using
        :func:`rate_limit`) and want ``rate``, ``key``, or ``cost`` to be
        a plain function rather than a string/int, wrap it in
        ``staticmethod(...)`` explicitly — otherwise Python's normal
        attribute lookup binds it as an instance method (implicitly
        passing ``self`` as the first argument), which isn't what these
        callables expect. :func:`rate_limit` handles this wrapping for
        you automatically.
    """

    algorithm: str = "token_bucket"
    rate: RateSpec = "60/m"
    key: str | KeyFunc = "ip"
    cost: int | Callable[[Any], int] = 1
    burst: int | None = None
    scope: str | None = None
    tier_resolver: TierResolver = staticmethod(default_tier_resolver)
    client: Any = None

    def __init__(self) -> None:
        self.last_result: LimitResult | None = None

    def allow_request(self, request: Any, view: Any) -> bool:
        """See :meth:`rest_framework.throttling.BaseThrottle.allow_request`.

        Args:
            request: The incoming request.
            view: The view handling it.

        Returns:
            Whether the request is within its configured limit. The full
            :class:`~drf_ratelimit_plus.results.LimitResult` is stored on
            ``self.last_result`` regardless, for header construction by
            :class:`~drf_ratelimit_plus.mixins.RateLimitHeadersMixin`.
        """
        rate = self._resolve_rate(request)
        cost = self.cost(request) if callable(self.cost) else self.cost
        client = self.client if self.client is not None else get_redis_client()
        key = self._build_key(request, view)

        if self.algorithm == "token_bucket":
            result = token_bucket_check(client, key, rate, cost=cost, burst=self.burst)
        elif self.algorithm == "sliding_window":
            result = sliding_window_check(client, key, rate, cost=cost)
        elif self.algorithm == "fixed_window":
            result = fixed_window_check(client, key, rate, cost=cost)
        else:
            raise InvalidAlgorithmError(
                f"Unknown algorithm {self.algorithm!r}. Valid options: {_ALGORITHM_NAMES}."
            )

        self.last_result = result
        return result.allowed

    def wait(self) -> float | None:
        """See :meth:`rest_framework.throttling.BaseThrottle.wait`.

        Returns:
            Seconds the client should wait before retrying, or ``None``
            if the last check succeeded (or hasn't run yet).
        """
        if self.last_result is None:
            return None
        return self.last_result.retry_after

    def _build_key(self, request: Any, view: Any) -> str:
        key_func = resolve_key_func(self.key)
        scope = self.scope if self.scope is not None else by_view(request, view)
        identity = key_func(request, view)
        prefix = get_setting("KEY_PREFIX")
        return f"{prefix}{self.algorithm}:{scope}:{identity}"

    def _resolve_rate(self, request: Any) -> Rate:
        rate = self.rate
        if callable(rate):
            rate = rate(request)
        if isinstance(rate, Mapping):
            return resolve_tier_rate(request, rate, resolver=self.tier_resolver)
        return parse_rate(rate)


def rate_limit(
    *,
    rate: RateSpec = "60/m",
    algorithm: str = "token_bucket",
    key: str | KeyFunc = "ip",
    cost: int | Callable[[Any], int] = 1,
    burst: int | None = None,
    scope: str | None = None,
    tier_resolver: TierResolver = default_tier_resolver,
    client: Any = None,
) -> type[RateLimitThrottle]:
    """Build a :class:`RateLimitThrottle` subclass for ``throttle_classes``.

    Args:
        rate: See :attr:`RateLimitThrottle.rate`.
        algorithm: One of ``"fixed_window"``, ``"sliding_window"``,
            ``"token_bucket"`` (default).
        key: See :attr:`RateLimitThrottle.key`.
        cost: See :attr:`RateLimitThrottle.cost`.
        burst: See :attr:`RateLimitThrottle.burst`.
        scope: See :attr:`RateLimitThrottle.scope`.
        tier_resolver: See :attr:`RateLimitThrottle.tier_resolver`.
        client: See :attr:`RateLimitThrottle.client`.

    Returns:
        A new :class:`RateLimitThrottle` subclass, ready to use in
        ``throttle_classes = [rate_limit(...)]``.

    Raises:
        drf_ratelimit_plus.exceptions.InvalidAlgorithmError: If
            ``algorithm`` isn't recognized.

    Example:
        .. code-block:: python

            class ArticleViewSet(viewsets.ModelViewSet):
                throttle_classes = [
                    rate_limit(rate="100/m", algorithm="token_bucket", burst=20, key="user"),
                ]
    """
    if algorithm not in _ALGORITHM_NAMES:
        raise InvalidAlgorithmError(
            f"Unknown algorithm {algorithm!r}. Valid options: {_ALGORITHM_NAMES}."
        )
    return type(
        "ConfiguredRateLimitThrottle",
        (RateLimitThrottle,),
        {
            "algorithm": algorithm,
            "rate": staticmethod(rate) if callable(rate) else rate,
            "key": staticmethod(key) if callable(key) else key,
            "cost": staticmethod(cost) if callable(cost) else cost,
            "burst": burst,
            "scope": scope,
            "tier_resolver": staticmethod(tier_resolver),
            "client": client,
        },
    )
