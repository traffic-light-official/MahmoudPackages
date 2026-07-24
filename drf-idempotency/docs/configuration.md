# Configuration

## Choosing a backend

| | `DatabaseBackend` | `RedisBackend` |
| --- | --- | --- |
| Setup | Just `migrate` | Requires a Redis server + `[redis]` extra |
| TTL / expiry | Manual (`cleanup_expired_idempotency_keys`) | Automatic (native Redis `EX`) |
| Works without extra infrastructure | Yes | No — needs Redis |
| Performance under high volume | Good; bounded by your DB | Excellent — purpose-built for this |
| Survives a database failover/restart independent of your primary DB | No (shares your DB) | Yes (if Redis is separate) |

Start with `DatabaseBackend` if you don't already run Redis — it needs
nothing beyond a migration. Move to `RedisBackend` if idempotency records
become a meaningful fraction of your database's write volume, or if you
already run Redis for caching/sessions and want to keep this off your
primary database.

```python
IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.database.DatabaseBackend",
}
# or
IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.redis.RedisBackend",
    "BACKEND_OPTIONS": {"url": "redis://localhost:6379/2"},
}
```

## Choosing which methods are covered

Defaults to `["POST", "PUT", "PATCH"]` — the methods that create or
mutate state. `GET`/`HEAD`/`OPTIONS`/`DELETE` are excluded by default
since `GET` is naturally idempotent and `DELETE`'s idempotency semantics
(deleting an already-deleted resource) are usually handled fine by
returning `404` on the second attempt. Add `DELETE` explicitly if your
delete endpoints have side effects (e.g. triggering a downstream webhook)
that shouldn't repeat:

```python
IDEMPOTENCY = {"METHODS": ["POST", "PUT", "PATCH", "DELETE"]}
```

## Deciding on `REQUIRE_KEY`

Leave disabled (default) while rolling this out — requests without a key
simply skip idempotency handling, so nothing breaks for clients that
haven't adopted the header yet. Enable once every client sends a key, to
close the gap entirely:

```python
IDEMPOTENCY = {"REQUIRE_KEY": True}
```

## Tuning TTLs

- `TTL_SECONDS` (default 24h): how long a completed response stays
  replayable. Match this to how long a client might reasonably retry
  (Stripe uses 24 hours).
- `LOCK_TTL_SECONDS` (default 30s): how long an in-progress lock is held
  before being considered abandoned. Set this comfortably above your
  view's worst-case (but still successful) execution time — too short,
  and a legitimately slow request's lock could be reclaimed by a retry
  while the original is still running; too long, and a genuinely crashed
  worker blocks retries longer than necessary.

## Deciding on `CACHE_CLIENT_ERROR_RESPONSES`

Enabled by default, matching Stripe: a `4xx` validation error is
deterministic for a given request body, so caching and replaying it is
safe and saves the client from re-triggering the same validation logic.
Disable only if your view's error responses have side effects that
shouldn't be silently skipped on retry (unusual, but possible with some
custom exception handling).

## Example project-wide configuration

```python
IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.redis.RedisBackend",
    "BACKEND_OPTIONS": {"url": "redis://localhost:6379/2"},
    "TTL_SECONDS": 86400,
    "LOCK_TTL_SECONDS": 45,
    "REQUIRE_KEY": True,
    "METHODS": ["POST", "PUT", "PATCH", "DELETE"],
}
```
