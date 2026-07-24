"""Custom exceptions raised by :mod:`drf_ratelimit_plus`.

Rate-limit *enforcement* (denying a request that exceeds its limit) uses
DRF's own :class:`rest_framework.exceptions.Throttled` exception directly
— see ``docs/architecture.md`` for why that's the right choice rather
than defining a parallel exception type. The exceptions in this module
are exclusively for *configuration* mistakes, raised at setup time.
"""

from __future__ import annotations


class RateLimitPlusError(Exception):
    """Base class for all configuration errors raised by this package."""


class InvalidRateError(RateLimitPlusError, ValueError):
    """Raised when a rate string cannot be parsed.

    See :func:`drf_ratelimit_plus.rates.parse_rate`.
    """


class InvalidKeyError(RateLimitPlusError, ValueError):
    """Raised when a ``key`` argument names an unknown built-in key function.

    See :func:`drf_ratelimit_plus.keys.resolve_key_func`.
    """


class InvalidAlgorithmError(RateLimitPlusError, ValueError):
    """Raised when an ``algorithm`` argument names an unknown algorithm.

    See :func:`drf_ratelimit_plus.throttles.rate_limit`.
    """


class UnknownTierError(RateLimitPlusError, ValueError):
    """Raised when a resolved plan-tier name has no matching entry.

    See :mod:`drf_ratelimit_plus.tiers`.
    """
