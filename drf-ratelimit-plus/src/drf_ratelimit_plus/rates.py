"""Parsing the compact ``"<count>/<period>"`` rate string.

Every public entry point (``rate_limit()``, ``@ratelimit()``, the
individual throttle classes) accepts rates in this shorthand — the same
convention DRF's own ``DEFAULT_THROTTLE_RATES`` setting uses, extended
with single-letter period aliases for brevity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from drf_ratelimit_plus.exceptions import InvalidRateError

#: Maps every accepted period spelling to its length in seconds.
_PERIODS: dict[str, int] = {
    "s": 1,
    "sec": 1,
    "second": 1,
    "m": 60,
    "min": 60,
    "minute": 60,
    "h": 3600,
    "hour": 3600,
    "d": 86400,
    "day": 86400,
}

_RATE_PATTERN = re.compile(r"^\s*(\d+)\s*/\s*([A-Za-z]+)\s*$")


@dataclass(frozen=True, slots=True)
class Rate:
    """A parsed rate limit: ``count`` requests per ``period`` seconds.

    Attributes:
        count: The maximum number of requests (or weighted cost units)
            allowed per ``period``.
        period: The window length in seconds.
    """

    count: int
    period: float

    @property
    def per_second(self) -> float:
        """The equivalent steady-state rate, in requests per second.

        Used by the token bucket algorithm as its refill rate.
        """
        return self.count / self.period


def parse_rate(rate: str | Rate) -> Rate:
    """Parse a ``"<count>/<period>"`` string into a :class:`Rate`.

    Args:
        rate: Either an already-parsed :class:`Rate` (returned unchanged),
            or a string like ``"100/m"``, ``"1000/hour"``, ``"10/s"``.
            Accepted period spellings: ``s``/``sec``/``second``,
            ``m``/``min``/``minute``, ``h``/``hour``, ``d``/``day``.

    Returns:
        The parsed :class:`Rate`.

    Raises:
        drf_ratelimit_plus.exceptions.InvalidRateError: If ``rate`` is a
            string that doesn't match the expected shape, or names an
            unrecognized period.

    Example:
        >>> parse_rate("100/m")
        Rate(count=100, period=60.0)
        >>> parse_rate("10/s").per_second
        10.0
    """
    if isinstance(rate, Rate):
        return rate
    match = _RATE_PATTERN.match(rate)
    if not match:
        raise InvalidRateError(
            f"Invalid rate string {rate!r}; expected '<count>/<period>', e.g. '100/m'."
        )
    count_str, period_name = match.groups()
    period_seconds = _PERIODS.get(period_name.lower())
    if period_seconds is None:
        raise InvalidRateError(
            f"Unrecognized period {period_name!r} in rate {rate!r}. "
            f"Valid periods: {sorted(set(_PERIODS))}."
        )
    count = int(count_str)
    if count <= 0:
        raise InvalidRateError(f"Rate count must be positive, got {count} in {rate!r}.")
    return Rate(count=count, period=float(period_seconds))
