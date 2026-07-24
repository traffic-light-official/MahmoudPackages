"""Rate-limiting algorithms, implemented as atomic Redis Lua scripts.

Each algorithm is a single ``EVAL`` call — Redis executes Lua scripts
atomically, so there is no read-modify-write race between concurrent
requests, and (critically for Redis Cluster) every script here only ever
touches keys that hash to the same slot, so no cross-slot transaction
support is required.

All three algorithms share one calling convention: they take a
``client``, a ``key`` (already prefixed and scoped by the caller), a
:class:`~drf_ratelimit_plus.rates.Rate`, a request ``cost``, an optional
``burst`` (token bucket only), and the current time; they return a
:class:`~drf_ratelimit_plus.results.LimitResult`.
"""

from __future__ import annotations

import math
import time
from typing import Any

from drf_ratelimit_plus.rates import Rate
from drf_ratelimit_plus.results import LimitResult

# --------------------------------------------------------------------------
# Fixed window
# --------------------------------------------------------------------------

_FIXED_WINDOW_SCRIPT = """
local key = KEYS[1]
local period_ms = tonumber(ARGV[1])
local cost = tonumber(ARGV[2])

local current = redis.call('INCRBY', key, cost)
if current == cost then
    redis.call('PEXPIRE', key, period_ms)
end
local ttl = redis.call('PTTL', key)
if ttl < 0 then
    redis.call('PEXPIRE', key, period_ms)
    ttl = period_ms
end
return {current, ttl}
"""


def fixed_window_check(
    client: Any, key: str, rate: Rate, *, cost: int = 1, now: float | None = None
) -> LimitResult:
    """Check a request against a fixed-window rate limit.

    Counts requests in discrete, non-overlapping windows of ``rate.period``
    seconds. Simple and cheap, but allows up to ``2 * rate.count`` requests
    across a window boundary (e.g. a burst just before a window ends,
    followed immediately by another just after it starts). Prefer
    :func:`sliding_window_check` if that boundary burst is a concern.

    Args:
        client: A Redis client (standalone or Cluster).
        key: The fully-qualified Redis key for this rate limit identity.
        rate: The configured limit.
        cost: How many units this request consumes (for weighted costs).
        now: Unused; accepted for calling-convention symmetry with the
            other algorithms.

    Returns:
        The :class:`~drf_ratelimit_plus.results.LimitResult`.
    """
    period_ms = int(rate.period * 1000)
    current, ttl_ms = client.eval(_FIXED_WINDOW_SCRIPT, 1, key, period_ms, cost)
    current = int(current)
    ttl_ms = int(ttl_ms)
    allowed = current <= rate.count
    remaining = max(0, rate.count - current)
    reset_seconds = math.ceil(ttl_ms / 1000)
    retry_after = reset_seconds if not allowed else None
    return LimitResult(
        allowed=allowed,
        limit=rate.count,
        remaining=remaining,
        reset_seconds=reset_seconds,
        retry_after=retry_after,
    )


# --------------------------------------------------------------------------
# Sliding window (Cloudflare-style weighted counter approximation)
# --------------------------------------------------------------------------

_SLIDING_WINDOW_SCRIPT = """
local current_key = KEYS[1]
local previous_key = KEYS[2]
local period_ms = tonumber(ARGV[1])
local cost = tonumber(ARGV[2])
local elapsed_ms = tonumber(ARGV[3])

local previous = tonumber(redis.call('GET', previous_key) or '0')
local weight = (period_ms - elapsed_ms) / period_ms
if weight < 0 then weight = 0 end
local current = tonumber(redis.call('GET', current_key) or '0')
local estimated_total = (previous * weight) + current

-- Returned as tostring(): Redis converts a Lua number reply to an
-- integer (RESP2 has no float reply type), which would silently
-- truncate the fractional estimate otherwise.
if estimated_total + cost > tonumber(ARGV[4]) then
    return {0, tostring(estimated_total), current, previous}
end

current = redis.call('INCRBY', current_key, cost)
redis.call('PEXPIRE', current_key, period_ms * 2)
return {1, tostring(estimated_total + cost), current, previous}
"""


