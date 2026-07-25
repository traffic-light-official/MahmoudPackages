# Performance

## One round trip instead of N

The entire point of this package is replacing N HTTP round trips with
one - for latency-bound clients (mobile apps, scripts talking to a
remote API over the internet), this dominates every other
consideration below. A batch of 100 items that would each cost 50ms of
network latency alone becomes one request instead of a 5-second
sequential loop.

## Per-item queries, not bulk SQL

Every item still goes through the normal serializer/model `.save()`
path - one `INSERT`/`UPDATE`/`DELETE` statement per item, not Django's
`bulk_create()`/`bulk_update()` (which skip signals, `save()`
overrides, and `auto_now` handling, none of which this package can
safely assume are irrelevant to your models). This means a bulk request
runs proportionally more SQL than a single-object request, not O(1)
SQL - a batch of 500 items issues roughly 500 `INSERT`s.

If your model has no custom `save()` logic and no signals that must
fire, and you need to bulk-create at a scale where per-row `INSERT`s
become the bottleneck, that's a case for calling
`Model.objects.bulk_create()` directly in your own view rather than
this package - see [FAQ](faq.md#why-doesnt-this-package-use-djangos-own-bulk_createbulk_update).

## Atomic mode holds one transaction open for the whole batch

A large atomic batch means a single, long-lived database transaction -
proportionally more lock contention and a longer-lived connection than
the equivalent number of separate single-object requests. `MAX_BATCH_SIZE`
exists specifically to bound this: pick a value where "worst case, this
transaction is open for X seconds" is acceptable for your database's
concurrent load, not just "large enough that legitimate use cases never
hit it." See [Security](security.md).

## Non-atomic mode's per-item savepoints have a small, fixed overhead

Each item wrapped in its own `transaction.atomic()` savepoint costs one
extra `SAVEPOINT`/`RELEASE SAVEPOINT` pair of statements compared to a
single un-savepointed `.save()` - negligible next to the cost of the
actual `INSERT`/`UPDATE`/`DELETE` itself, and a fixed cost regardless
of batch size (it doesn't compound - it's O(1) extra per item, not
O(n) overall).

## `bulk_update`/`bulk_destroy` resolve every instance in one query

`_resolve_instances`/`_resolve_instances_by_id` fetch every item's
target object with a single `queryset.filter(<field>__in=[...])` query,
not one query per item - a batch of 100 update/destroy items issues one
`SELECT ... WHERE id IN (...)` to resolve all of them, then one
`UPDATE`/`DELETE` per item during the write phase itself (Django has no
generic "bulk update N different rows with N different values each" SQL
primitive, so the per-row write cost is unavoidable with this
package's approach).

## Recommended: add `select_related`/`prefetch_related` to `queryset` as usual

`bulk_update`/`bulk_destroy`'s resolution query benefits from the exact
same queryset optimizations a single-object `retrieve`/`update` would -
`queryset = Article.objects.select_related("author").all()` avoids N+1
queries the same way it always does, since the resolution step is a
normal Django queryset under the hood.
