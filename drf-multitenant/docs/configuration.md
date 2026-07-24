# Configuration

All configuration lives under a single Django setting, `MULTITENANT`, a
dict of overrides merged on top of sensible defaults. See
[Settings](settings.md) for the exhaustive key-by-key reference — this
page covers the two decisions you actually need to make: **how to
identify your tenant model**, and **how to resolve the current tenant
from a request**.

## The tenant model

```python
MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
}
```

Required by the built-in `header_resolver` and `subdomain_resolver`
(they need to look up a tenant instance by id/slug). Not required if you
only use `user_attr_resolver` or write your own resolver that doesn't
need to query it.

## Choosing a resolver

`MULTITENANT["RESOLVER"]` is a dotted path to a `(request) -> tenant |
None` callable. Three are built in:

```python
# Header-based (default): X-Tenant-ID: 42
MULTITENANT = {"RESOLVER": "drf_multitenant.resolvers.header_resolver"}

# Subdomain-based: acme.example.com -> Tenant.objects.get(slug="acme")
MULTITENANT = {"RESOLVER": "drf_multitenant.resolvers.subdomain_resolver"}

# User-attribute-based: request.user.tenant
MULTITENANT = {"RESOLVER": "drf_multitenant.resolvers.user_attr_resolver"}
```

Write your own with the same signature for anything else (an API key
lookup, a JWT claim, a path prefix):

```python
def api_key_resolver(request):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    return Tenant.objects.filter(api_keys__key=api_key).first()
```

## The tenant field name

`MULTITENANT["TENANT_FIELD"]` (default `"tenant"`) is the name of the FK
field every tenant-scoped model defines. Override it if your schema
uses a different name:

```python
MULTITENANT = {"TENANT_FIELD": "organization"}

class Article(TenantScopedModel):
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE)
```

## Strict mode

`MULTITENANT["STRICT"]` (default `True`) controls what happens when no
tenant can be resolved for a request: `TenantMiddleware` rejects it with
an HTTP 400 before the view runs at all. Set it to `False` to let such
requests through — tenant-scoped managers then return empty querysets,
so a public, non-tenant-scoped endpoint doesn't need special-casing, but
views that *do* need a tenant must check for it themselves (e.g. via
`IsTenantMember`).

## Per-environment overrides

A common pattern is header-based resolution in development/testing
(easy to set manually with curl or an API client) and subdomain-based
resolution in production:

```python
# settings/dev.py
MULTITENANT = {"TENANT_MODEL": "accounts.Tenant", "RESOLVER": "drf_multitenant.resolvers.header_resolver"}

# settings/production.py
MULTITENANT = {"TENANT_MODEL": "accounts.Tenant", "RESOLVER": "drf_multitenant.resolvers.subdomain_resolver"}
```
