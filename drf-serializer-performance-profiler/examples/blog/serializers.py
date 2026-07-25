"""DRF serializers for the runnable example: an unoptimized and an optimized version."""

from __future__ import annotations

from rest_framework import serializers

from drf_serializer_performance_profiler import ProfileSerializerMixin
from examples.blog.models import Article


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer[Article]):
    """Unoptimized: ``comment_count`` runs one query per row."""

    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]

    def get_comment_count(self, obj: Article) -> int:
        return obj.comments.count()  # type: ignore[attr-defined,no-any-return]


class OptimizedArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer[Article]):
    """Optimized: ``comment_count`` reads a queryset annotation - no extra queries."""

    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]
