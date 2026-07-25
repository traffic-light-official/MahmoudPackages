"""DRF viewsets for the test app.

Two list endpoints over the same data: one deliberately N+1-prone
(no ``select_related``), one deliberately optimized - used across the
test suite to exercise both "the guard fires" and "the guard stays
quiet" paths against real request/response cycles, not just synthetic
query events.
"""

from __future__ import annotations

from rest_framework import viewsets

from tests.test_app.models import Article
from tests.test_app.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ReadOnlyModelViewSet[Article]):
    """Deliberately N+1-prone: no ``select_related`` on the queryset."""

    serializer_class = ArticleSerializer
    queryset = Article.objects.all()


class OptimizedArticleViewSet(viewsets.ReadOnlyModelViewSet[Article]):
    """The same data, with ``select_related("author")`` applied."""

    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()
