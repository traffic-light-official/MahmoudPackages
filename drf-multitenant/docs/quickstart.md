# Quick Start

A complete, minimal setup from zero to an isolated API.

## 1. The tenant model

```python
# accounts/models.py
from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
```

## 2. Settings

```python
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    ...,
    "drf_multitenant.middleware.TenantMiddleware",
]

MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
}
```

## 3. A tenant-scoped model

```python
# articles/models.py
from django.db import models
from drf_multitenant.models import TenantScopedModel

class Article(TenantScopedModel):
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default="")
```

## 4. Serializer and viewset

```python
# articles/serializers.py
from drf_multitenant.serializers import TenantScopedModelSerializer

class ArticleSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "tenant", "title", "body"]
        read_only_fields = ["id", "tenant"]

# articles/views.py
from rest_framework import viewsets
from drf_multitenant.permissions import IsTenantMember

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsTenantMember]
```

## 5. Try it

```bash
# tenant 1 creates an article
curl -X POST http://localhost:8000/articles/ \
  -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"title": "Hello"}'

# tenant 1 can see it
curl http://localhost:8000/articles/ -H "X-Tenant-ID: 1"
# -> [{"id": 1, "tenant": 1, "title": "Hello", "body": ""}]

# tenant 2 cannot
curl http://localhost:8000/articles/ -H "X-Tenant-ID: 2"
# -> []

# no tenant header at all: rejected before the view even runs
curl http://localhost:8000/articles/
# -> 400 {"detail": "No tenant could be resolved for this request."}
```

## 6. Test it

```python
# tests/test_articles.py
from drf_multitenant.testing import as_tenant, assert_no_cross_tenant_leak

def test_articles_are_isolated(client, tenant_a, tenant_b):
    with as_tenant(tenant_a):
        Article.objects.create(title="A's article")
    with as_tenant(tenant_b):
        Article.objects.create(title="B's article")

    with as_tenant(tenant_a):
        rows = list(Article.objects.all())
    assert_no_cross_tenant_leak(rows, tenant_a)
```

See [Testing](testing.md) for the full set of test helpers, and
[Common Patterns](common-patterns.md) for subdomain-based resolution,
per-tenant caching, and admin integration.
