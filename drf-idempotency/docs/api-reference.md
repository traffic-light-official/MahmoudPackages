# API Reference

Generated in part from source docstrings via
[mkdocstrings](https://mkdocstrings.github.io/).

## Integration points

### IdempotencyMiddleware

::: drf_idempotency.middleware.IdempotencyMiddleware

### idempotent

::: drf_idempotency.decorators.idempotent

## Status tracking

### get_idempotency_status

::: drf_idempotency.status.get_idempotency_status

## Fingerprinting

### compute_fingerprint

::: drf_idempotency.fingerprint.compute_fingerprint

## Backends

### BaseBackend

::: drf_idempotency.backends.base.BaseBackend

### StoredRecord

::: drf_idempotency.backends.base.StoredRecord

### AcquireResult

::: drf_idempotency.backends.base.AcquireResult

### DatabaseBackend

::: drf_idempotency.backends.database.DatabaseBackend

### RedisBackend

::: drf_idempotency.backends.redis.RedisBackend

## Models

### IdempotencyRecord

::: drf_idempotency.models.IdempotencyRecord

## Exceptions

### IdempotencyError

::: drf_idempotency.exceptions.IdempotencyError

### MissingIdempotencyKeyError

::: drf_idempotency.exceptions.MissingIdempotencyKeyError

### InvalidIdempotencyKeyError

::: drf_idempotency.exceptions.InvalidIdempotencyKeyError

### IdempotencyKeyReuseError

::: drf_idempotency.exceptions.IdempotencyKeyReuseError

### ConcurrentRequestError

::: drf_idempotency.exceptions.ConcurrentRequestError

## Settings

See [Settings](settings.md) for the full list of recognized
`IDEMPOTENCY` keys.

## Management command

### cleanup_expired_idempotency_keys

```bash
python manage.py cleanup_expired_idempotency_keys [--quiet]
```

See [Deployment](deployment.md#scheduling-cleanup).
