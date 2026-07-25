# Configuration

This package has one Django setting, `BULK_OPERATIONS`, with two keys -
see [Settings](settings.md) for both. Everything else is configured the
same way you'd configure any other DRF viewset: `permission_classes`,
`authentication_classes`, `serializer_class`, `queryset`.

## Choosing atomic vs. non-atomic

The single most important decision this package asks you to make is
the `ATOMIC` setting (default `True`):

```python
# settings.py
BULK_OPERATIONS = {
    "ATOMIC": False,
}
```

- **Atomic** (default): every item is validated before anything is
  written. If any single item is invalid or fails to save, *nothing* in
  the batch is committed - the whole request is a single unit of work.
  Choose this when your bulk endpoint represents one logical operation
  from the client's point of view (e.g. "import this CSV row-batch as
  one transaction").
- **Non-atomic**: every item is attempted independently, so 99 valid
  items in a batch of 100 still succeed even if item 100 is bad. Choose
  this when items are genuinely independent from each other (e.g. "mark
  these 500 notifications as read - if one is already gone, that's
  fine, do the rest").

This is a global, project-wide setting - it isn't currently overridable
per-viewset. If different viewsets in your project genuinely need
different modes, wrap each one's bulk action call with
`@override_settings`-style logic yourself, or open an issue describing
the use case (see [Contributing](contributing.md)).

## Capping batch size

```python
# settings.py
BULK_OPERATIONS = {
    "MAX_BATCH_SIZE": 500,
}
```

Applies identically to all four bulk actions and both atomic/non-atomic
modes - a request submitting more items than this is rejected with
`400` before any validation or database work happens at all. See
[Security](security.md) for why this matters even in non-atomic mode.

## Per-viewset lookup field

`bulk_update`/`bulk_partial_update`/`bulk_destroy` identify each item's
target object via `bulk_lookup_field` (default `"id"`) - override it
per viewset if your model's natural external identifier is something
else:

```python
class ArticleViewSet(BulkModelViewSet):
    bulk_lookup_field = "slug"
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

```
PUT /articles/bulk-update/    [{"slug": "hello-world", "title": "Hello, World!"}]
```
