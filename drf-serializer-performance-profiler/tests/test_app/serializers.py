"""DRF serializers for the test app."""

from __future__ import annotations

from rest_framework import serializers

from drf_serializer_performance_profiler import ProfileSerializerMixin
from tests.test_app.models import Article


class ArticleSerializer(ProfileSerializerMixin, serializers.ModelSerializer[Article]):
    """Serializes an :class:`~tests.test_app.models.Article`.

    ``comment_count`` deliberately queries the database once per
    instance (``obj.comments.count()``) - a realistic stand-in for a
    slow, N+1-prone computed field - while ``title``/``author`` cost no
    additional queries at all (the FK id is already on the row).
    """

    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ["id", "title", "author", "comment_count"]

    def get_comment_count(self, obj: Article) -> int:
        return obj.comments.count()  # type: ignore[attr-defined,no-any-return]
