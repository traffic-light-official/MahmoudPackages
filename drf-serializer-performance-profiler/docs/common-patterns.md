# Common Patterns

## Diagnosing a "this endpoint got slow after we added a field" regression

Enable the header for the affected endpoint, compare before/after (or
just look at which field dominates the total):

```python
# settings.py (temporarily, or gated by an env var in staging)
SERIALIZER_PROFILER = {"ENABLED": True}
```

```
X-Serializer-Profile: related_summary=180.40ms (25q), title=0.05ms (0q) (total=180.45ms, queries=25)
```

Immediately points at `related_summary` and its 25 queries, without
needing to bisect the recent commits that touched the serializer.

## Enabling passive monitoring in production without exposing anything

```python
# settings.py
SERIALIZER_PROFILER = {
    "LOG_SLOW_FIELDS": True,
    "SLOW_FIELD_THRESHOLD_MS": 20.0,
}
```

Safe to leave on permanently - nothing is ever exposed over HTTP, only
written to your application logs (logger name
`"drf_serializer_performance_profiler"`). Feed the resulting log stream
into whatever aggregation you already use, and alert on a sudden spike
in slow-field warnings for a given serializer/field pair.

## Turning an N+1-prone `SerializerMethodField` into an annotation

The single most common fix this package's output points you toward:

```python
# before
class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    comment_count = serializers.SerializerMethodField()

    def get_comment_count(self, obj):
        return obj.comments.count()  # one query per row

# after
class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    comment_count = serializers.IntegerField(read_only=True)  # reads an annotation
```

```python
# views.py
queryset = Article.objects.annotate(comment_count=Count("comments"))
```

See [Quick Start](quickstart.md) and [Examples](examples.md) for the
full before/after profile comparison.

## Asserting a fix actually reduced query count, in CI

```python
from drf_serializer_performance_profiler import get_serializer_profile


def test_comment_count_costs_no_queries(make_article):
    article = make_article(comment_count=5)
    with override_settings(SERIALIZER_PROFILER={"ENABLED": True}):
        serializer = ArticleSerializer(article)
        _ = serializer.data

    profile = get_serializer_profile(serializer)
    assert profile.fields["comment_count"].query_count == 0
```

Catches a regression (someone reverting the annotation, or adding a
new N+1-prone field) before it reaches production - a genuine
performance regression test, not just a functional one.

## Combining with pagination to keep the profile representative

The header aggregates across every row *in the response*, not the
whole table - paginate normally, and the profile reflects exactly the
page size a real client would receive:

```python
class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    pagination_class = PageNumberPagination  # page_size = 20, say
    serializer_class = ArticleSerializer
```

A field costing `(20q)` on a 20-item page is a much clearer N+1 signal
than testing against an unpaginated 10,000-row table would be.

## Documenting expected per-field cost in code review

```python
class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    # Annotated on the queryset (see ArticleViewSet.queryset) - must
    # stay 0 queries; if this regresses, check the annotation is
    # still present and named `comment_count`.
    comment_count = serializers.IntegerField(read_only=True)
```

A short comment naming the *expected* query count for a field that
was deliberately optimized helps a future contributor notice a
regression by reading the code, not just by re-running the profiler.
