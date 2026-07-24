# drf-multitenant

[![CI](https://github.com/mahmoudgshaker/drf-multitenant/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mahmoudgshaker/drf-multitenant/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/drf-multitenant.svg)](https://pypi.org/project/drf-multitenant/)
[![Python versions](https://img.shields.io/pypi/pyversions/drf-multitenant.svg)](https://pypi.org/project/drf-multitenant/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Shared-schema multi-tenancy for Django REST Framework: one set of
database tables, automatic row-level isolation enforced at every layer
— queryset, serializer, permission, cache, and admin — so a single
missed `.filter(tenant=...)` call anywhere in application code can't
leak data across tenants.

```python
from drf_multitenant.models import TenantScopedModel

class Article(TenantScopedModel):
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

# Anywhere in your codebase:
Article.objects.all()  # automatically scoped to the current request's tenant
```

## Why

Shared-schema multi-tenancy is efficient (one schema, one migration
path, no per-tenant database provisioning) but famously easy to get
wrong: one forgotten `.filter(tenant=request.tenant)` and tenant A can
read or write tenant B's data. `drf-multitenant` makes the *safe*
default (`Model.objects.all()` returns only the current tenant's rows)
so the unsafe behavior — reading across tenants — requires an explicit,
greppable, logged opt-in (`Model.objects.unscoped()`), not the reverse.

## Features

- **Automatic queryset scoping**: `TenantManager` filters every query to
  the current tenant; `unscoped()` is the explicit, logged escape hatch.
- **Async-safe tenant context**: built on `contextvars`, correct under
  ASGI and `sync_to_async`/`async_to_sync`, not just thread-locals.
- **Save-time enforcement**: `TenantScopedModel.save()` auto-assigns the
  current tenant on create and rejects saving a row under the wrong one.
- **Serializer-layer enforcement**: `TenantScopedSerializerMixin` blocks
  writes that would relate an object to another tenant's data.
- **DRF permission**: `IsTenantMember` for object-level defense in depth.
- **Middleware with pluggable resolution**: header, subdomain, or
  user-attribute tenant resolution out of the box; write your own with
  the same one-function signature.
- **Per-tenant caching**: namespaced cache keys on top of Django's own
  cache framework — no new backend required.
- **Admin integration**: `TenantAdminMixin` scopes the Django admin to
  the current tenant (superusers see everything).
- **Testing utilities**: `as_tenant()`, `as_no_tenant()`, and
  `assert_no_cross_tenant_leak()` for exercising and verifying isolation
  in your own test suite.
- Fully typed, PEP 561 compatible, `mypy --strict` clean.

## Installation

```bash
pip install drf-multitenant
```

## Quick Start

```python
# settings.py
MIDDLEWARE = [
    ...,
    "drf_multitenant.middleware.TenantMiddleware",
]
MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
}

# models.py
from drf_multitenant.models import TenantScopedModel

class Article(TenantScopedModel):
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

# serializers.py
from drf_multitenant.serializers import TenantScopedModelSerializer

class ArticleSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "tenant", "title"]
        read_only_fields = ["id", "tenant"]

# views.py
from drf_multitenant.permissions import IsTenantMember

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsTenantMember]
```

## Documentation

Full documentation: <https://mahmoudgshaker.github.io/drf-multitenant/>

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
