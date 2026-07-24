# Advanced Usage

## Using the Redis backend

```bash
pip install drf-idempotency[redis]
```

```python
IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.redis.RedisBackend",
    "BACKEND_OPTIONS": {"url": "redis://localhost:6379/2", "key_prefix": "myapp-idempotency:"},
}
```

Or reuse an existing client instance (e.g. one you already configured
with connection pooling elsewhere):

```python
import redis

_client = redis.Redis(host="localhost", port=6379, db=2)

IDEMPOTENCY = {
    "BACKEND": "drf_idempotency.backends.redis.RedisBackend",
    "BACKEND_OPTIONS": {"client": _client},
}
```

## Using the database backend

```python
IDEMPOTENCY = {"BACKEND": "drf_idempotency.backends.database.DatabaseBackend"}
```

```bash
python manage.py migrate
python manage.py cleanup_expired_idempotency_keys  # run periodically
```

Works identically on PostgreSQL, MySQL, and SQLite — atomicity comes from
a unique constraint plus Django's own `get_or_create` (which catches the
resulting `IntegrityError` and re-fetches), not any database-specific
locking feature.

## Writing a custom backend

Implement `BaseBackend`'s five methods:

```python
from datetime import timedelta
from collections.abc import Mapping
from drf_idempotency.backends.base import AcquireResult, BaseBackend, StoredRecord


class MemcachedBackend(BaseBackend):
    def acquire_or_get(self, key: str, fingerprint: str, *, lock_ttl: timedelta) -> AcquireResult:
        ...

    def complete(self, key: str, *, status_code: int, headers: Mapping[str, str], body: bytes, ttl: timedelta) -> None:
        ...

    def fail(self, key: str) -> None:
        ...

    def get(self, key: str) -> StoredRecord | None:
        ...

    def cleanup_expired(self) -> int:
        ...
```

The correctness of the whole package hinges on `acquire_or_get` being
genuinely atomic: if two callers invoke it concurrently for the same key,
exactly one must get `acquired=True`. See
`drf_idempotency.backends.redis.RedisBackend` (built on Redis's atomic
`SET NX`) and `drf_idempotency.backends.database.DatabaseBackend` (built
on a unique constraint) for two different ways to achieve this — pick
whichever your storage technology naturally supports.

```python
IDEMPOTENCY = {"BACKEND": "myapp.backends.MemcachedBackend"}
```

## Combining the decorator with global middleware

If `IdempotencyMiddleware` is installed project-wide *and* a specific
view also carries `@idempotent()` (perhaps left over from before the
middleware was added), both wrapping the same request is handled safely:
the outer layer (the middleware) performs the real acquire-or-replay
logic, and the inner layer (the decorator) detects this via a marker
already set on the request and simply calls the view directly — no
spurious `409 Conflict` against your own outer layer. See
[Architecture](architecture.md#re-entrancy-guard) for why this is
necessary and how it works. Even so, prefer using **one** integration
point per view for clarity — mixing them project-wide is more likely to
confuse a future reader than to serve a real purpose.

## Combining with other middleware

`IdempotencyMiddleware` reads `request.body` (via fingerprinting) before
your view runs. This is compatible with Django's standard middleware
ordering — place it wherever you'd place any other middleware that needs
to inspect the request body (typically after security/session middleware,
before your own custom business-logic middleware).

## Inspecting a stored record directly

For debugging or admin tooling:

```python
from drf_idempotency.core import get_backend

record = get_backend().get("some-key")
if record is not None:
    print(record.status, record.response_status_code)
```

## Multiple backends in one project

Nothing prevents constructing a second backend instance directly (bypassing
the global `IDEMPOTENCY` setting) for a specific use case — e.g. a
short-TTL, in-memory-like Redis instance for one particularly
high-volume, latency-sensitive endpoint, alongside the database backend
for everything else. Call `RedisBackend(...)`/`DatabaseBackend(...)`
directly and use `drf_idempotency.core.process_idempotent_request`
yourself rather than the standard middleware/decorator, if you need this
level of control.
