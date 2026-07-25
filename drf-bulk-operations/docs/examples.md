# Examples

A complete, runnable example lives in [`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-bulk-operations/examples/blog)
in the source repository - models, a serializer, a bulk-enabled
viewset, and a script exercising every action in both atomic and
non-atomic mode, with no test framework and no running server.

Run it yourself:

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-bulk-operations
pip install -e ".[dev]"
python -m examples.blog.example
```

## `examples/blog/models.py`

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        app_label = "blog"


class Article(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    published = models.BooleanField(default=False)

    class Meta:
        app_label = "blog"
        ordering = ["id"]
```

## `examples/blog/views.py`

```python
from rest_framework.permissions import AllowAny

from drf_bulk_operations import BulkModelViewSet
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer


class ArticleViewSet(BulkModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
```

## `examples/blog/example.py` output

The script calls each action directly
(`ArticleViewSet.as_view({"post": "bulk_create"})(request)`), without a
URL conf or a running server:

```text
== Bulk create (atomic, default): all valid ==
  POST /articles/bulk/ -> 201 [{'id': 1, 'title': 'First Post', 'author': 1, 'published': False}, {'id': 2, 'title': 'Second Post', 'author': 1, 'published': False}]

== Bulk create (atomic): one invalid item aborts the whole batch ==
  POST /articles/bulk/ -> 400 [{}, {'title': [ErrorDetail(string='This field may not be blank.', code='blank')]}]
  Article count unchanged: 2

== Bulk update ==
  PUT /articles/bulk-update/ -> 200 [{'id': 1, 'title': 'First Post (Revised)', 'author': 1, 'published': False}]

== Bulk partial update ==
  PATCH /articles/bulk-partial-update/ -> 200 [{'id': 1, 'title': 'First Post (Revised)', 'author': 1, 'published': True}]

== Bulk delete ==
  DELETE /articles/bulk-delete/ -> 204 None
  Article count after delete: 0

== Non-atomic mode: partial success ==
  POST /articles/bulk/ -> 207 [{'index': 0, 'status': 'success', 'data': {'id': 3, 'title': 'Good Post', 'author': 1, 'published': False}}, {'index': 1, 'status': 'error', 'errors': {'title': [ErrorDetail(string='This field may not be blank.', code='blank')]}}]
```

A few things worth noting from this output:

- The atomic-mode invalid-batch response is `[{}, {"title": [...]}]` -
  an empty dict for the item that *would* have validated fine, mirroring
  DRF's own `ListSerializer.errors` shape, since nothing was ever saved
  either way.
- `Article count unchanged: 2` after the aborted batch confirms
  atomic mode's core guarantee: the one valid item in that batch
  ("Would Succeed Alone") was never written.
- The non-atomic response tags each item with `"status"` and an
  `"index"` - `id: 3` in the successful item shows the primary key
  sequence continuing from the earlier (deleted) rows, since SQLite
  doesn't reuse deleted autoincrement IDs by default.

See [Quick Start](quickstart.md) for the same operations wired up to a
real URL conf and router instead of being called directly.
