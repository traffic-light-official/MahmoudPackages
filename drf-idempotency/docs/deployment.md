# Deployment

## Version pinning

```
drf-idempotency>=1.0,<2.0
```

## Supported runtime versions

| Dependency | Supported |
| --- | --- |
| Python | 3.10, 3.11, 3.12, 3.13 |
| Django | 4.2, 5.0, 5.1, 5.2 |
| Django REST Framework | 3.14+ |
| redis (optional) | 5.0+ |

## Database backend: migrations

```bash
python manage.py migrate drf_idempotency
```

This creates one table, `drf_idempotency_idempotencyrecord`. It has no
foreign keys into your own schema, so it can be migrated independently of
your application's own models.

## Scheduling cleanup

The database backend has no native TTL — expired records are treated as
absent on read, but still occupy storage until removed. Schedule the
cleanup command periodically:

**Cron:**

```
0 * * * * cd /path/to/project && python manage.py cleanup_expired_idempotency_keys --quiet
```

**Celery beat:** define a task that wraps the command, then schedule it:

```python
# tasks.py
from celery import shared_task
from django.core.management import call_command


@shared_task
def cleanup_idempotency_keys() -> None:
    call_command("cleanup_expired_idempotency_keys", quiet=True)
```

```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    "cleanup-idempotency-keys": {
        "task": "myapp.tasks.cleanup_idempotency_keys",
        "schedule": crontab(minute=0),  # hourly
    },
}
```

Not needed for `RedisBackend` — Redis expires keys natively via `EX`.

## Redis deployment considerations

- Use a **separate Redis logical database** (`BACKEND_OPTIONS: {"url":
  "redis://host:6379/N"}`) or a distinct `key_prefix` from your caching/
  session Redis usage, so idempotency keys can't collide with unrelated
  keys and can be reasoned about/monitored independently.
- Idempotency records are small and short-lived (bounded by
  `TTL_SECONDS`) — memory footprint scales with your idempotent-request
  volume × `TTL_SECONDS`, not indefinitely.
- If Redis is unavailable, `RedisBackend` calls will raise a connection
  error from the underlying `redis` client — idempotency handling is not
  designed to silently degrade to "no idempotency" on backend failure,
  since that could mean silently allowing double-processing. Monitor
  Redis availability as you would for any other critical dependency.

## Rolling out to an existing API

1. Add `drf_idempotency` to `INSTALLED_APPS` and migrate (database
   backend) — no behavior changes yet.
2. Add `IdempotencyMiddleware` (or the decorator on specific views) with
   `REQUIRE_KEY: False` (default) — clients that don't send the header
   are completely unaffected.
3. Update client SDKs/integrations to send `Idempotency-Key` on retryable
   requests.
4. Once adoption is confirmed (e.g. via logging how many requests arrive
   without the header), consider enabling `REQUIRE_KEY: True` for
   endpoints where double-processing risk justifies making it mandatory.
