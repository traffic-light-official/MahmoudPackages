# Settings

All configuration lives under a single Django setting, `IDEMPOTENCY`, a
dict of overrides merged on top of the defaults below. Settings are
validated eagerly (on first access) and cached; the cache invalidates
automatically on Django's `setting_changed` signal, so
`@override_settings(IDEMPOTENCY={...})` works correctly in tests.

## HEADER_NAME

- **Type:** `str`
- **Default:** `"Idempotency-Key"`

The request header carrying the client-supplied idempotency key.

## REPLAY_HEADER_NAME

- **Type:** `str`
- **Default:** `"Idempotent-Replayed"`

The response header set to `"true"` on a replayed response and `"false"`
on a freshly-executed one.

## METHODS

- **Type:** `list[str]`
- **Default:** `["POST", "PUT", "PATCH"]`

HTTP methods idempotency handling applies to. Case-insensitive; normalized
to uppercase internally.

## BACKEND

- **Type:** `str` (dotted import path)
- **Default:** `"drf_idempotency.backends.database.DatabaseBackend"`

The backend class used to store idempotency records. See
[`BaseBackend`](api-reference.md#basebackend) for the interface, and
[Configuration](configuration.md#choosing-a-backend) for choosing between
the built-in options.

## BACKEND_OPTIONS

- **Type:** `dict`
- **Default:** `{}`

Extra keyword arguments passed to the backend's constructor — e.g. `{"url":
"redis://...", "key_prefix": "myapp:"}` for `RedisBackend`.

## TTL_SECONDS

- **Type:** `int`
- **Default:** `86400` (24 hours)

How long a completed response remains eligible for replay.

## LOCK_TTL_SECONDS

- **Type:** `int`
- **Default:** `30`

How long an in-progress lock is held before being considered abandoned
(e.g. the worker handling the original request crashed) and reclaimable
by a subsequent attempt.

## REQUIRE_KEY

- **Type:** `bool`
- **Default:** `False`

When `True`, requests using a method in `METHODS` without the idempotency
header are rejected with `400 Bad Request`.

## MAX_KEY_LENGTH

- **Type:** `int`
- **Default:** `255`

Maximum accepted length of the idempotency key itself.

## CACHE_CLIENT_ERROR_RESPONSES

- **Type:** `bool`
- **Default:** `True`

Whether `4xx` responses are cached and replayed like successful ones.
`5xx` responses are never cached regardless of this setting.
