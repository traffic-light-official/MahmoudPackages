# Advanced Usage

## Profiling a serializer with nested serializers

A nested serializer field's own timing (including everything *it*
does internally) is attributed to the *parent* field's entry, as one
number - `ProfileSerializerMixin` measures each of the parent
serializer's fields as a unit, including whatever the field's own
`to_representation()` does internally (which, for a nested serializer
field, is that whole nested serializer's rendering). To see the nested
serializer's own per-field breakdown, mix `ProfileSerializerMixin` into
the nested serializer class too - it gets its own, separate profile:

```python
class AuthorSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio"]


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    author = AuthorSerializer()

    class Meta:
        model = Article
        fields = ["id", "title", "author"]
```

```python
article_serializer = ArticleSerializer(article)
data = article_serializer.data

outer_profile = get_serializer_profile(article_serializer)
inner_profile = get_serializer_profile(article_serializer.fields["author"])
```

## Aggregating profiles across multiple serializers in one request

`ProfileSerializerViewMixin` already does this for every serializer
`get_serializer()` creates - reuse `merge_profiles()` yourself if your
view serializes more than one thing manually (e.g. a custom action
combining two different serializers in one response):

```python
from drf_serializer_performance_profiler import get_serializer_profile, merge_profiles


class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    @action(detail=True)
    def summary(self, request, pk=None):
        article = self.get_object()
        article_data = ArticleSerializer(article).data
        author_data = AuthorSerializer(article.author).data

        combined = merge_profiles(
            [
                p
                for s in (ArticleSerializer(article), AuthorSerializer(article.author))
                if (p := get_serializer_profile(s)) is not None
            ]
        )
        return Response({"article": article_data, "author": author_data})
```

## Combining with `drf-n-plus-one-query-guard`

Both packages instrument database queries, but answer different
questions: `drf-n-plus-one-query-guard` answers "did this *request*
trigger a repeated query pattern" (fingerprint-based, whole-request
scope); this package answers "which specific serializer *field* is
responsible for however many queries ran." Use them together - the
guard tells you a request has an N+1 problem at all; this package's
header tells you exactly which field to fix:

```python
class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    serializer_class = ArticleSerializer  # ProfileSerializerMixin-based
    queryset = Article.objects.all()
```

```python
# settings.py
N_PLUS_ONE_GUARD = {"MODE": "warn"}
SERIALIZER_PROFILER = {"ENABLED": True}
```

## Writing a custom threshold per field

`SLOW_FIELD_THRESHOLD_MS` is global - if one field is expected to be
slow (e.g. a genuinely expensive aggregate) and you don't want it
cluttering logs, read the profile yourself in `finalize_response`
instead of relying on the built-in per-field logging:

```python
class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        for serializer in getattr(self, "_profiled_serializers", []):
            profile = get_serializer_profile(serializer)
            if profile and (comment_count := profile.fields.get("comment_count")):
                if comment_count.total_time_ms > 100:
                    logger.error("comment_count is unexpectedly slow: %s", comment_count)
        return response
```

## Testing that a fix actually reduced query count

```python
def test_annotated_comment_count_costs_no_queries(api_client, make_article):
    make_article(comment_count=5)
    with override_settings(SERIALIZER_PROFILER={"ENABLED": True, "RESTRICT_TO_STAFF": False}):
        response = api_client.get("/articles/")
    assert "comment_count=" in response.headers["X-Serializer-Profile"]
    assert "(0q)" in response.headers["X-Serializer-Profile"].split("comment_count=")[1][:20]
```

See [Testing](testing.md) for a cleaner pattern using
`get_serializer_profile()` directly instead of parsing the header
string.
