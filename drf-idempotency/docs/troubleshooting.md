# Troubleshooting

## `422 Unprocessable Entity` when retrying what looks like the same request

**Cause:** the request body differs from what was originally associated
with this idempotency key — even a whitespace or field-ordering
difference in a raw string body would matter if your fingerprint were
computed differently, though this package hashes the *raw bytes* Django
received, so JSON key ordering from `json.dumps` on the client side
**does** matter if it varies between attempts (e.g. a dict with
non-deterministic key order serialized differently each time).

**Fix:** ensure your client serializes the retry body identically to the
original (e.g. build the JSON string once and reuse it across attempts,
rather than re-serializing a dict whose key order might vary), or
generate a fresh idempotency key if the request is genuinely different.

## `409 Conflict` that never resolves

**Cause:** either a genuinely very slow original request (increase
`LOCK_TTL_SECONDS` if this is expected), or a worker that crashed while
holding the lock — in which case the lock self-expires after
`LOCK_TTL_SECONDS` and a subsequent retry will be allowed to proceed (see
[Architecture](architecture.md)). If retries keep hitting `409` well past
your configured `LOCK_TTL_SECONDS`, something is holding a *new* lock each
time — check whether each retry is generating a *new* key rather than
reusing one (a very common client bug).

## Middleware raises the wrong kind of response / raw exception instead of JSON

If you're extending or overriding `IdempotencyMiddleware` and lost the
`try/except IdempotencyError` wrapper, see
[Architecture](architecture.md#why-view-exceptions-behave-differently-under-middleware-vs-the-decorator) —
this package's exceptions subclass `APIException`, which only
auto-converts to a response *inside DRF's own view dispatch*, not in
plain Django middleware. If you write a custom middleware wrapper, keep
that `try/except` (or call `drf_idempotency.core.build_error_response`
yourself).

## `ImproperlyConfigured: Unknown key(s) in 'IDEMPOTENCY'`

**Cause:** a typo in a setting name, or a key that doesn't exist. Compare
against [Settings](settings.md) — every key is case-sensitive.

## `django.db.utils.OperationalError: no such table: drf_idempotency_idempotencyrecord`

**Cause:** using `DatabaseBackend` without running migrations.

**Fix:** ensure `"drf_idempotency"` is in `INSTALLED_APPS` and run
`python manage.py migrate`.

## `ImportError: drf_idempotency.backends.redis requires the 'redis' package`

**Cause:** `RedisBackend` configured without the `redis` package
installed.

**Fix:** `pip install drf-idempotency[redis]`.

## A decorated view combined with global middleware returns an unexpected `409`

This should not happen with the built-in re-entrancy guard — see
[Architecture](architecture.md#re-entrancy-guard). If you see this,
check whether you're constructing a *new* request object somewhere
between the middleware and the decorator (e.g. re-wrapping
`HttpRequest` in a fresh `Request` instance) — the guard relies on a
marker attribute persisting on the *same* request object across both
layers. If your code creates a new request wrapper mid-stack, the marker
won't be visible to the inner layer.

## Response headers seem to be missing after replay

Only headers stored at `complete()` time are replayed;
`Content-Length`, `Connection`, and `Set-Cookie` are deliberately excluded
from what's stored (see [Architecture](architecture.md)) — the first two
are recomputed correctly by Django regardless, and `Set-Cookie` is
excluded as a deliberate safety choice (replaying a stale `Set-Cookie`
value on every retry would be surprising and is rarely, if ever, desired).
If you need a specific header preserved that isn't showing up, check it
was actually present on the *first* response (the one that got cached),
not just expected by convention.

## Tests fail with "database is locked" using the database backend

This is a SQLite-specific limitation when running true concurrent
(multi-threaded/multi-process) access against an in-memory database — see
`tests/test_concurrency.py`'s module docstring in this package's own
repository for why its race-condition tests target the Redis backend
instead. Use a real database (PostgreSQL/MySQL) or a file-based SQLite
database with appropriate timeout settings if you need to test genuine
multi-connection concurrency against `DatabaseBackend` specifically.
