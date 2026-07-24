# Settings

All configuration lives under a single Django setting, `RATELIMIT_PLUS`, a
dict of overrides merged on top of the defaults below.

## REDIS_URL

- **Type:** `str`
- **Default:** `"redis://localhost:6379/0"`

Used to construct the default Redis client. Ignored if `REDIS_CLIENT` is
set.

## REDIS_CLIENT

- **Type:** `str | None`
- **Default:** `None`

A dotted path to a pre-built `redis.Redis`/`redis.cluster.RedisCluster`
instance, or to a no-argument callable returning one. Takes precedence
over `REDIS_URL` when set.

## KEY_PREFIX

- **Type:** `str`
- **Default:** `"ratelimit-plus:"`

Prefix applied to every Redis key this package writes.

## LIMIT_HEADER / REMAINING_HEADER / RESET_HEADER

- **Type:** `str`
- **Defaults:** `"RateLimit-Limit"`, `"RateLimit-Remaining"`, `"RateLimit-Reset"`

Response header names, added by `RateLimitHeadersMixin` (and the
`@ratelimit()` decorator).

## API_KEY_HEADER

- **Type:** `str`
- **Default:** `"X-API-Key"`

Header read by the built-in `by_api_key` key function.

## TENANT_ATTR

- **Type:** `str`
- **Default:** `"tenant_id"`

Attribute read off `request` by the built-in `by_tenant` key function.

## DEFAULT_TIER

- **Type:** `str`
- **Default:** `"default"`

Fallback tier name used when a plan-tier rate mapping doesn't have an
entry for the resolved tier, and when `default_tier_resolver` can't
determine a plan for the current request.
