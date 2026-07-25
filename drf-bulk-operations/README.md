# drf-bulk-operations

[![PyPI version](https://img.shields.io/pypi/v/drf-bulk-operations.svg)](https://pypi.org/project/drf-bulk-operations/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-bulk-operations.svg)](https://pypi.org/project/drf-bulk-operations/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Bulk create/update/delete endpoints for Django REST Framework
ViewSets - one JSON list in, per-item results out, with a real choice
between atomic (all-or-nothing) and non-atomic (independent, partial
success) semantics.

```python
from drf_bulk_operations import BulkModelViewSet


class ArticleViewSet(BulkModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

```
POST   /articles/bulk/                    [{"title": "A"}, {"title": "B"}]
PUT    /articles/bulk-update/             [{"id": 1, "title": "A2"}, {"id": 2, "title": "B2"}]
PATCH  /articles/bulk-partial-update/     [{"id": 1, "title": "A3"}]
DELETE /articles/bulk-delete/             [1, 2, 3]
```

## Why

DRF's own mixins handle exactly one object per request. Creating,
updating, or deleting a hundred objects means a hundred round trips -
or writing the same bulk-endpoint boilerplate (batch size limits,
per-item validation, deciding what "partial failure" even means) in
every project that needs it. This package adds that layer once,
correctly.

## Features

- **`bulk_create`/`bulk_update`/`bulk_partial_update`/`bulk_destroy`**
  actions - mix in only the ones you need, or use `BulkModelViewSet`
  for all four.
- **Atomic mode** (default): every item is validated before anything is
  written; if any item is invalid, nothing is saved and the response
  lists every item's errors by index.
- **Non-atomic mode**: every item is attempted independently (its own
  savepoint), so one bad item doesn't block the rest - the response
  reports exactly which items succeeded and which didn't
  (`207 Multi-Status` for a mixed result).
- **`MAX_BATCH_SIZE`** setting to cap how many items one request may
  submit.
- Per-object permission checks on `bulk_update`/`bulk_partial_update`/
  `bulk_destroy`, exactly like DRF's own single-object mixins.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-bulk-operations
```

Requires Python 3.10+, Django 4.2-5.2, and Django REST Framework 3.14+.

## Quick Start

```python
from drf_bulk_operations import BulkModelViewSet
from rest_framework.routers import DefaultRouter

class ArticleViewSet(BulkModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

router = DefaultRouter()
router.register("articles", ArticleViewSet)
```

See [`docs/quickstart.md`](docs/quickstart.md) for non-atomic mode,
custom lookup fields, and mixing in only the mixins you need.

## Documentation

Full documentation is available at
[Documentation Home Page](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/), including:

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/troubleshooting)

## Contributing

Contributions are welcome — see [Contributing](https://mahmoudgshake.github.io/MahmoudPackages/drf-bulk-operations/contributing).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-bulk-operations/LICENSE).
