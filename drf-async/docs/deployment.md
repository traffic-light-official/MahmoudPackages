# Deployment

## Checklist

- [ ] `drf_async` in `INSTALLED_APPS`.
- [ ] Served behind a real ASGI server (`uvicorn`/`daphne`/`hypercorn`),
      not just `runserver`/a WSGI worker - otherwise async views still
      work correctly but gain no concurrency benefit (see
      [Performance](performance.md#async-views-only-pay-off-under-an-asgi-server)).
- [ ] Django's `DATABASES` backend supports the async ORM your handler
      code calls directly - all first-party backends (PostgreSQL,
      MySQL, SQLite, Oracle) do as of Django 4.2+; a third-party
      backend that hasn't implemented the async interface will raise
      `NotSupportedError` the moment an async ORM call reaches it.
- [ ] Every viewset registered with a router mixes only async actions
      or only sync actions - a viewset with both sync and async
      `@action`-decorated methods bound in the same `as_view()` call
      gets treated as fully synchronous by Django (see
      [Architecture](architecture.md#why-as_view-needs-an-override)),
      silently losing the concurrency benefit for its async actions
      rather than failing loudly.
- [ ] Cache backend used by `AsyncSimpleRateThrottle` subclasses
      (`CACHES["default"]`, or whatever `cache` alias you use) supports
      Django's async cache interface - the built-in Redis and local-memory
      backends do; a third-party cache backend that only implements the
      sync interface raises `NotImplementedError` from `cache.aget`/`.aset`.

## No database migrations, no persisted state of its own

This package defines no models - there is nothing to migrate, and no
state persists between requests or between processes. Rate-limit
history for `AsyncSimpleRateThrottle` lives in whatever cache backend
you configure, exactly like DRF's own `SimpleRateThrottle`.

## ASGI application setup

```python
# asgi.py
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
application = get_asgi_application()
```

```bash
uvicorn myproject.asgi:application --workers 4
```

Each `uvicorn` worker process runs its own event loop; async views
within one worker process share that loop, yielding control to other
in-flight requests during any `await` on I/O (an async ORM call, a
cache read, an awaited async permission/throttle). Scale worker *count*
for CPU-bound concurrency the same way you would for a sync deployment
(more processes, one per core) - the event loop only helps with
I/O-bound concurrency within a process.

## Mixed sync/async views in the same project

Nothing prevents deploying `AsyncModelViewSet`-based views alongside
plain sync `ModelViewSet`-based ones behind the same ASGI server -
Django's async handler dispatches each view according to its own
`view_is_async` marking (see
[Architecture](architecture.md#why-as_view-needs-an-override)), calling
sync views through a thread-pool bridge automatically. There is no
project-wide "all views must be async" requirement; convert
incrementally (see
[Common Patterns](common-patterns.md#migrating-an-existing-sync-viewset-incrementally)).

## Database connection pool sizing under async load

An ASGI worker serving many concurrent async requests can open more
simultaneous database connections than a WSGI worker handling one
request at a time ever would, since I/O-bound requests interleave
within the same process instead of queuing behind each other. Size
`CONN_MAX_AGE` and any external connection pooler (PgBouncer, etc.)
for your actual expected concurrency, not for the request-at-a-time
assumption a sync deployment's connection usage pattern might suggest.
