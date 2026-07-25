"""DRF serializer for the test app."""

from __future__ import annotations

from rest_framework import serializers

from tests.test_app.models import Article


class ArticleSerializer(serializers.ModelSerializer[Article]):
    """Serializes an :class:`~tests.test_app.models.Article`."""

    class Meta:
        model = Article
        fields = ["id", "title", "owner"]
