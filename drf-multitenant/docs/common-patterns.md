# Common Patterns

## Subdomain-based SaaS

```python
MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
    "RESOLVER": "drf_multitenant.resolvers.subdomain_resolver",
}
```

Requires a `slug` field on your tenant model and DNS/routing that sends
`*.yourdomain.com` to your app. Combine with `ALLOWED_HOSTS` covering
the wildcard subdomain.

## API-key-per-tenant

```python
def api_key_resolver(request):
    key = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not key:
        return None
    api_key = ApiKey.objects.filter(key=key).select_related("tenant").first()
    return api_key.tenant if api_key else None
```

```python
MULTITENANT = {"RESOLVER": "myproject.resolvers.api_key_resolver"}
```

## Superuser "view as tenant" for support

```python
def support_resolver(request):
    if request.user.is_superuser and "X-Impersonate-Tenant" in request.headers:
        return Tenant.objects.filter(pk=request.headers["X-Impersonate-Tenant"]).first()
    return header_resolver(request)  # fall back to the normal path
```

## Free/public endpoints alongside tenant-scoped ones

Set `STRICT = False` so the middleware doesn't reject every request
with no tenant, then gate tenant-scoped views explicitly:

```python
MULTITENANT = {"TENANT_MODEL": "accounts.Tenant", "STRICT": False}

class PublicStatusView(APIView):
    permission_classes = [AllowAny]  # no IsTenantMember — works with no tenant

class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTenantMember]  # requires a resolved tenant
```

## Per-tenant rate limiting

Combine `drf_multitenant.cache`'s per-tenant namespacing with your own
throttle class (or a separate rate-limiting package) keyed off
`request.tenant`:

```python
from rest_framework.throttling import SimpleRateThrottle

class PerTenantThrottle(SimpleRateThrottle):
    scope = "tenant"

    def get_cache_key(self, request, view):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return None  # no tenant, no throttling (or reject via IsTenantMember instead)
        return self.cache_format % {"scope": self.scope, "ident": tenant.pk}
```

## Seeding data in tests and fixtures

```python
@pytest.fixture
def acme(db):
    return Tenant.objects.create(name="Acme", slug="acme")

@pytest.fixture
def acme_articles(acme):
    with tenant_context(acme):
        return [Article.objects.create(title=f"Article {i}") for i in range(3)]
```

## Data migrations touching tenant-scoped models

Bind a tenant explicitly, or use `all_tenants` for a migration that
intentionally spans every tenant:

```python
def migrate_forward(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    # Data migrations bypass this package's managers entirely (apps.get_model
    # returns historical, unmanaged model classes) — the TENANT_FIELD is
    # just a normal column here; filter/update explicitly per tenant if needed.
    Article.objects.filter(status="draft").update(status="pending_review")
```
