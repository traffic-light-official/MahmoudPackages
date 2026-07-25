# Quick Start

## A full profiled viewset

```python
# serializers.py
from drf_serializer_performance_profiler import ProfileSerializerMixin
from rest_framework import serializers


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]

    def get_comment_count(self, obj):
        return obj.comments.count()
```

```python
# views.py
from drf_serializer_performance_profiler import ProfileSerializerViewMixin
from rest_framework.viewsets import ModelViewSet


class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
```

```python
# settings.py
SERIALIZER_PROFILER = {"ENABLED": True}
```

## Reading the header on a detail request

```
GET /articles/1/
200 OK

X-Serializer-Profile: comment_count=8.30ms (1q), title=0.02ms (0q), author=0.01ms (0q) (total=8.33ms, queries=1)
```

`comment_count` costs one query per article (`obj.comments.count()`);
`title`/`author` cost none, since the FK id is already on the row.

## Reading the header on a list request

```
GET /articles/
200 OK

X-Serializer-Profile: comment_count=24.90ms (10q), title=0.15ms (0q), author=0.08ms (0q) (total=25.13ms, queries=10)
```

For 10 articles in the response, `comment_count`'s numbers are the
**sum across all 10 rows** - 10 queries total, one per row - not a
single row's cost. This is what makes the header immediately point at
an N+1 pattern: a field whose query count scales with the number of
rows in the response is a strong signal something should use
`prefetch_related`/an annotation instead.

## Fixing the N+1 and confirming it

```python
class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").annotate(
        comment_count=Count("comments")
    )
```

```python
# serializers.py - read the annotation instead of running a per-row query
class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]
```

```
X-Serializer-Profile: title=0.14ms (0q), author=0.07ms (0q), comment_count=0.05ms (0q) (total=0.26ms, queries=0)
```

## Passive logging, no header needed

```python
SERIALIZER_PROFILER = {
    "LOG_SLOW_FIELDS": True,
    "SLOW_FIELD_THRESHOLD_MS": 10.0,
}
```

```
WARNING drf_serializer_performance_profiler: Slow serializer field ArticleSerializer.comment_count: 24.90ms (10 queries)
```

Works even with `ENABLED: False` - nothing is ever exposed to a
client, only written to your application's logs.

## Reading a profile directly from your own code

```python
from drf_serializer_performance_profiler import get_serializer_profile

serializer = ArticleSerializer(article)
data = serializer.data  # triggers to_representation()

profile = get_serializer_profile(serializer)
for field in profile.slowest_fields():
    print(field.field_name, field.total_time_ms, field.query_count)
```

See [Advanced Usage](advanced-usage.md) for aggregating profiles across
multiple serializers in one request, and combining this with
`drf-n-plus-one-query-guard`.
