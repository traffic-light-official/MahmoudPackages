# Advanced Usage

## Background tasks and management commands

`TenantMiddleware` only runs for HTTP requests. A Celery task, a
management command, or a signal handler that touches tenant-scoped
models needs to bind the tenant itself:

```python
from drf_multitenant.context import tenant_context

@shared_task
def send_weekly_digest(tenant_id: int) -> None:
    tenant = Tenant.objects.get(pk=tenant_id)
    with tenant_context(tenant):
        for article in Article.objects.filter(published_at__gte=last_week):
            ...
```

Without this, `Article.objects.all()` inside the task would return an
empty queryset (no tenant bound) rather than raising — see
[Architecture](architecture.md) for why that's the deliberately safe
default.

## Cross-tenant reporting/admin views

Use the `all_tenants` manager explicitly for legitimate cross-tenant
access (an internal analytics dashboard, a support tool):

```python
def tenant_signup_counts():
    return (
        Article.all_tenants.values("tenant")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
```

Every `.unscoped()` call (equivalent to using `all_tenants`) is logged
at `WARNING` level with a stack trace, so unexpected cross-tenant access
elsewhere in the codebase is visible in your logs and greppable in code
review — see [Security](security.md).

## Combining `IsTenantMember` with other permissions

`IsTenantMember` composes normally with DRF's `AND`/`OR` permission
composition:

```python
permission_classes = [IsAuthenticated & IsTenantMember]
```

or per-action:

```python
def get_permissions(self):
    if self.action == "destroy":
        return [IsAuthenticated(), IsTenantMember(), IsAdminUser()]
    return [IsAuthenticated(), IsTenantMember()]
```

## Writing your own resolver

Any `(request) -> tenant | None` callable works — nothing needs to
subclass anything:

```python
# resolvers.py
from django.core.exceptions import ObjectDoesNotExist

def jwt_claim_resolver(request):
    claims = getattr(request, "auth", None)  # e.g. set by a JWT auth class
    if not claims or "tenant_id" not in claims:
        return None
    try:
        return Tenant.objects.get(pk=claims["tenant_id"])
    except ObjectDoesNotExist:
        return None
```

```python
MULTITENANT = {"RESOLVER": "myproject.resolvers.jwt_claim_resolver"}
```

## Serializers with related fields: avoid a frozen queryset

A `PrimaryKeyRelatedField` declared explicitly in a serializer's class
body with `queryset=Model.objects.all()` builds that queryset **once**,
at import time — before any tenant context exists. Since
`TenantManager` returns an empty queryset with no tenant bound, that
field would be permanently unusable. Let `ModelSerializer` auto-build
related fields from your model's `ForeignKey` instead (it rebuilds them
fresh per serializer instantiation, i.e. per request) — see
[FAQ](faq.md) for the full explanation, and
[Architecture](architecture.md) for why the manager behaves this way at
all.

If you must declare a related field explicitly (e.g. to customize
`label` or add a custom validator), rebuild its queryset dynamically in
`get_fields()` instead of the class body:

```python
class ArticleSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "tenant", "reviewer", "title"]

    def get_fields(self):
        fields = super().get_fields()
        fields["reviewer"] = serializers.PrimaryKeyRelatedField(
            queryset=Reviewer.objects.all(),  # re-evaluated per instantiation
            required=False,
        )
        return fields
```

## Multiple tenant models / hierarchical tenancy

`TENANT_MODEL` and `TENANT_FIELD` are both single, package-wide
settings — the package assumes one tenant model and one field name
across your project. For hierarchical tenancy (organizations containing
teams, each independently scoped), scope by the *lowest* level that
needs isolation and derive the parent relationship through it, rather
than trying to configure two independent tenant dimensions.
