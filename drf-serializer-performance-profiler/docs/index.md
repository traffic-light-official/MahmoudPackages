# drf-serializer-performance-profiler

Find slow fields in Django REST Framework serializers - per-field
timing and per-field database query counts, with zero change to what's
actually serialized.

```python
from drf_serializer_performance_profiler import ProfileSerializerMixin


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]
```

```
X-Serializer-Profile: comment_count=42.10ms (12q), author=3.20ms (1q), title=0.05ms (0q) (total=45.35ms, queries=13)
```

## Why this exists

A slow API endpoint is often a slow *serializer*, not a slow view or a
slow query considered in isolation - a single `SerializerMethodField`
computing an aggregate, or a related field silently triggering a query
per row, can dominate response time while every other field is
instant. DRF gives you no built-in way to see which field is
responsible, short of manually adding `print(time.time())` calls around
suspect fields and removing them again afterward. This package
instruments every field's rendering step individually - timing it and
counting the database queries it triggers - aggregated across every
row in a list response, without changing a single byte of the actual
serialized output.

## Where to go next

- New to the package? Start with [Getting Started](getting-started.md).
- Want the exact guarantee about output never changing? Read
  [Architecture](architecture.md).
- Looking for a specific class or function? Jump to
  [API Reference](api-reference.md).
- Something not behaving as expected? Check
  [Troubleshooting](troubleshooting.md) and the [FAQ](faq.md).

## At a glance

| Task | Where |
| --- | --- |
| Instrument a serializer | [`ProfileSerializerMixin`](api-reference.md#profileserializermixin) |
| Attach the profile as a response header | [`ProfileSerializerViewMixin`](api-reference.md#profileserializerviewmixin) |
| Turn on the header | [`SERIALIZER_PROFILER`](settings.md) setting (`ENABLED`) |
| Log slow fields in production, with no header exposure | [`LOG_SLOW_FIELDS`](settings.md) setting |
| Read a profile from your own code | [`get_serializer_profile()`](api-reference.md#get_serializer_profile) |
