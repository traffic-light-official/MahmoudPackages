"""Plan-tier rate limits: different limits for different subscription tiers.

Pass a mapping of tier name to rate (instead of a single rate string) to
``rate_limit()``/``@ratelimit()``, along with a ``tier_resolver`` callable
that inspects the request and returns which tier applies.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from drf_ratelimit_plus.exceptions import UnknownTierError
from drf_ratelimit_plus.rates import Rate, parse_rate
from drf_ratelimit_plus.settings import get_setting

TierResolver = Callable[[Any], str]


def default_tier_resolver(request: Any) -> str:
    """The built-in tier resolver: reads ``request.user.plan``.

    Args:
        request: The incoming request.

    Returns:
        The value of ``request.user.plan`` if the request has an
        authenticated user with a ``plan`` attribute, otherwise the
        ``DEFAULT_TIER`` setting.

    Example:
        Attach a ``plan`` attribute (a string) to your user model, or
        override this entirely by passing your own ``tier_resolver``
        callable — e.g. one that reads a related ``Subscription`` model.
    """
    user = getattr(request, "user", None)
    plan = getattr(user, "plan", None) if user is not None else None
    return str(plan) if plan else str(get_setting("DEFAULT_TIER"))


def resolve_tier_rate(
    request: Any,
    tiers: Mapping[str, str | Rate],
    *,
    resolver: TierResolver = default_tier_resolver,
) -> Rate:
    """Resolve which :class:`~drf_ratelimit_plus.rates.Rate` applies to a request.

    Args:
        request: The incoming request.
        tiers: A mapping of tier name to rate string (or already-parsed
            :class:`~drf_ratelimit_plus.rates.Rate`), e.g.
            ``{"free": "10/m", "pro": "100/m", "enterprise": "1000/m"}``.
        resolver: Determines which tier name applies to ``request``.
            Defaults to :func:`default_tier_resolver`.

    Returns:
        The resolved :class:`~drf_ratelimit_plus.rates.Rate`.

    Raises:
        drf_ratelimit_plus.exceptions.UnknownTierError: If the resolved
            tier name has no entry in ``tiers`` and ``tiers`` also has no
            entry for the ``DEFAULT_TIER`` setting to fall back to.
    """
    tier_name = resolver(request)
    rate = tiers.get(tier_name)
    if rate is None:
        default_tier = get_setting("DEFAULT_TIER")
        rate = tiers.get(default_tier)
        if rate is None:
            raise UnknownTierError(
                f"No rate configured for tier {tier_name!r}, and no fallback "
                f"entry for the default tier {default_tier!r}. Configured "
                f"tiers: {sorted(tiers)}."
            )
    return parse_rate(rate)
