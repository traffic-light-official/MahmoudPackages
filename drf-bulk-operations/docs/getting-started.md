# Getting Started

## Install

```bash
pip install drf-bulk-operations
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_bulk_operations",
]
```

No further settings are required - see [Settings](settings.md) for the
two optional overrides (`MAX_BATCH_SIZE`, `ATOMIC`).

## Add bulk endpoints to an existing viewset

```python
# views.py
from drf_bulk_operations import BulkModelViewSet


class ArticleViewSet(BulkModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

Register it exactly like any other viewset:

```python
# urls.py
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet)
urlpatterns = router.urls
```

This adds four new routes alongside the usual `list`/`create`/
`retrieve`/`update`/`partial_update`/`destroy` ones:

```
POST   /articles/bulk/                    [{"title": "A"}, {"title": "B"}]
PUT    /articles/bulk-update/             [{"id": 1, "title": "A2"}]
PATCH  /articles/bulk-partial-update/     [{"id": 1, "published": true}]
DELETE /articles/bulk-delete/             [1, 2, 3]
```

## Only need one operation?

Mix in just the mixin you need instead of `BulkModelViewSet`:

```python
from drf_bulk_operations import BulkDestroyModelMixin
from rest_framework import viewsets


class ArticleViewSet(BulkDestroyModelMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

This viewset gets `bulk_destroy` (`DELETE .../bulk-delete/`) in
addition to its normal single-object actions, with none of the other
three bulk endpoints.

## What happens now

- `POST /articles/bulk/` with a list of objects validates every item
  *before* writing anything (the default, atomic mode) - if any item is
  invalid, nothing is saved and the response is `400` with a per-item
  error list.
- If every item validates, all of them are created in a single
  database transaction and the response is `201` with the list of
  created objects.

See [Quick Start](quickstart.md) for non-atomic mode, custom lookup
fields, and object-level permissions on bulk update/destroy.
