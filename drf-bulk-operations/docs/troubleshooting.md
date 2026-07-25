# Troubleshooting

## A `PUT`/`PATCH`/`DELETE` bulk request returns `405 Method Not Allowed`

If you've written a *custom* mixin combining one of this package's
actions with your own `@action`-decorated method, check whether they
share a `url_path` - DRF's router creates one URL pattern per action,
and two actions sharing a path silently shadow each other (only the
first-registered one is ever reachable). This package's own four
mixins each use a distinct path (`bulk`, `bulk-update`,
`bulk-partial-update`, `bulk-delete`) specifically to avoid this - see
[Architecture](architecture.md#why-every-bulk-action-has-its-own-dedicated-url).
If you're only using this package's own mixins unmodified, this
shouldn't happen; if it does, please report it (see
[Contributing](contributing.md)).

## `400 Bad Request` with `"Expected a list of items, got dict"`

The request body is a JSON object (`{...}`), not an array (`[...]`) -
every bulk action expects a top-level list, even for a single item
(`[{...}]`, not `{...}`).

## `400 Bad Request` with `"Batch of N item(s) exceeds the maximum of M item(s)"`

The submitted list is longer than `MAX_BATCH_SIZE` - either split the
request into smaller batches, or raise the setting if your use case
genuinely needs larger batches (see [Configuration](configuration.md)
and [Security](security.md) for the tradeoff).

## Atomic mode: one bad item's error also shows up for items that were actually fine

This is expected - in atomic mode, the response to a failed batch is a
plain list of every item's validation result (empty dict `{}` for
items that validated successfully), matching DRF's own
`ListSerializer.errors` shape. An empty `{}` entry means that
particular item was fine; it just wasn't saved because a *different*
item in the same batch failed. See [Architecture](architecture.md).

## `bulk_update`/`bulk_partial_update` says an item is "missing the required 'id' field"

Every item in the request body must include the view's
`bulk_lookup_field` (default `"id"`) identifying which object it
updates - a full replacement object without an ID has nothing to match
against an existing row. If your model's natural identifier isn't
`id`, set `bulk_lookup_field` on the viewset (see
[Configuration](configuration.md#per-viewset-lookup-field)).

## `bulk_update`/`bulk_destroy` says "No object found with id=..."

Either the ID doesn't exist, or it does exist but is filtered out by
`get_queryset()` (e.g. scoped to a different user/tenant, or excluded
by a default filter) - from the requesting client's perspective these
look identical, matching how a single-object `404` already behaves for
the same reasons.

## A within-batch duplicate value is caught inconsistently between atomic and non-atomic mode

This is expected, not a bug - see
[Architecture](architecture.md#why-a-within-batch-duplicate-title-behaves-differently-in-each-mode)
for exactly why atomic mode surfaces it as a database-level rollback
while non-atomic mode surfaces it as an ordinary validation error on
the second occurrence.

## A bulk request to an object I shouldn't have access to returns `403` for the whole batch, not a per-item error

This is deliberate - object-level permission denial is a hard abort at
the DRF exception-handling layer, the same as it is for a single-object
endpoint, not one of this package's own per-item success/failure
results. See
[Architecture](architecture.md#object-level-permission-denial-is-a-hard-abort-not-a-per-item-result).

## `TypeError`/unexpected behavior when `perform_create`/`perform_update`/`perform_destroy` is overridden

These hooks are called once per item, synchronously, inside that
item's own transaction/savepoint scope - if your override does
anything that itself needs to run *after* the whole batch completes
(e.g. sending one aggregate notification for the entire batch, not one
per item), do that in the view's `bulk_create`/etc. method itself
(override it, call `super()`, then run your post-batch logic on the
response), not inside `perform_create`.
