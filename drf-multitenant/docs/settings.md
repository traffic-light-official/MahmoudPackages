# Settings Reference

Every key recognized in the `MULTITENANT` Django setting.

```python
MULTITENANT = {
    "TENANT_MODEL": "accounts.Tenant",
    "TENANT_FIELD": "tenant",
    "RESOLVER": "drf_multitenant.resolvers.header_resolver",
    "TENANT_HEADER": "X-Tenant-ID",
    "USER_TENANT_ATTR": "tenant",
    "STRICT": True,
    "CACHE_KEY_PREFIX": "tenant",
    "CACHE_ALIAS": "default",
}
```

Every key is optional except `TENANT_MODEL` when using the default
(header-based) resolver.

| Key | Default | Description |
|---|---|---|
| `TENANT_MODEL` | `None` | `"app_label.ModelName"` identifying your tenant model. Required by `header_resolver`/`subdomain_resolver`; not needed for `user_attr_resolver` or a custom resolver that doesn't query it. |
| `TENANT_FIELD` | `"tenant"` | Name of the FK field on every tenant-scoped model. Read via `getattr(obj, f"{TENANT_FIELD}_id")` throughout the package, so it must match the field name you actually declared. |
| `RESOLVER` | `"drf_multitenant.resolvers.header_resolver"` | Dotted path to a `(request) -> tenant \| None` callable, used by `TenantMiddleware`. |
| `TENANT_HEADER` | `"X-Tenant-ID"` | Header name read by `header_resolver`. |
| `USER_TENANT_ATTR` | `"tenant"` | Attribute name read off `request.user` by `user_attr_resolver`. |
| `STRICT` | `True` | If `True`, `TenantMiddleware` rejects (400) any request with no resolvable tenant, before the view runs. If `False`, the request proceeds with no tenant bound. |
| `CACHE_KEY_PREFIX` | `"tenant"` | Prefix applied to every key `drf_multitenant.cache` builds, before the tenant-id segment. |
| `CACHE_ALIAS` | `"default"` | Name of the `CACHES` backend `get_tenant_cache()` uses when no explicit alias is given. |

## Validation

Every key is validated when first accessed (and re-validated after any
`MULTITENANT` change, including in `@override_settings` blocks in
tests):

- Unknown keys raise `ImproperlyConfigured`, listing the valid ones.
- Wrong value types raise `ImproperlyConfigured`, naming the expected
  type.
- An empty `TENANT_FIELD` raises `ImproperlyConfigured` explicitly (an
  empty field name would silently no-op every scoping check).

## Runtime access

```python
from drf_multitenant.settings import get_setting

get_setting("TENANT_FIELD")  # -> "tenant" (or your override)
```

Raises `KeyError` for an unrecognized key name — this is the same
function every other module in the package uses internally, so it's
always in sync with what's actually consulted.
