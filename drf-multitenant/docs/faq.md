# FAQ

## Why does `Author.objects.all()` sometimes return nothing?

Because no tenant is bound to the current context — `TenantManager`
returns an empty queryset (never an exception) whenever
`get_current_tenant()` is `None`. This happens outside of a request
(a shell session, a management command, a Celery task) unless you bind
one yourself with `tenant_context()`. It's a deliberate, load-bearing
design choice: see [Architecture](architecture.md) for why the manager
must behave this way rather than raising.

## Why doesn't `TenantScopedModel` define the tenant field for me?

Two reasons. First, the field name is configurable
(`MULTITENANT["TENANT_FIELD"]`) precisely because real schemas name it
differently (`organization`, `account`, `company`) — an abstract base
can't guess which name you want. Second, declaring an FK to a specific
model inside a shared abstract base, resolved from a setting at
class-definition time, is fragile across app-loading order in ways that
just writing the field yourself entirely avoids. It costs one extra
line (`tenant = models.ForeignKey(...)`) in exchange for removing both
problems.

## My `PrimaryKeyRelatedField` never validates any pk — why?

You likely declared it explicitly in a serializer's class body:

```python
class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
```

`Author.objects.all()` here is evaluated **once**, at class-definition
(import) time — before any request, and therefore with no tenant bound.
Since `TenantManager` returns an empty queryset with no tenant set, this
field's queryset is frozen empty forever. Let `ModelSerializer`
auto-build the field from your model's `ForeignKey` instead (remove the
explicit declaration, just list the field name in `Meta.fields`) — it
rebuilds the field, and its queryset, fresh on every serializer
instantiation (i.e. every request), correctly scoped each time. See
[Advanced Usage](advanced-usage.md#serializers-with-related-fields-avoid-a-frozen-queryset)
for the pattern to use if you need to customize the field beyond what
auto-generation gives you.

## Can I use more than one tenant model in the same project?

Not directly — `TENANT_MODEL`/`TENANT_FIELD` are single, project-wide
settings. For hierarchical tenancy, scope by the lowest level that needs
isolation and derive parent relationships through it rather than
configuring two independent tenant dimensions.

## Does this work with Django REST Framework's pagination/filtering?

Yes — `TenantManager`'s filter is applied before pagination, ordering,
or `django-filter`-style filtering ever see the queryset, so they only
ever operate on the current tenant's rows. Nothing about tenant scoping
interacts specially with pagination.

## What happens with `bulk_create()` or `queryset.update()`?

They bypass `TenantScopedModel.save()` entirely — Django's bulk
operations don't call `save()` per instance. `queryset.update(...)` is
still scoped (you can only update rows the current tenant's manager
already sees), but `bulk_create([...])` needs the tenant field set
explicitly on every instance you construct. See
[Security](security.md#what-is-enforced-and-where).

## Is this compatible with async views?

Yes — the tenant context is built on `contextvars.ContextVar`
specifically so it propagates correctly across `await` points and
`sync_to_async`/`async_to_sync` boundaries, unlike a thread-local would.
See [Architecture](architecture.md#why-contextvars-not-thread-locals).

## How is this different from django-tenant-schemas / schema-per-tenant approaches?

Schema-per-tenant (separate PostgreSQL schemas or databases) isolates at
the database level and needs per-tenant migrations and connection
routing. `drf-multitenant` is shared-schema: one set of tables, one
migration path, isolation enforced in application code (ORM, serializer,
permission layers) instead of at the database boundary. Shared-schema is
simpler to operate at small-to-medium scale; schema-per-tenant offers
stronger isolation guarantees (a bug literally cannot cross a database
boundary) at the cost of operational complexity. Pick based on your
isolation requirements and operational capacity — this package is for
projects that have decided shared-schema is the right tradeoff.
