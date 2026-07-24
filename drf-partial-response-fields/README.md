# drf-partial-response-fields

[![CI](https://github.com/mahmoudgshaker/drf-partial-response-fields/actions/workflows/ci.yml/badge.svg)](https://github.com/mahmoudgshaker/drf-partial-response-fields/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/drf-partial-response-fields.svg)](https://pypi.org/project/drf-partial-response-fields/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-partial-response-fields.svg)](https://pypi.org/project/drf-partial-response-fields/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

GraphQL-like sparse fieldsets for Django REST Framework — with automatic
`select_related` / `prefetch_related` / `only()` query optimization, so
requesting fewer fields also means fewer queries and less data transferred.

```
GET /api/articles/1/?fields=title,author(name,email),tags(label)
```

```json
{
  "title": "Shipping Faster with Sparse Fieldsets",
  "author": { "name": "Ada Lovelace", "email": "ada@example.com" },
  "tags": [{ "label": "performance" }, { "label": "django" }]
}
```

## Why

Fetching the full representation of a resource is wasteful when a client
only needs a few fields — especially on mobile, in list views, or in
BFF-style aggregation layers. Most "sparse fieldset" implementations for
DRF only filter the *serializer output* and leave the ORM query untouched,
so you save bytes on the wire but still pay for every join and every
`SerializerMethodField` query. This package does both: it filters what gets
serialized **and** rewrites the queryset so the database only does the work
that's actually needed.

## Features

- **Nested field selection**: `?fields=title,author(name,email)`
- **Deep nesting**: any depth, e.g. `author(company(name,address(city)))`
- **Exclusion**: `?fields=-internal_notes,-legacy_id`
- **Aliasing**: `?fields=publishedAt:created_at`
- **Wildcards**: `?fields=*` (explicit "no restriction")
- **Works with**: `ModelSerializer`, nested serializers, `SerializerMethodField`,
  pagination, `ViewSet`/`GenericAPIView`/`APIView`, the Browsable API, and
  OpenAPI schema generation (via `drf-spectacular`)
- **Automatic query optimization**: `select_related`, `prefetch_related`
  (including recursively-optimized nested `Prefetch` querysets), and
  `only()` are derived from the requested fields — see
  [`docs/performance.md`](docs/performance.md) for measured query-count
  reductions.
- **Safe by default**: unrequested `SerializerMethodField`s are never
  invoked, so expensive computed fields only cost what they cost when a
  client actually asks for them.
- **Fully typed**, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-partial-response-fields

# with OpenAPI schema support
pip install drf-partial-response-fields[openapi]
```

Requires Python 3.10+, Django 4.2+, and Django REST Framework 3.14+.

## Quick Start

```python
# serializers.py
from rest_framework import serializers
from drf_partial_response_fields import PartialFieldsModelSerializer


class AuthorSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class ArticleSerializer(PartialFieldsModelSerializer):
    author = AuthorSerializer()

    class Meta:
        model = Article
        fields = ["id", "title", "body", "author"]
```

```python
# views.py
from rest_framework import viewsets
from drf_partial_response_fields import PartialResponseMixin


class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

That's it — `GET /articles/?fields=title,author(name)` now returns only
`title` and `author.name`, and the underlying queryset automatically gets
`select_related("author").only("id", "title", "author__id", "author__name")`.

See [`docs/quickstart.md`](docs/quickstart.md) and
[`docs/advanced-usage.md`](docs/advanced-usage.md) for aliasing, exclusion,
`SerializerMethodField` optimization hints, and plain-`APIView` integration.

## Documentation

Full documentation is available at
<https://mahmoudgshaker.github.io/drf-partial-response-fields/>, including:

- [Getting Started](docs/getting-started.md)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md) / [Settings](docs/settings.md)
- [Quick Start](docs/quickstart.md)
- [Advanced Usage](docs/advanced-usage.md)
- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Examples](docs/examples.md)
- [Common Patterns](docs/common-patterns.md)
- [Performance](docs/performance.md)
- [Security](docs/security.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
