# Advanced Usage

## Overriding `perform_create`/`perform_update`/`perform_destroy`

Each mixin calls a `perform_*` hook that defaults to exactly what DRF's
own single-object mixins do (`serializer.save()`/`instance.delete()`) -
override it the same way you would on a regular `ModelViewSet`, e.g. to
attach the requesting user or trigger a side effect per item:

```python
class ArticleViewSet(BulkModelViewSet):
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        AuditLog.objects.create(action="article_deleted", target_id=instance.pk)
        instance.delete()
```

These hooks run once per item, inside that item's own transaction
scope (a savepoint in non-atomic mode, part of the shared outer
transaction in atomic mode) - anything raised here that's a
`django.db.DatabaseError` subclass is caught and reported the same way
a validation failure is; anything else propagates and aborts the
request entirely (see [Architecture](architecture.md)).

## A custom lookup field

```python
class ArticleViewSet(BulkModelViewSet):
    bulk_lookup_field = "slug"
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

```
PUT /articles/bulk-update/     [{"slug": "hello-world", "title": "Hello, World!"}]
DELETE /articles/bulk-delete/  ["hello-world", "another-post"]
```

`bulk_lookup_field` must be an attribute the queryset can filter on
directly (`queryset.filter(<field>__in=[...])`) - a `related_name` or
computed property won't work, the same restriction DRF's own
`lookup_field` has.

## Mixing in only the operations you need

Every mixin is independent - there's no requirement to use
`BulkModelViewSet`:

```python
from drf_bulk_operations import BulkCreateModelMixin, BulkDestroyModelMixin
from rest_framework import viewsets


class ArticleViewSet(BulkCreateModelMixin, BulkDestroyModelMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

This gets `bulk_create` and `bulk_destroy` but not `bulk_update`/
`bulk_partial_update` - useful for a viewset where bulk import and bulk
cleanup are common operations but bulk editing isn't.

## Building the per-item response shape yourself

`ItemResult`/`build_bulk_response` are public - reuse them if you're
writing a custom action that needs the same "some succeeded, some
didn't" reporting shape this package uses internally:

```python
from drf_bulk_operations import ItemResult
from drf_bulk_operations.results import build_bulk_response


@action(detail=False, methods=["post"])
def bulk_publish(self, request, *args, **kwargs):
    results = []
    for index, article_id in enumerate(request.data):
        try:
            article = self.get_queryset().get(pk=article_id)
        except Article.DoesNotExist:
            results.append(ItemResult(index, success=False, errors={"detail": "Not found."}))
            continue
        article.published = True
        article.save(update_fields=["published"])
        results.append(ItemResult(index, success=True, data={"id": article.pk}))
    return build_bulk_response(results, all_success_status=status.HTTP_200_OK)
```

## Using a different serializer for bulk requests

`get_serializer()` is called unchanged from `GenericAPIView` - override
`get_serializer_class()` on your viewset if bulk requests should use a
leaner serializer than single-object ones (e.g. skipping an expensive
nested field):

```python
class ArticleViewSet(BulkModelViewSet):
    def get_serializer_class(self):
        if self.action in {"bulk_create", "bulk_update", "bulk_partial_update"}:
            return ArticleBulkSerializer
        return ArticleSerializer
```

`self.action` is set to the bound action name (`"bulk_create"`, etc.)
by DRF's own `ViewSetMixin`, exactly as it would be for `"create"` or
`"list"`.
