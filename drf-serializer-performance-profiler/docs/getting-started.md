# Getting Started

## Install

```bash
pip install drf-serializer-performance-profiler
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "drf_serializer_performance_profiler",
]
```

No profile is ever attached to a response until you explicitly enable
it - see [Settings](settings.md).

## Mix into a serializer

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

`ProfileSerializerMixin` must come *before* the DRF serializer base
class in the MRO (as shown above) - it overrides `to_representation`
and needs to call `super().to_representation()` to get the real,
unmodified output.

## Mix into the view that uses it

```python
# views.py
from drf_serializer_performance_profiler import ProfileSerializerViewMixin
from rest_framework.viewsets import ModelViewSet


class ArticleViewSet(ProfileSerializerViewMixin, ModelViewSet):
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
```

## Turn on the header

```python
# settings.py
SERIALIZER_PROFILER = {
    "ENABLED": True,
}
```

By default, the header is only attached for a **staff** user
(`request.user.is_staff`) - a request from anyone else gets no header
at all, even with `ENABLED: True`. Log in as staff and make a request:

```
GET /articles/1/
200 OK

X-Serializer-Profile: comment_count=8.30ms (1q), title=0.02ms (0q), author=0.01ms (0q) (total=8.33ms, queries=1)
```

See [Security](security.md) for why this restriction exists and when
it's safe to relax.

## What happens now

- The response body is byte-for-byte identical to what the same
  serializer would produce without either mixin - only the header is
  added.
- For a list endpoint, the header shows the *aggregated* total across
  every row in the response, not just the first one - see
  [Architecture](architecture.md).

See [Quick Start](quickstart.md) for passive slow-field logging (no
header, safe for production) and reading a profile directly from your
own code.
