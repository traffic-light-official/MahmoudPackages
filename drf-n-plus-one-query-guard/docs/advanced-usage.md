# Advanced Usage

## Middleware

```python
MIDDLEWARE = [
    ...,
    "drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware",
]
```

Wraps every request in an `NPlusOneGuard` using the configured `MODE`:

- `"warn"`/`"report"`: the request completes normally. When
  `settings.DEBUG` is `True`, a summary of any violations is added via
  the `RESPONSE_HEADER` response header (never added when `DEBUG` is
  `False`).
- `"raise"`: a suspected N+1 becomes an `NPlusOneDetectedError`
  propagating out of the middleware like any other unhandled exception
  - typically a 500 response via Django's normal exception handling.
  Only enable this for the middleware in development/CI/staging - see
  [Security](security.md).

## Guarding a specific view or action

```python
from drf_n_plus_one_query_guard import guard_view


class ArticleViewSet(viewsets.ModelViewSet):
    @guard_view(mode="raise", threshold=2)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    @guard_view()
    def comments(self, request, *args, **kwargs):
        ...
```

`threshold`/`mode` passed to `guard_view()` override the
`N_PLUS_ONE_GUARD` setting for that one method only, same as
`NPlusOneGuard(threshold=..., mode=...)` directly.

## Using `NPlusOneGuard` directly for custom dispatch

`NPlusOneGuard` is what both the middleware and `guard_view()` are
built on - use it directly for anything neither covers (a Celery task,
a management command, a GraphQL resolver):

```python
from drf_n_plus_one_query_guard import NPlusOneGuard

def process_batch(items):
    with NPlusOneGuard(mode="warn") as guard:
        for item in items:
            handle(item)
    if guard.violations:
        metrics.increment("n_plus_one.detected", len(guard.violations))
```

## Using `QueryTracker` directly for fully custom reporting

`QueryTracker` only captures - it never logs, raises, or reads any
setting. Use it directly if you want to build your own reporting layer
(e.g. sending violations to an APM tool instead of `logging`):

```python
from drf_n_plus_one_query_guard import QueryTracker

with QueryTracker() as tracker:
    handle_request()

for violation in tracker.violations(threshold=2):
    apm_client.capture_message(
        f"Suspected N+1: {violation.fingerprint!r} x{violation.count}",
        extra={"call_site": violation.call_site},
    )
```

## Inspecting every captured query, not just violations

`tracker.events`/`guard._tracker` (via `NPlusOneGuard`, not part of its
public API - use `QueryTracker` directly if you need this) holds every
`QueryEvent`, not just the ones that repeated - useful for building a
full per-request query log:

```python
from drf_n_plus_one_query_guard import QueryTracker

with QueryTracker() as tracker:
    handle_request()

for event in tracker.events:
    print(event.alias, event.call_site, event.sql)
```

## Multiple database aliases

`QueryTracker` (and therefore `NPlusOneGuard`,
`NPlusOneGuardMiddleware`, `guard_view()`, `assert_no_n_plus_one()`) all
instrument every alias in Django's `connections.all()`, not just
`"default"` - a fingerprint repeating on a read-replica alias is
reported the same as one on `"default"`. `QueryEvent.alias` tells you
which.
