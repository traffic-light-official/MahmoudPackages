# Architecture

## The safe default: empty, never partial, never crashed

`TenantManager.get_queryset()` has exactly two outcomes: filtered to the
current tenant, or empty. It never returns unfiltered rows, and — after
an early design mistake caught in this package's own test suite — it
never raises either.

The first version of this package *did* raise `NoTenantSetError` from
inside the manager when no tenant was bound (gated by a `STRICT`
setting). That's intuitively appealing: fail loudly rather than
silently return nothing. It broke on contact with completely ordinary
DRF code:

```python
class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
```

`Author.objects.all()` here is evaluated **once**, in the class body, at
**import time** — long before any request, and therefore with no tenant
bound. A manager that raises when unscoped would crash the entire
process on startup. The fix was to make `TenantManager` always
construction-safe: build the queryset lazily-filtered when a tenant is
bound, and `.none()` (a real, valid, zero-row Django queryset — no
exception, no special-casing) when it isn't. Constructing
`Model.objects.all()` must be safe at any time, including before any
tenant has ever existed.

Enforcing that a tenant *must* be resolvable moved to where it actually
belongs: `TenantMiddleware`, at the start of request handling — the one
place where "there is no context yet" and "there should be a context by
now" are genuinely different situations. See
[FAQ](faq.md#why-does-authorobjectsall-sometimes-return-nothing) for the
concrete symptom this produces if you don't know about it.

## Why `contextvars`, not thread-locals

A thread-local current-tenant would silently break under ASGI: an
`async def` view's code can resume on a different OS thread than it
started on after an `await`, and `sync_to_async`/`async_to_sync`
boundaries move work between threads explicitly. `contextvars.ContextVar`
is designed exactly for this — its value follows the logical
task/coroutine, not the OS thread, and is automatically. This is also
why `tenant_context()` is a context manager built on
`ContextVar.set()`/`.reset()` rather than a plain module-level variable.

## Defense in depth, not one gate

Isolation is enforced independently at four layers, deliberately
redundant:

1. **Queryset** (`TenantManager`) — the primary, load-bearing layer.
   Every read goes through it by default.
2. **Serializer** (`TenantScopedSerializerMixin.validate()`) — catches
   writes that reference another tenant's object by id, for the case
   where a related field's queryset *wasn't* auto-scoped (a manually
   declared field using `all_tenants`, or a related model that isn't
   itself tenant-scoped).
3. **Model** (`TenantScopedModel.save()`) — catches saves below the
   serializer layer entirely (a management command, a signal handler, a
   data migration) by auto-assigning the current tenant and rejecting a
   mismatch.
4. **Permission** (`IsTenantMember`) — an explicit, request-level check
   for object access paths that don't go through a tenant-scoped
   queryset at all (a custom action operating on a raw pk from the
   request body).

None of these four is redundant in practice: each closes a path the
others don't cover. See [Testing](testing.md) for how this package's own
suite exercises each layer independently, including the case where the
serializer-level check is the *only* thing catching a cross-tenant
reference (queryset scoping deliberately bypassed via `all_tenants`).

## `unscoped()` as a logged, named escape hatch

Cross-tenant access is sometimes legitimate (an admin dashboard, a data
migration). Rather than making the "safe" queryset hard to bypass,
`unscoped()` makes bypassing it *loud*: every call logs a `WARNING` with
a full stack trace via the `drf_multitenant` logger, so an accidental or
unreviewed cross-tenant query is visible in production logs and
greppable (`grep -rn "\.unscoped()"`) in code review — a stricter bar
than a silent `Model.objects.all()` would ever get past.

## The admin bypasses the default manager entirely

`TenantAdminMixin.get_queryset()` doesn't call
`super().get_queryset()` — it builds directly from `self.model.all_tenants`.
This is intentional: the admin needs to decide scoping itself
(unfiltered for superusers, filtered otherwise), and going through
`TenantManager` first would apply a filter the admin then has to
partially undo for superusers, plus risk an empty result if no tenant
happens to be bound for that particular admin request.

## Why the tenant FK field isn't provided automatically

`TenantScopedModel` deliberately does not declare a `tenant` field for
you, even though it could (Django supports lazy string FK targets, the
same trick `AUTH_USER_MODEL` uses). Two reasons: the field name is
configurable (`TENANT_FIELD`) precisely because existing schemas name it
differently (`organization`, `account`, `company`), and a fixed FK
target baked into an abstract base would need to know your tenant model
at class-definition time in a way that's fragile across app-loading
order. Declaring the field yourself is one extra line and removes both
problems.
