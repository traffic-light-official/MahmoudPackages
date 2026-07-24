"""The result every rate-limiting algorithm produces.

A single, algorithm-agnostic shape lets the throttle classes, header
builders, and tests all work identically regardless of which algorithm
(token bucket, sliding window, fixed window) actually decided the
outcome.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LimitResult:
    """The outcome of checking one request against a rate limit.

    Attributes:
        allowed: Whether the request is within its limit.
        limit: The configured maximum (requests, or weighted cost units,
            per window/bucket capacity).
        remaining: How much of the limit is left after this check
            (never negative).
        reset_seconds: Seconds until the limit fully resets (the window
            closes, or the bucket refills to capacity). Always present,
            regardless of ``allowed``.
        retry_after: Seconds the caller should wait before retrying.
            ``None`` when ``allowed`` is ``True``.
    """

    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    retry_after: int | None
