# Security

## Threat model

The risk this package exists to mitigate: in shared-schema
multi-tenancy, every tenant's rows live in the same tables, so a single
missing `.filter(tenant=...)` anywhere in application code — a new
endpoint, a bugfix, a data export script — can expose or corrupt another
tenant's data. `drf-multitenant`'s core design choice is to make the
*safe* behavior the path of least resistance: `Model.objects.all()`
returns only the current tenant's rows by construction, so a developer
has to actively opt out (`unscoped()`/`all_tenants`) to see across
tenants, rather than actively opt in (`.filter(tenant=...)`) to stay
safe. See [Architecture](architecture.md) for why each layer exists.

## What is enforced, and where

| Layer | Enforces | Bypassed by |
|---|---|---|
| `TenantManager` | Reads via `Model.objects` | `Model.all_tenants`, `.unscoped()`, raw SQL, `apps.get_model()` in migrations |
| `TenantScopedModel.save()` | Writes via the ORM | Bulk operations (`bulk_create`, `.update()`) that don't call `save()` |
| `TenantScopedSerializerMixin` | Serializer-level relation writes | A manually-declared related field built against an unscoped queryset |
| `IsTenantMember` | DRF view/object access | Custom actions or raw SQL that don't call `get_object()`/check permissions |

None of these is a complete guarantee on its own — read the "bypassed
by" column and design your endpoints and background jobs accordingly.
In particular: **bulk operations bypass `save()` entirely.**
`Model.objects.bulk_create([...])` and `queryset.update(...)` do not go
through `TenantScopedModel.save()`, so the auto-assign and mismatch
guard don't apply to them. `TenantManager` still scopes the `queryset`
half of an `.update()` call (you can only update rows already visible to
the current tenant), but `bulk_create()` needs the tenant field set
explicitly on every instance you pass in.

## Unscoped access is logged, not silent

Every `.unscoped()` call (and therefore every `all_tenants` read,
implicitly, since `all_tenants` bypasses the manager the same way)
that goes through `TenantQuerySet.unscoped()` directly logs a `WARNING`
with a full stack trace via the `drf_multitenant` logger. Route this
logger to your monitoring/alerting stack in production — an unexpected
`unscoped()` call in a code path that shouldn't need one is exactly the
kind of thing you want to know about immediately, not discover in an
audit.

## The Django admin is a trusted, cross-tenant surface for superusers

`TenantAdminMixin` deliberately shows superusers every tenant's rows —
the Django admin is assumed to be operated by trusted staff, and
restricting superuser admin access further is out of scope for this
package. If your admin is reachable by non-staff or by tenant-level
users, that's a separate access-control decision to make (e.g. via
Django's own permission system) independent of this package.

## `STRICT = False` widens what's reachable with no tenant

Setting `MULTITENANT["STRICT"] = False` allows requests with no
resolvable tenant to reach your views. Tenant-scoped querysets still
return empty results for such requests (never another tenant's data),
but any endpoint that doesn't explicitly require `IsTenantMember` (or
check `get_current_tenant()` itself) will execute normally with no
tenant bound — make sure that's the behavior you actually want for that
endpoint (a public health-check is fine; a tenant-scoped resource
probably isn't).

## Cache keys are namespaced, not encrypted

`drf_multitenant.cache`'s per-tenant key namespacing prevents accidental
key collisions between tenants sharing one cache backend — it does not
encrypt cache values or restrict backend-level access. If your cache
backend is itself shared infrastructure with broader access than your
application, that's a separate concern this package doesn't address.

## Reporting a vulnerability

See [SECURITY.md](https://github.com/mahmoudgshaker/drf-multitenant/blob/main/SECURITY.md)
in the repository root for the disclosure process.
