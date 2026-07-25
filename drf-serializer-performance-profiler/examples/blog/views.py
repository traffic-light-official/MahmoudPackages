"""Views demonstrating this package's main features."""

from __future__ import annotations

from django.db.models import Count
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from drf_serializer_performance_profiler import ProfileSerializerViewMixin
from examples.blog.models import Article
from examples.blog.serializers import ArticleSerializer, OptimizedArticleSerializer


class ArticleViewSet(ProfileSerializerViewMixin, ReadOnlyModelViewSet):
    """Unoptimized: ``comment_count`` costs one query per row."""

    permission_classes = [AllowAny]
    serializer_class = ArticleSerializer
    queryset = Article.objects.select_related("author").all()


class OptimizedArticleViewSet(ProfileSerializerViewMixin, ReadOnlyModelViewSet):
    """Optimized: ``comment_count`` is a queryset annotation, costing no extra queries."""

    permission_classes = [AllowAny]
    serializer_class = OptimizedArticleSerializer
    queryset = Article.objects.select_related("author").annotate(comment_count=Count("comments"))
