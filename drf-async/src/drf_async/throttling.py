"""Async-native throttle support.

Existing DRF ``BaseThrottle`` subclasses keep working unchanged with
:class:`~drf_async.views.AsyncAPIView` - their ``allow_request`` is
bridged via :func:`drf_async.compat.call_maybe_async`.
:class:`AsyncSimpleRateThrottle` is a genuinely async re-implementation
of DRF's own ``SimpleRateThrottle`` (same cache key format, same rate
parsing, same sliding-window algorithm) using Django's async cache API
(``cache.aget``/``cache.aset``, stable since Django 4.2) instead of
bridging the sync cache through a thread - there's no serialization or
database work involved in a cache read/write, so there's no reason to
pay for a thread hop here the way permission/serializer checks
sometimes must.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from django.core.cache import cache as default_cache
from django.core.exceptions import ImproperlyConfigured
from rest_framework.settings import api_settings
from rest_framework.throttling import BaseThrottle

from drf_async.compat import call_maybe_async

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class BaseAsyncThrottle(BaseThrottle):
    """Base class for a throttle whose checks are naturally async."""

    async def allow_request(self, request: Request, view: APIView) -> bool:  # type: ignore[override]
        """Return whether the request should be allowed. Must be overridden."""
        raise NotImplementedError(".allow_request() must be overridden")

    async def wait(self) -> float | None:  # type: ignore[override]
        """Return a recommended number of seconds to wait, or ``None``."""
        return None


class AsyncSimpleRateThrottle(BaseAsyncThrottle):
    """An async re-implementation of :class:`rest_framework.throttling.SimpleRateThrottle`.

    Subclass and override :meth:`get_cache_key` the same way you would
    for the sync version - the rate string format (``"<num>/<period>"``),
    ``scope``/``THROTTLE_RATES`` lookup, and cache key format
    (``cache_format``) are all unchanged.
    """

    cache = default_cache
    timer = staticmethod(time.time)
    cache_format = "throttle_%(scope)s_%(ident)s"
    scope: str | None = None
    # djangorestframework-stubs types this as dict[str, float | int | None],
    # but every real value is a rate string like "5/min" - annotate with the
    # type this class actually uses.
    THROTTLE_RATES: dict[str, str | None] = api_settings.DEFAULT_THROTTLE_RATES  # type: ignore[assignment]

    def __init__(self) -> None:
        if not getattr(self, "rate", None):
            self.rate = self.get_rate()
        num_requests, duration = self.parse_rate(self.rate)
        # Only ever read when self.rate is not None (both allow_request() and
        # wait() return/short-circuit before touching these otherwise), at
        # which point parse_rate() always returns a pair of real ints - see
        # its own body - so 0 here is a placeholder that's never actually used.
        self.num_requests: int = num_requests if num_requests is not None else 0
        self.duration: int = duration if duration is not None else 0
        self.key: str | None = None
        self.history: list[float] = []
        self.now: float = 0.0

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        """Return a unique cache key for this request, or ``None`` to skip throttling."""
        raise NotImplementedError(".get_cache_key() must be overridden")

    def get_rate(self) -> str | None:
        """Look up this throttle's rate string from ``THROTTLE_RATES`` via ``scope``."""
        if not self.scope:
            raise ImproperlyConfigured(
                f"You must set either `.scope` or `.rate` for '{self.__class__.__name__}' throttle"
            )
        try:
            return self.THROTTLE_RATES[self.scope]
        except KeyError:
            raise ImproperlyConfigured(
                f"No default throttle rate set for '{self.scope}' scope"
            ) from None

    def parse_rate(self, rate: str | None) -> tuple[int | None, int | None]:
        """Parse a ``"<num>/<period>"`` rate string into ``(num_requests, duration_seconds)``."""
        if rate is None:
            return (None, None)
        num, period = rate.split("/")
        num_requests = int(num)
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period[0]]
        return (num_requests, duration)

    async def allow_request(self, request: Request, view: APIView) -> bool:  # type: ignore[override]
        """Check (and record, on success) this request against the sliding window."""
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = await self.cache.aget(self.key, [])
        self.now = self.timer()

        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return await self._throttle_failure()
        return await self._throttle_success()

    async def _throttle_success(self) -> bool:
        self.history.insert(0, self.now)
        await self.cache.aset(self.key, self.history, self.duration)
        return True

    async def _throttle_failure(self) -> bool:
        return False

    async def wait(self) -> float | None:  # type: ignore[override]
        """Return the recommended number of seconds until the next allowed request."""
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1
        if available_requests <= 0:
            return None
        return remaining_duration / float(available_requests)


class AsyncAnonRateThrottle(AsyncSimpleRateThrottle):
    """Throttles unauthenticated requests only, keyed by client IP."""

    scope = "anon"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        """Return ``None`` (never throttle) for an authenticated user."""
        if request.user and request.user.is_authenticated:
            return None
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class AsyncUserRateThrottle(AsyncSimpleRateThrottle):
    """Throttles per authenticated user (falling back to client IP if anonymous)."""

    scope = "user"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        """Key by user pk if authenticated, else by client IP."""
        ident: Any = (
            request.user.pk
            if request.user and request.user.is_authenticated
            else self.get_ident(request)
        )
        return self.cache_format % {"scope": self.scope, "ident": ident}


async def check_throttle(throttle: BaseThrottle, request: Request, view: APIView) -> bool:
    """Check one throttle instance, bridging sync and async transparently."""
    return bool(await call_maybe_async(throttle.allow_request, request, view))


async def wait_for_throttle(throttle: BaseThrottle) -> float | None:
    """Get one throttle's recommended wait time, bridging sync and async transparently."""
    result = await call_maybe_async(throttle.wait)
    return float(result) if result is not None else None
