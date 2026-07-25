# Quick Start

## A full bulk-enabled viewset

```python
# models.py
class Article(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    published = models.BooleanField(default=False)
```

```python
# serializers.py
from rest_framework import serializers


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "author", "published"]
```

```python
# views.py
from rest_framework.permissions import IsAuthenticated

from drf_bulk_operations import BulkModelViewSet


class ArticleViewSet(BulkModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Article.objects.select_related("author").all()
    serializer_class = ArticleSerializer
```

## Bulk create

```
POST /articles/bulk/
[
  {"title": "First Post", "author": 1},
  {"title": "Second Post", "author": 1}
]
```

```json
201 Created
[
  {"id": 1, "title": "First Post", "author": 1, "published": false},
  {"id": 2, "title": "Second Post", "author": 1, "published": false}
]
```

A blank title in either item aborts the whole request (default,
atomic mode):

```json
400 Bad Request
[
  {},
  {"title": ["This field may not be blank."]}
]
```

## Bulk update and partial update

```
PUT /articles/bulk-update/
[{"id": 1, "title": "First Post (Revised)", "author": 1, "published": true}]
```

```
PATCH /articles/bulk-partial-update/
[{"id": 1, "published": false}]
```

Both identify each item by `id` (or your view's `bulk_lookup_field`) -
every other key is passed to the serializer as the update data.

## Bulk delete

```
DELETE /articles/bulk-delete/
[1, 2, 3]
```

```
204 No Content
```

## Switching to non-atomic mode

```python
# settings.py
BULK_OPERATIONS = {"ATOMIC": False}
```

Now a batch with one bad item still saves the good ones:

```
POST /articles/bulk/
[{"title": "Good Post", "author": 1}, {"title": "", "author": 1}]
```

```json
207 Multi-Status
[
  {"index": 0, "status": "success", "data": {"id": 3, "title": "Good Post", "author": 1, "published": false}},
  {"index": 1, "status": "error", "errors": {"title": ["This field may not be blank."]}}
]
```

## Object-level permissions

`bulk_update`/`bulk_partial_update`/`bulk_destroy` call
`check_object_permissions()` for every resolved instance, exactly like
DRF's own single-object `update`/`destroy` - a denied object aborts the
*entire* request with `403`, the same as a single-object endpoint would
(this is a hard abort at the DRF exception-handling layer, not one of
the per-item results in a `207` response):

```python
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class ArticleViewSet(BulkModelViewSet):
    permission_classes = [IsOwner]
    ...
```

See [Advanced Usage](advanced-usage.md) for a custom lookup field and
overriding `perform_create`/`perform_update`/`perform_destroy`.
