# Examples

Runnable/adaptable snippets live in [`examples/`](https://github.com/mahmoudgshaker/drf-multitenant/tree/main/examples)
in the repository. This page walks through the same scenarios inline.

## A minimal tenant-scoped app

```python
# examples/minimal_app/models.py
from django.db import models
from drf_multitenant.models import TenantScopedModel

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

class Project(TenantScopedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
```

```python
# examples/minimal_app/serializers.py
from drf_multitenant.serializers import TenantScopedModelSerializer
from .models import Project

class ProjectSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "tenant", "name"]
        read_only_fields = ["id", "tenant"]
```

```python
# examples/minimal_app/views.py
from rest_framework import viewsets
from drf_multitenant.permissions import IsTenantMember
from .models import Project
from .serializers import ProjectSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsTenantMember]
```

## Subdomain-based resolution

```python
# examples/subdomain_settings.py
MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
    "RESOLVER": "drf_multitenant.resolvers.subdomain_resolver",
}
```

Requires your `Tenant` model to have a `slug` field, and each tenant to
be reachable at `<slug>.yourdomain.com`.

## A background task binding its own tenant

```python
# examples/tasks.py
from celery import shared_task
from drf_multitenant.context import tenant_context
from accounts.models import Tenant
from projects.models import Project

@shared_task
def archive_stale_projects(tenant_id: int) -> None:
    tenant = Tenant.objects.get(pk=tenant_id)
    with tenant_context(tenant):
        Project.objects.filter(updated_at__lt=cutoff()).update(archived=True)
```

## Per-tenant caching

```python
# examples/cached_view.py
from drf_multitenant.cache import get_tenant_cache

def expensive_dashboard_stats():
    cache = get_tenant_cache()
    stats = cache.get("dashboard-stats")
    if stats is None:
        stats = compute_stats()  # scoped to the current tenant already
        cache.set("dashboard-stats", stats, timeout=300)
    return stats
```

## Admin integration

```python
# examples/admin.py
from django.contrib import admin
from drf_multitenant.admin import TenantAdminMixin
from .models import Project

@admin.register(Project)
class ProjectAdmin(TenantAdminMixin):
    list_display = ["name", "tenant"]
```

## Testing isolation

```python
# examples/test_isolation.py
import pytest
from drf_multitenant.testing import as_tenant, assert_no_cross_tenant_leak
from .models import Project

@pytest.mark.django_db
def test_projects_are_isolated(tenant_a, tenant_b):
    with as_tenant(tenant_a):
        Project.objects.create(name="A's project")
    with as_tenant(tenant_b):
        Project.objects.create(name="B's project")

    with as_tenant(tenant_a):
        rows = list(Project.objects.all())
    assert len(rows) == 1
    assert_no_cross_tenant_leak(rows, tenant_a)
```

See [Common Patterns](common-patterns.md) for more real-world recipes.
