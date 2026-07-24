# Performance

## The tenant filter is a normal indexed WHERE clause

`TenantManager` adds exactly one `.filter(tenant=...)` (or your
configured `TENANT_FIELD`) to every query — the same thing you'd write
by hand. There's no additional query, no post-fetch filtering in
Python, and no ORM-level overhead beyond what a plain `.filter()` call
already costs. **Index the tenant FK column** (Django does this
automatically for `ForeignKey` fields) — for any table that grows large
per tenant, a composite index leading with the tenant column
(`(tenant_id, created_at)`, `(tenant_id, status)`, etc., matching your
common query patterns) matters far more than anything this package
does.

## Context lookups are O(1) and allocation-free per access

`get_current_tenant()` is a single `ContextVar.get()` call — no
dictionary lookup, no thread-local overhead, no I/O. Calling it
thousands of times per request (which `TenantManager` effectively does,
once per queryset construction) has no measurable cost.

## `TenantMiddleware` runs the resolver exactly once per request

Resolution happens once, in `TenantMiddleware.__call__`, and the result
is bound to the context for the request's entire duration — it is not
re-resolved per query. The cost of the resolver you choose (a header
read is O(1); `subdomain_resolver`/`header_resolver` each do one
indexed lookup against your tenant table) is paid once, not once per
queryset.

## Per-tenant caching adds one string format, no extra round-trip

`tenant_cache_key()` is pure string formatting — `TenantCache.get()`/`.set()`
make exactly the same number of backend calls as calling the underlying
cache directly; only the key differs.

## `unscoped()` costs a log call

Every `.unscoped()` invocation logs a `WARNING` with `stack_info=True` —
by design (see [Architecture](architecture.md)), so misuse is visible.
`stack_info=True` does have a real (if small) cost, since Python must
capture and format the current stack. This is intentional: `unscoped()`
should be rare enough that this cost never shows up in a profile; if
it's showing up, that's itself a signal you're using the escape hatch
somewhere in a hot path where you should probably be using `objects`
instead.

## No N+1 introduced by tenant scoping

`TenantManager`'s filter composes normally with `select_related()`/
`prefetch_related()` — it's applied to the base queryset before any
further chaining, exactly like a `.filter()` you'd write yourself:

```python
Article.objects.select_related("author").filter(status="published")
# -> WHERE tenant_id = %s AND status = %s, with the author JOIN, as expected
```
