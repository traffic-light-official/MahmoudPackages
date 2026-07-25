"""A lightweight, cache-backed rate limiter for outbound notifications.

This is a fixed-window counter meant to prevent runaway over-notification
(e.g. a buggy loop sending the same email 500 times), not a precise
sliding-window limiter for security-sensitive rate limiting - see the
sibling package ``drf-ratelimit-plus`` for that.
"""

from __future__ import annotations

import time
from typing import Final

from django.core.cache import cache

from drf_notification.settings import get_setting

_PERIOD_SECONDS: Final[dict[str, int]] = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}


class InvalidRateLimitError(ValueError):
    """Raised when a configured rate-limit string cannot be parsed."""


def parse_rate(rate: str) -> tuple[int, int]:
    """Parse a ``"count/period"`` string into ``(count, period_seconds)``.

    Args:
        rate: A rate limit string such as ``"50/day"`` or ``"10/hour"``.
            ``period`` must be one of ``second``, ``minute``, ``hour``,
            ``day``.

    Returns:
        The parsed ``(count, period_seconds)`` tuple.

    Raises:
        InvalidRateLimitError: If ``rate`` is not well-formed.
    """
    try:
        count_str, period = rate.split("/")
        count = int(count_str)
    except ValueError as exc:
        raise InvalidRateLimitError(f"Invalid rate limit string: {rate!r}") from exc
    if period not in _PERIOD_SECONDS:
        raise InvalidRateLimitError(
            f"Invalid rate limit period {period!r} in {rate!r}; must be one of "
            f"{sorted(_PERIOD_SECONDS)}."
        )
    if count <= 0:
        raise InvalidRateLimitError(f"Rate limit count must be positive, got {count} in {rate!r}.")
    return count, _PERIOD_SECONDS[period]


def is_rate_limited(user_id: int, channel: str) -> bool:
    """Return whether ``user_id`` has exceeded the configured rate limit for ``channel``.

    Args:
        user_id: Primary key of the recipient.
        channel: The delivery channel being checked.

    Returns:
        ``True`` if the limit configured in the ``RATE_LIMITS`` setting
        for ``channel`` has been reached or exceeded for the current
        window (and the attempt should be suppressed), ``False`` if the
        channel has no configured limit or the limit has not been
        reached.
    """
    rate_limits: dict[str, str | None] = get_setting("RATE_LIMITS")
    rate = rate_limits.get(channel)
    if not rate:
        return False

    count, period_seconds = parse_rate(rate)
    window = int(time.time() // period_seconds)
    cache_key = f"drf_notification:ratelimit:{channel}:{user_id}:{window}"

    cache.add(cache_key, 0, timeout=period_seconds)
    try:
        current = cache.incr(cache_key)
    except ValueError:
        # The key expired between add() and incr() in a race at a window
        # boundary; treat this attempt as the first one in a fresh window.
        cache.set(cache_key, 1, timeout=period_seconds)
        current = 1

    return current > count
