# Getting Started

## Install

```bash
pip install drf-multitenant
```

## 1. Configure the middleware and settings

```python
# settings.py
MIDDLEWARE = [
    ...,
    "drf_multitenant.middleware.TenantMiddleware",
]
MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",  # "app_label.ModelName"
}
```

`TenantMiddleware` resolves the current tenant for every request
(header-based by default — see [Configuration](configuration.md) for
subdomain- or user-attribute-based resolution) and binds it to a
request-scoped context.

## 2. Define a tenant-scoped model

```python
# accounts/models.py
class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

# articles/models.py
from drf_multitenant.models import TenantScopedModel

class Article(TenantScopedModel):
    tenant = models.ForeignKey("accounts.Tenant", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
```

Note that `TenantScopedModel` does **not** define the `tenant` field
itself — you do, with whatever FK target and on-delete behavior fits
your schema. This is deliberate: see [FAQ](faq.md) for why.

## 3. Use the tenant-scoped serializer and permission

```python
# articles/serializers.py
from drf_multitenant.serializers import TenantScopedModelSerializer

class ArticleSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "tenant", "title"]
        read_only_fields = ["id", "tenant"]

# articles/views.py
from drf_multitenant.permissions import IsTenantMember

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsTenantMember]
```

That's it: `Article.objects.all()` in the viewset's `queryset` attribute
is automatically scoped to whichever tenant `TenantMiddleware` resolved
for the current request — no explicit `.filter(tenant=...)` anywhere.

## Your first isolated request

```
GET /articles/
X-Tenant-ID: 1
```

returns only tenant 1's articles. The same request with `X-Tenant-ID: 2`
returns only tenant 2's — and neither can see or reference the other's
rows, at the queryset, serializer, or permission layer.

## Next steps

- [Quick Start](quickstart.md) for the full request-flow walkthrough.
- [Configuration](configuration.md) for resolver options (header,
  subdomain, user attribute, or your own).
- [Testing](testing.md) for exercising isolation in your own test suite.
