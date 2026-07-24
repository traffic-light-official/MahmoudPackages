# drf-multitenant

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

Full documentation: <https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/>

- [Getting Started](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/getting-started)
- [Installation](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/installation)
- [Configuration](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/configuration) / [Settings](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/settings)
- [Quick Start](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/quickstart)
- [Advanced Usage](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/advanced-usage)
- [Architecture](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/architecture)
- [API Reference](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/api-reference)
- [Examples](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/examples)
- [Common Patterns](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/common-patterns)
- [Performance](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/performance)
- [Security](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/security)
- [Testing](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/testing)
- [Deployment](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/deployment)
- [FAQ](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/faq)
- [Troubleshooting](https://mahmoudgshake.github.io/MahmoudPackages/drf-multitenant/troubleshooting)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-multitenant/CONTRIBUTING.md).

## License

MIT — see [LICENSE](https://github.com/MahmoudGShake/MahmoudPackages/blob/master/drf-multitenant/LICENSE).
