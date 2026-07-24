# Getting Started

This page gets a single endpoint working end to end in about five minutes.
For a deeper tour of every feature, see [Quick Start](quickstart.md) and
[Advanced Usage](advanced-usage.md).

## Prerequisites

- Python 3.10+
- Django 4.2+
- Django REST Framework 3.14+

## 1. Install

```bash
pip install drf-partial-response-fields
```

No changes to `INSTALLED_APPS` are required — this package has no models,
migrations, or app config of its own.

## 2. Update your serializer

Mix `PartialFieldsSerializerMixin` into any serializer that should support
`?fields=`, or use the ready-made `PartialFieldsModelSerializer` base class:

```python
from drf_partial_response_fields import PartialFieldsModelSerializer


class AuthorSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class ArticleSerializer(PartialFieldsModelSerializer):
    author = AuthorSerializer()

    class Meta:
        model = Article
        fields = ["id", "title", "body", "author"]
```

Nested serializers (like `AuthorSerializer` above) need the mixin too — each
serializer is responsible for filtering its own level of the response tree.

## 3. Update your view

Mix `PartialResponseMixin` into your view or viewset, again *before* the DRF
base class:

```python
from rest_framework import viewsets
from drf_partial_response_fields import PartialResponseMixin


class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

## 4. Try it

```bash
curl "http://localhost:8000/articles/1/?fields=title,author(name)"
```

```json
{
  "id": 1,
  "title": "Shipping Faster with Sparse Fieldsets",
  "author": {"id": 3, "name": "Ada Lovelace"}
}
```

Notice `id` is always present — see [`ALWAYS_INCLUDE`](settings.md#always_include).
Everything else you didn't ask for (`body`, `author.email`, ...) is gone
from the response, and the underlying queryset was automatically rewritten
to `select_related("author").only("id", "title", "author__id", "author__name")` —
no extra query for the author, and no columns fetched that weren't needed.

## Next steps

- [Configuration](configuration.md) — project-wide setup considerations.
- [Quick Start](quickstart.md) — nested selection, exclusion, aliasing,
  wildcards.
- [Advanced Usage](advanced-usage.md) — `SerializerMethodField` hints,
  plain `APIView` integration, OpenAPI docs.
