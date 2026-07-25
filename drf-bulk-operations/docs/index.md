# drf-bulk-operations

Bulk create/update/delete endpoints for Django REST Framework
ViewSets - one JSON list in, per-item results out, with a real choice
between atomic (all-or-nothing) and non-atomic (independent, partial
success) semantics.

```python
from drf_bulk_operations import BulkModelViewSet


class ArticleViewSet(BulkModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

## Why this exists

DRF's own mixins (`CreateModelMixin`, `UpdateModelMixin`,
`DestroyModelMixin`) handle exactly one object per request - there's no
built-in way to create, update, or delete a hundred objects without a
hundred round trips, or writing the same batch-endpoint boilerplate
(size limits, per-item validation, deciding what "partial failure" even
means) in every project that needs it. This package adds that layer
once: four `@action`-decorated mixins, each with a genuine choice
between two well-defined failure modes, not just a loop around
`.save()`.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Deciding between atomic and non-atomic mode for your use case? Read
  [Architecture](architecture.md).
- Looking for a specific class or function? Jump to
  [API Reference](api-reference.md).
- Something not behaving as expected? Check
  [Troubleshooting](troubleshooting.md) and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Bulk-create a list of objects | [`BulkCreateModelMixin`](api-reference.md#bulkcreatemodelmixin) - `POST .../bulk/` |
| Bulk full-update by ID | [`BulkUpdateModelMixin`](api-reference.md#bulkupdatemodelmixin) - `PUT .../bulk-update/` |
| Bulk partial-update by ID | [`BulkPartialUpdateModelMixin`](api-reference.md#bulkpartialupdatemodelmixin) - `PATCH .../bulk-partial-update/` |
| Bulk-delete by ID | [`BulkDestroyModelMixin`](api-reference.md#bulkdestroymodelmixin) - `DELETE .../bulk-delete/` |
| All four at once | [`BulkModelViewSet`](api-reference.md#bulkmodelviewset) |
| All-or-nothing vs. partial success | [`ATOMIC`](settings.md) setting |
| Cap items per request | [`MAX_BATCH_SIZE`](settings.md) setting |
