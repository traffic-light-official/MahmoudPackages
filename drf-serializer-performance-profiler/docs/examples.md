# Examples

A complete, runnable example lives in [`examples/blog/`](https://github.com/MahmoudGShake/MahmoudPackages/tree/master/drf-serializer-performance-profiler/examples/blog)
in the source repository - models, an unoptimized serializer, an
optimized one, and a script comparing their profiles side by side.

Run it yourself:

```bash
git clone https://github.com/MahmoudGShake/MahmoudPackages.git
cd MahmoudPackages/drf-serializer-performance-profiler
pip install -e ".[dev]"
python -m examples.blog.example
```

## `examples/blog/serializers.py`

```python
from rest_framework import serializers

from drf_serializer_performance_profiler import ProfileSerializerMixin
from examples.blog.models import Article


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    """Unoptimized: comment_count runs one query per row."""

    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]

    def get_comment_count(self, obj):
        return obj.comments.count()


class OptimizedArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer):
    """Optimized: comment_count reads a queryset annotation - no extra queries."""

    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]
```

## `examples/blog/views.py`

```python
from django.db.models import Count
from rest_framework.viewsets import ReadOnlyModelViewSet

from drf_serializer_performance_profiler import ProfileSerializerViewMixin
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer, OptimizedArticleSerializer


class ArticleViewSet(ProfileSerializerViewMixin, ReadOnlyModelViewSet):
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()


class OptimizedArticleViewSet(ProfileSerializerViewMixin, ReadOnlyModelViewSet):
    serializer_class = OptimizedArticleSerializer
    queryset = Article.objects.select_related("author").annotate(comment_count=Count("comments"))
```

## `examples/blog/example.py` output

Both endpoints list the same 3 articles (2 comments each):

```text
== Unoptimized: comment_count runs one query per row ==
  Status: 200, articles: 3
  X-Serializer-Profile: comment_count=0.94ms (3q), id=0.07ms (0q), author=0.03ms (0q), title=0.02ms (0q) (total=1.07ms, queries=3)

== Optimized: comment_count is a queryset annotation ==
  Status: 200, articles: 3
  X-Serializer-Profile: id=0.02ms (0q), author=0.02ms (0q), title=0.01ms (0q), comment_count=0.01ms (0q) (total=0.06ms, queries=0)
```

A few things worth noting from this output:

- `comment_count`'s query count is exactly **3** for the unoptimized
  version - one per article in the response, confirming it's genuinely
  N+1-shaped, not a fixed cost.
- After switching to an annotation, `comment_count` costs **0**
  queries and drops to the bottom of the slowest-fields ordering - the
  annotation is already computed by the single query the queryset
  itself issues, so there's nothing left for the field to do beyond
  reading an attribute.
- `id`/`author`/`title` cost 0 queries in both versions, as expected -
  they were never the problem; `comment_count` was.

See [Quick Start](quickstart.md) for the same before/after walkthrough
explained field by field.
