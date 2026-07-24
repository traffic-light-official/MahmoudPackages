# FAQ

## Why is Redis a hard requirement, not an optional backend?

Correct distributed rate limiting needs an atomic, shared, low-latency
read-modify-write primitive — Redis's Lua scripting (`EVAL`) is exactly
that. A database-backed alternative (like `drf-idempotency` offers) would
need per-request row locking or unique-constraint tricks that don't map
cleanly onto "count requests per rolling time window" the way they do
onto "claim this key exactly once" — so this package doesn't pretend to
offer a database fallback.

## Does this replace DRF's built-in throttles?

Not necessarily — `rate_limit()`-produced throttles are regular
`BaseThrottle` subclasses, so they coexist fine with `UserRateThrottle`,
`AnonRateThrottle`, or `ScopedRateThrottle` in the same
`throttle_classes` list if you have a reason to keep both. Most projects
migrating fully to this package simply replace the built-in ones for the
extra algorithm choice, burst handling, and header support.

## What happens if I don't add `RateLimitHeadersMixin`?

Throttling still works fully — `429`/`Retry-After` come from DRF's own
`Throttled` exception regardless. You just won't get the informational
`RateLimit-Limit`/`RateLimit-Remaining`/`RateLimit-Reset` headers on
successful responses.

## Can I use this outside DRF, in plain Django views?

The algorithm functions (`token_bucket_check`, etc.) have no DRF
dependency — call them directly from any Python code, including a plain
Django view. `rate_limit()`/`RateLimitThrottle`/`RateLimitHeadersMixin`
are DRF-specific (they build on `BaseThrottle` and `finalize_response()`),
so for a non-DRF view you'd call the algorithm function yourself and
handle the `429` response manually.

## How is this different from `django-ratelimit`?

`django-ratelimit` targets plain Django views with a decorator-first API
and (typically) Django's cache framework as a backend. This package is
DRF-native (built on `BaseThrottle`, composes with `permission_classes`/
`authentication_classes`/other throttles automatically), Redis-first (for
genuine distributed atomicity and Cluster support), and offers token
bucket/sliding window algorithms with real burst handling that a
cache-backed fixed-window counter can't provide.

## Does `cost=0` let me "peek" at the current state without consuming budget?

Yes for token bucket (a true no-op check). Fixed/sliding window with
`cost=0` also don't consume budget, but as a side effect may initialize a
counter key for a previously-unseen identity (setting its TTL) even
though no real request occurred — a minor, harmless quirk of how the
underlying `INCRBY 0` command behaves on a non-existent key. See
[Advanced Usage](advanced-usage.md#inspecting-a-keys-current-state-directly).

## Is there a way to reset a specific key manually?

Not as public API today, but straightforward via the client directly for
an operational/debugging scenario:

```python
from drf_ratelimit_plus.client import get_redis_client
from drf_ratelimit_plus.settings import get_setting

get_redis_client().delete(f"{get_setting('KEY_PREFIX')}token_bucket:some-scope:user:42")
```

(Match the key format your configured algorithm/scope/key function
actually produces — see [Architecture](architecture.md) for how keys are
built.)
