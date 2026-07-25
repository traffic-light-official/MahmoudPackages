# FAQ

## Why isn't there one `/bulk/` endpoint with four HTTP methods?

Because DRF's router doesn't support it safely for independently
composable mixins - see
[Architecture](architecture.md#why-every-bulk-action-has-its-own-dedicated-url)
for the exact mechanism and the empirical proof.

## Why doesn't this package use Django's own `bulk_create`/`bulk_update`?

`QuerySet.bulk_create()`/`bulk_update()` skip `Model.save()` entirely -
which means no custom `save()` overrides, no `pre_save`/`post_save`
signals, and no `auto_now`/`auto_now_add` handling (unless you pass
`update_fields` carefully and your model doesn't rely on `save()` logic
at all). This package can't safely assume that's fine for your models
in general, so every item goes through the normal serializer →
`.save()` path, exactly like a single-object request would - one SQL
statement per item, not a single bulk statement. If your model has no
such logic and you're operating at a scale where per-row `INSERT`s are
the bottleneck, calling `bulk_create()`/`bulk_update()` directly in
your own view is the right tool, not this package.

## Can I use a different atomic/non-atomic mode per viewset?

Not currently - `ATOMIC` is one project-wide `BULK_OPERATIONS` setting.
If you need this, the simplest workaround is overriding the relevant
`bulk_*` method on that one viewset to wrap it with
`override_settings`-equivalent logic, or open an issue describing the
use case (see [Contributing](contributing.md)).

## Does non-atomic mode guarantee items are processed in order?

Yes - both modes iterate the submitted list in order, and the `index`
in every result corresponds to the item's position in the request
body. This matters if later items in a non-atomic batch depend on
earlier ones having already been committed (e.g. a within-batch
duplicate check - see
[Architecture](architecture.md#why-a-within-batch-duplicate-title-behaves-differently-in-each-mode)).

## What happens if I submit an empty list?

Every action accepts an empty list and returns success immediately
(`201`/`200`/`204` with an empty body/list) - there's nothing to
validate or process, so nothing can fail.

## Can `bulk_update` change an object's primary key?

No - the lookup field (`id` by default) identifies *which* object each
item updates; if you also include it in the update data, DRF's
`ModelSerializer` treats the primary key field as read-only by default,
so it's silently ignored as an input, exactly like a single-object
`update` would.

## Does this work with nested/related serializers?

Yes, unchanged - `get_serializer()` is called exactly as a single-object
view would call it, so any custom serializer (nested writes, custom
`create()`/`update()` overrides) works the same way it already does for
your viewset's single-object actions. This package doesn't add or
require any special serializer behavior.

## Can I bulk-create objects that reference each other (e.g. a self-referential FK)?

Not within the same batch - each item is validated and saved
independently (or, in atomic mode, validated together but still saved
one at a time), so an item referencing another item's not-yet-created
ID in the same batch fails validation (the referenced ID doesn't exist
yet). Create the referenced objects first, in an earlier request.

## Is there a bulk `GET`/list-by-IDs endpoint?

No - listing by ID is already well-served by DRF's own filtering
(`?id__in=1,2,3` via a filter backend, or a custom `get_queryset()`
override) since it's read-only and doesn't need per-item validation,
transactions, or a partial-success report. This package focuses on the
write operations that actually need those.
