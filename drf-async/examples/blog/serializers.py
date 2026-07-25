"""DRF serializer for the runnable example."""

from __future__ import annotations

from rest_framework import serializers

from examples.blog.models import Article


class ArticleSerializer(serializers.ModelSerializer[Article]):
    """Serializes an :class:`~examples.blog.models.Article`."""

    class Meta:
        model = Article
        fields = ["id", "title", "author"]
