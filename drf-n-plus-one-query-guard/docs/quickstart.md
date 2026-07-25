# Quick Start

## In a test

```python
from drf_n_plus_one_query_guard import assert_no_n_plus_one


def test_article_list_has_no_n_plus_one(api_client):
    with assert_no_n_plus_one():
        api_client.get("/articles/")
```

## Guarding every request

```python
# settings.py
MIDDLEWARE = [
    ...,
    "drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware",
]
```

## Guarding one view

```python
from drf_n_plus_one_query_guard import guard_view


class ArticleViewSet(viewsets.ModelViewSet):
    @guard_view(mode="raise")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

## From Python, at any lower level you need

```python
from drf_n_plus_one_query_guard import NPlusOneGuard

with NPlusOneGuard(mode="report") as guard:
    ...  # anything that executes queries

for violation in guard.violations:
    print(violation.count, violation.fingerprint, violation.call_site)
```

```python
from drf_n_plus_one_query_guard import QueryTracker

with QueryTracker() as tracker:
    ...

for violation in tracker.violations(threshold=3):
    print(violation.count, violation.fingerprint)
```

See [Architecture](architecture.md) for how `NPlusOneGuard` (dispatches
on `MODE`) relates to `QueryTracker` (pure capture, no dispatch).
