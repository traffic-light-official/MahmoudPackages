# drf-n-plus-one-query-guard

[![PyPI version](https://img.shields.io/pypi/v/drf-n-plus-one-query-guard.svg)](https://pypi.org/project/drf-n-plus-one-query-guard/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-n-plus-one-query-guard.svg)](https://pypi.org/project/drf-n-plus-one-query-guard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Detect N+1 query patterns in Django REST Framework views - in tests, in
development, and (opt-in) in production - by fingerprinting repeated
SQL shapes, not just counting total queries.

```python
from drf_n_plus_one_query_guard import assert_no_n_plus_one


def test_article_list_has_no_n_plus_one(api_client):
    with assert_no_n_plus_one():
        api_client.get("/articles/")
```

```
AssertionError: Suspected N+1 queries detected:
  5x 'SELECT ... FROM test_app_author WHERE id = %s' (first at views.py:42)
```

## Why

A plain "assert query count <= N" test breaks every time you add an
unrelated, legitimate query, and tells you nothing about *which* query
is the problem when it fails. This package fingerprints each executed
query's normalized SQL shape and flags a shape that repeats - which is
what an N+1 actually looks like (one query per row of an un-prefetched
loop) - along with the application code location that triggered it.

## Features

- **Fingerprint-based detection**, not a query-count budget: catches
  the actual repeated-shape pattern, with the call site that caused it.
- **`assert_no_n_plus_one()`**: a self-contained pytest context manager,
  independent of any Django setting - drop it into any test.
- **`NPlusOneGuardMiddleware`**: guards every request; `warn`/`raise`/
  `report` modes, plus a `DEBUG`-only response header.
- **`guard_view()`**: a per-view/per-action decorator for narrower opt-in.
- **Works across every configured database alias**, via Django's public
  `connection.execute_wrapper()` hook - no `DEBUG=True` requirement, no
  monkeypatching.
- **An ignore list** (`IGNORE_PATTERNS`) for known, accepted repeated
  queries, so you don't have to raise the threshold project-wide.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-n-plus-one-query-guard
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_n_plus_one_query_guard",
]
```

## Quick Start

In a test:

```python
from drf_n_plus_one_query_guard import assert_no_n_plus_one

with assert_no_n_plus_one():
    list(Article.objects.all())  # fine: no repeated fingerprint
```

Guarding every request in development:

```python
# settings.py
MIDDLEWARE = [
    ...,
    "drf_n_plus_one_query_guard.middleware.NPlusOneGuardMiddleware",
]
```

Guarding one view:

```python
from drf_n_plus_one_query_guard import guard_view


class ArticleViewSet(viewsets.ModelViewSet):
    @guard_view(mode="raise")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

See [`docs/quickstart.md`](docs/quickstart.md) for the full settings
reference.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-n-plus-one-query-guard/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-n-plus-one-query-guard/LICENSE).
