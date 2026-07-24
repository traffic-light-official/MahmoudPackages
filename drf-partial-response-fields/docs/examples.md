# Examples

Runnable versions of these examples live in
[`examples/`](https://github.com/mahmoudgshaker/drf-partial-response-fields/tree/main/examples).

## A complete blog API

```python
# models.py
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()


class Tag(models.Model):
    label = models.CharField(max_length=100)


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    tags = models.ManyToManyField(Tag, related_name="articles")
    created_at = models.DateTimeField(auto_now_add=True)
```

```python
# serializers.py
from rest_framework import serializers
from drf_partial_response_fields import PartialFieldsModelSerializer, requires_related


class AuthorSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class TagSerializer(PartialFieldsModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "label"]


class ArticleSerializer(PartialFieldsModelSerializer):
    author = AuthorSerializer()
    tags = TagSerializer(many=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "title", "body", "author", "tags", "comment_count", "created_at"]

    def get_comment_count(self, obj):
        return obj.comments.count()
```

```python
# views.py
from rest_framework import viewsets
from drf_partial_response_fields import PartialResponseMixin


class ArticleViewSet(PartialResponseMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

### Requests and responses

```
GET /articles/?fields=title,author(name)
```

```json
[{"id": 1, "title": "...", "author": {"id": 3, "name": "Ada Lovelace"}}]
```

```
GET /articles/?fields=title,tags(label),comment_count
```

```json
[{"id": 1, "title": "...", "tags": [{"id": 1, "label": "django"}], "comment_count": 4}]
```

## A dashboard endpoint requesting only aggregate fields

```python
class ArticleStatsSerializer(PartialFieldsModelSerializer):
    tag_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "tag_count"]


class ArticleStatsViewSet(PartialResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ArticleStatsSerializer

    def get_queryset(self):
        return Article.objects.annotate(tag_count=Count("tags"))
```

```
GET /article-stats/?fields=title,tag_count
```

The optimizer recognizes `tag_count` as a queryset annotation (not a model
relation) and includes it in `only()` without attempting to resolve it as a
foreign key — see [Architecture](architecture.md#the-query-optimizers-decision-tree).

## A `SerializerMethodField` with optimizer hints

```python
class ArticleSerializer(PartialFieldsModelSerializer):
    editor_note = serializers.SerializerMethodField()

    @requires_related(select_related=["editor__profile"])
    def get_editor_note(self, obj):
        return f"Reviewed by {obj.editor.profile.display_name}"
```

```
GET /articles/?fields=editor_note
```

Only when `editor_note` is requested does the queryset gain
`select_related("editor__profile")` — a request that omits it never pays
for the extra join.

## Renaming fields for a public API

```
GET /articles/?fields=publishedAt:created_at,writer:author(name)
```

```json
{"publishedAt": "2026-01-01T00:00:00Z", "writer": {"name": "Ada Lovelace"}}
```

Useful when your internal field names (`created_at`, `author`) don't match
the naming convention a public API contract requires (`publishedAt`,
`writer`), without maintaining two parallel serializers.