def sliding_window_check(
    client: Any, key: str, rate: Rate, *, cost: int = 1, now: float | None = None
) -> LimitResult:
    """Check a request against an approximate sliding-window rate limit.

    Estimates the request count over the trailing ``rate.period`` seconds
    as a weighted blend of the current fixed window's count and the
    previous window's count, weighted by how far into the current window
    "now" is. This is the same approximation Cloudflare's public rate
    limiter documentation describes: memory-efficient (two counters per
    identity, not one entry per request) while avoiding fixed-window's
    boundary-burst problem.

    Args:
        client: A Redis client (standalone or Cluster).
        key: The fully-qualified Redis key for this rate limit identity.
            Both the current and previous window's actual keys are
            derived from this with a ``{hash-tag}``-safe suffix, so they
            always land on the same Cluster slot.
        rate: The configured limit.
        cost: How many units this request consumes.
        now: The current time, as seconds since the epoch. Defaults to
            :func:`time.time`; pass explicitly in tests for determinism.

    Returns:
        The :class:`~drf_ratelimit_plus.results.LimitResult`. ``remaining``
        and ``reset_seconds`` are based on the estimated (not exact)
        count, consistent with this algorithm's approximate nature.
    """
    now_ms = int((now if now is not None else time.time()) * 1000)
    period_ms = int(rate.period * 1000)
    window_index = now_ms // period_ms
    elapsed_ms = now_ms - (window_index * period_ms)

    # Wrap the entire base key in a Redis Cluster hash tag ("{...}") so
    # only its content (not the differing window-index suffix appended
    # outside the braces) determines the hash slot - guaranteeing both
    # keys below always land on the same slot/node, with no cooperation
    # required from the caller.
    current_key = f"{{{key}}}:{window_index}"
    previous_key = f"{{{key}}}:{window_index - 1}"

    allowed_flag, estimated_total, _current, _previous = client.eval(
        _SLIDING_WINDOW_SCRIPT,
        2,
        current_key,
        previous_key,
        period_ms,
        cost,
        elapsed_ms,
        rate.count,
    )
    allowed = bool(int(allowed_flag))
    estimated_total = float(estimated_total)
    remaining = max(0, math.floor(rate.count - estimated_total))
    reset_seconds = math.ceil((period_ms - elapsed_ms) / 1000)
    retry_after = reset_seconds if not allowed else None
    return LimitResult(
        allowed=allowed,
        limit=rate.count,
        remaining=remaining,
        reset_seconds=reset_seconds,
        retry_after=retry_after,
    )


# --------------------------------------------------------------------------
# Token bucket
# --------------------------------------------------------------------------

_TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_per_ms = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now_ms = tonumber(ARGV[4])
local ttl_ms = tonumber(ARGV[5])

local bucket = redis.call('HMGET', key, 'tokens', 'timestamp')
local tokens = tonumber(bucket[1])
local timestamp = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    timestamp = now_ms
end

local delta_ms = now_ms - timestamp
if delta_ms < 0 then delta_ms = 0 end
tokens = math.min(capacity, tokens + (delta_ms * refill_per_ms))

local allowed = 0
if tokens >= cost then
    tokens = tokens - cost
    allowed = 1
end

redis.call('HSET', key, 'tokens', tostring(tokens), 'timestamp', tostring(now_ms))
redis.call('PEXPIRE', key, ttl_ms)

return {allowed, tostring(tokens)}
"""


def token_bucket_check(
    client: Any,
    key: str,
    rate: Rate,
    *,
    cost: int = 1,
    burst: int | None = None,
    now: float | None = None,
) -> LimitResult:
    """Check a request against a token-bucket rate limit.

    The bucket refills continuously at ``rate.count / rate.period`` tokens
    per second, up to a capacity of ``burst`` (defaulting to ``rate.count``
    if not given — i.e. no extra burst allowance beyond the steady-state
    rate). This is the algorithm to reach for when you want to allow a
    client to burst above their steady-state rate occasionally, as long as
    they've been under it recently (each unused token accumulates, up to
    the bucket's capacity).

    Args:
        client: A Redis client (standalone or Cluster).
        key: The fully-qualified Redis key for this rate limit identity —
            a single Redis Hash storing ``tokens`` and ``timestamp``, so
            this is always a single-key (Cluster-safe) operation.
        rate: The configured steady-state limit.
        cost: How many tokens this request consumes.
        burst: The bucket's capacity, i.e. the maximum number of tokens
            that can accumulate for later bursting. Defaults to
            ``rate.count``.
        now: The current time, as seconds since the epoch. Defaults to
            :func:`time.time`; pass explicitly in tests for determinism.

    Returns:
        The :class:`~drf_ratelimit_plus.results.LimitResult`. ``limit`` is
        reported as the bucket's capacity (``burst``), since that's the
        maximum a single burst can consume.
    """
    capacity = burst if burst is not None else rate.count
    refill_per_ms = rate.per_second / 1000.0
    now_ms = int((now if now is not None else time.time()) * 1000)
    # Keep the bucket alive long enough to refill from empty to capacity,
    # plus a safety margin, so a quiet identity doesn't linger forever but
    # also doesn't expire mid-accumulation.
    ttl_ms = int((capacity / rate.per_second) * 1000) + int(rate.period * 1000)

    allowed_flag, tokens_str = client.eval(
        _TOKEN_BUCKET_SCRIPT, 1, key, capacity, refill_per_ms, cost, now_ms, ttl_ms
    )
    allowed = bool(int(allowed_flag))
    tokens = float(tokens_str)
    remaining = max(0, math.floor(tokens))
    if allowed:
        retry_after = None
    else:
        deficit = cost - tokens
        retry_after = math.ceil(deficit / refill_per_ms / 1000) if refill_per_ms > 0 else None
    reset_seconds = math.ceil((capacity - tokens) / rate.per_second) if rate.per_second > 0 else 0
    return LimitResult(
        allowed=allowed,
        limit=capacity,
        remaining=remaining,
        reset_seconds=max(0, reset_seconds),
        retry_after=retry_after,
    )
