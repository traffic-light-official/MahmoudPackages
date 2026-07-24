# drf-multitenant

Shared-schema multi-tenancy for Django REST Framework.

Every tenant shares the same database tables — no per-tenant schemas or
databases to provision — and row-level isolation is enforced
automatically at every layer: the ORM (`TenantManager`), the serializer
(`TenantScopedSerializerMixin`), the permission (`IsTenantMember`), the
cache (`drf_multitenant.cache`), and the Django admin
(`TenantAdminMixin`). A single missed `.filter(tenant=...)` call
anywhere in application code can't leak data across tenants, because
`Model.objects.all()` is *never* actually unfiltered.

## The core idea

```python
from drf_multitenant.models import TenantScopedModel

class Article(TenantScopedModel):
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

# Anywhere in your codebase, in any view, task, or shell session:
Article.objects.all()  # only ever returns the current tenant's rows
```

The unsafe operation — reading across tenants — requires an explicit,
greppable, logged opt-in: `Article.objects.unscoped()`.

## What it does

- Resolves the current tenant per request (header, subdomain, or user
  attribute) and binds it to an async-safe, `contextvars`-based context.
- Filters every ORM query automatically to that tenant.
- Auto-assigns the tenant on model creation and rejects saving a row
  under the wrong one.
- Blocks serializer writes that would relate an object to another
  tenant's data.
- Namespaces cache keys per tenant on top of Django's own cache
  framework.
- Scopes the Django admin to the current tenant for non-superusers.
- Provides test helpers for exercising and asserting isolation.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Wiring up resolution and models? See
  [Quick Start](quickstart.md) and [Configuration](configuration.md).
- Want to understand why the design works the way it does (and the
  serializer gotcha it specifically avoids)? See
  [Architecture](architecture.md) and [FAQ](faq.md).
- Looking for a specific class or function? See
  [API Reference](api-reference.md).
