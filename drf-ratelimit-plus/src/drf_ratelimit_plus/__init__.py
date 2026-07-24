"""Advanced rate limiting for Django REST Framework.

The public API is intentionally small:

* :func:`~drf_ratelimit_plus.throttles.rate_limit` — build a configured
  throttle class for a view's ``throttle_classes``.
* :func:`~drf_ratelimit_plus.decorators.ratelimit` — the same, as a
  decorator for function-based views.
* :class:`~drf_ratelimit_plus.mixins.RateLimitHeadersMixin` — add
  ``RateLimit-*`` response headers to class-based views.
* :mod:`drf_ratelimit_plus.keys` — built-in and composable key functions.

See ``docs/quickstart.md`` for a complete end-to-end example.
"""

from __future__ import annotations

from drf_ratelimit_plus.decorators import ratelimit
from drf_ratelimit_plus.exceptions import (
    InvalidAlgorithmError,
    InvalidKeyError,
    InvalidRateError,
    RateLimitPlusError,
    UnknownTierError,
)
from drf_ratelimit_plus.keys import by_api_key, by_ip, by_tenant, by_user, by_view, combine
from drf_ratelimit_plus.mixins import RateLimitHeadersMixin
from drf_ratelimit_plus.rates import Rate, parse_rate
from drf_ratelimit_plus.results import LimitResult
from drf_ratelimit_plus.throttles import RateLimitThrottle, rate_limit
from drf_ratelimit_plus.tiers import default_tier_resolver, resolve_tier_rate

__version__ = "1.0.0"

__all__ = [
    "InvalidAlgorithmError",
    "InvalidKeyError",
    "InvalidRateError",
    "LimitResult",
    "Rate",
    "RateLimitHeadersMixin",
    "RateLimitPlusError",
    "RateLimitThrottle",
    "UnknownTierError",
    "__version__",
    "by_api_key",
    "by_ip",
    "by_tenant",
    "by_user",
    "by_view",
    "combine",
    "default_tier_resolver",
    "parse_rate",
    "rate_limit",
    "ratelimit",
    "resolve_tier_rate",
]
